from dcim.choices import DeviceFaceChoices, SubdeviceRoleChoices
from dcim.models import (
    Device,
    DeviceBay,
    DeviceBayTemplate,
    DeviceRole,
    DeviceType,
    Manufacturer,
    Rack,
    Site,
)
from netbox_blade_chassis.models import DeviceBayTemplateLayout


def run():
    site, _ = Site.objects.get_or_create(name='Blade Test Site', defaults={'slug': 'blade-test-site'})
    rack, _ = Rack.objects.get_or_create(
        site=site,
        name='Rack-1',
        defaults={'u_height': 42, 'status': 'active'},
    )
    manufacturer, _ = Manufacturer.objects.get_or_create(name='BladeLab', defaults={'slug': 'bladelab'})

    parent_type, _ = DeviceType.objects.update_or_create(
        manufacturer=manufacturer,
        model='SuperMicro-4in1',
        defaults={
            'slug': 'supermicro-4in1',
            'u_height': 4,
            'subdevice_role': SubdeviceRoleChoices.ROLE_PARENT,
        },
    )

    child_type, _ = DeviceType.objects.update_or_create(
        manufacturer=manufacturer,
        model='Blade-Server',
        defaults={
            'slug': 'blade-server',
            'u_height': 0,
            'subdevice_role': SubdeviceRoleChoices.ROLE_CHILD,
        },
    )

    parent_role, _ = DeviceRole.objects.get_or_create(name='cloud', defaults={'slug': 'cloud', 'color': 'ff5722'})
    blade_role, _ = DeviceRole.objects.get_or_create(name='Blade', defaults={'slug': 'blade', 'color': '4caf50'})

    bay_names = [f'Bay {index}' for index in range(1, 5)]
    layouts = [(0, 0), (1, 0), (0, 1), (1, 1)]

    DeviceBayTemplate.objects.get_or_create(
        device_type=parent_type,
        name='USB',
        defaults={'label': 'USB'},
    )

    templates = []
    for name, position in zip(bay_names, layouts):
        template, _ = DeviceBayTemplate.objects.get_or_create(
            device_type=parent_type,
            name=name,
        )
        templates.append((template, position[0], position[1]))

    DeviceBayTemplateLayout.objects.filter(
        device_bay_template__device_type=parent_type,
    ).delete()
    DeviceBayTemplateLayout.objects.bulk_create([
        DeviceBayTemplateLayout(
            device_bay_template=template,
            position_x=position_x,
            position_y=position_y,
        )
        for template, position_x, position_y in templates
    ])

    parent, _ = Device.objects.update_or_create(
        name='chassis-01',
        defaults={
            'device_type': parent_type,
            'role': parent_role,
            'site': site,
            'rack': rack,
            'position': 10,
            'face': DeviceFaceChoices.FACE_FRONT,
            'status': 'active',
        },
    )

    hostname = 'cloud-stagehv2-inf-int-b1.example.dev'
    for bay_name in bay_names:
        bay, _ = DeviceBay.objects.get_or_create(device=parent, name=bay_name)
        blade, _ = Device.objects.update_or_create(
            name=f'{hostname}#{bay_name}',
            defaults={
                'device_type': child_type,
                'role': blade_role,
                'site': site,
                'status': 'active',
            },
        )
        bay.installed_device = blade
        bay.save()

    print(f'Site: {site.pk}')
    print(f'Rack: {rack.pk}')
    print(f'Parent device: {parent.pk}')


run()
