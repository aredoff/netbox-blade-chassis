import django
from django.core.exceptions import ValidationError
from django.test import TestCase

django.setup()

from dcim.models import (
    Device,
    DeviceBayTemplate,
    DeviceRole,
    DeviceType,
    Manufacturer,
    Site,
)

from netbox_blade_chassis.layout import (
    LayoutEntry,
    device_has_blade_layout,
    get_chassis_title,
    get_layout_map,
    get_symmetric_column_count,
    group_layout_by_row,
    mirror_column_index,
    validate_grid_symmetry,
)
from netbox_blade_chassis.models import DeviceBayTemplateLayout


class DeviceBayTemplateLayoutTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        manufacturer = Manufacturer.objects.create(name='Test', slug='test')
        cls.device_type = DeviceType.objects.create(
            manufacturer=manufacturer,
            model='Blade Chassis',
            slug='blade-chassis',
            subdevice_role='parent',
        )
        cls.bay_templates = [
            DeviceBayTemplate.objects.create(device_type=cls.device_type, name=f'Bay {index}')
            for index in range(1, 9)
        ]

    def test_unique_position_validation(self):
        DeviceBayTemplateLayout.objects.create(
            device_bay_template=self.bay_templates[0],
            position_x=0,
            position_y=0,
        )
        duplicate = DeviceBayTemplateLayout(
            device_bay_template=self.bay_templates[1],
            position_x=0,
            position_y=0,
        )
        with self.assertRaises(ValidationError):
            duplicate.full_clean()

    def test_asymmetric_blade_layout_rejected(self):
        layout_map = {
            'Bay 1': LayoutEntry(0, 0),
            'Bay 2': LayoutEntry(1, 0),
            'Bay 3': LayoutEntry(2, 0),
            'Bay 4': LayoutEntry(3, 0),
            'Bay 5': LayoutEntry(0, 1),
        }
        with self.assertRaises(ValidationError):
            validate_grid_symmetry(layout_map)

    def test_group_layout_symmetric_grid(self):
        layout_map = {
            'Bay 1': LayoutEntry(0, 0),
            'Bay 2': LayoutEntry(1, 0),
            'Bay 3': LayoutEntry(0, 1),
            'Bay 4': LayoutEntry(1, 1),
        }
        rows = group_layout_by_row(layout_map)
        self.assertEqual(get_symmetric_column_count(rows), 2)
        self.assertEqual(len(rows[0]), 2)
        self.assertEqual(len(rows[1]), 2)

    def test_mirror_column_index(self):
        self.assertEqual(mirror_column_index(0, 4), 3)
        self.assertEqual(mirror_column_index(1, 2), 0)
        self.assertEqual(mirror_column_index(0, 1), 0)

    def test_device_has_blade_layout_when_positions_set(self):
        DeviceBayTemplateLayout.objects.create(
            device_bay_template=self.bay_templates[0],
            position_x=0,
            position_y=0,
        )
        self.assertTrue(device_has_blade_layout(self.device_type))

    def test_get_layout_map_returns_coordinates(self):
        DeviceBayTemplateLayout.objects.create(
            device_bay_template=self.bay_templates[0],
            position_x=1,
            position_y=2,
        )
        entry = get_layout_map(self.device_type)['Bay 1']
        self.assertEqual(entry.position_x, 1)
        self.assertEqual(entry.position_y, 2)

    def test_validate_grid_symmetry_requires_equal_row_widths(self):
        layout_map = {
            'Bay 1': LayoutEntry(0, 0),
            'Bay 2': LayoutEntry(1, 0),
            'USB': LayoutEntry(0, 1),
        }
        with self.assertRaises(ValidationError):
            validate_grid_symmetry(layout_map)

        symmetric_map = {
            'Bay 1': LayoutEntry(0, 0),
            'Bay 2': LayoutEntry(1, 0),
            'USB': LayoutEntry(0, 1),
            'Empty': LayoutEntry(1, 1),
        }
        validate_grid_symmetry(symmetric_map)


class ChassisTitleTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        manufacturer = Manufacturer.objects.create(name='Title Test', slug='title-test')
        cls.device_type = DeviceType.objects.create(
            manufacturer=manufacturer,
            model='SuperMicro-4in1',
            slug='supermicro-4in1',
            subdevice_role='parent',
        )
        cls.role = DeviceRole.objects.create(name='cloud', slug='cloud', color='2196f3')
        cls.site = Site.objects.create(name='Test Site', slug='test-site')
        cls.device = Device.objects.create(
            device_type=cls.device_type,
            role=cls.role,
            site=cls.site,
            name='chassis-01.example.com',
        )

    def test_chassis_title_uses_device_name(self):
        self.assertEqual(get_chassis_title(self.device), 'chassis-01.example.com')

    def test_chassis_title_falls_back_to_model_without_name(self):
        self.device.name = ''
        self.device.save()
        self.assertEqual(get_chassis_title(self.device), 'SuperMicro-4in1')
