import django
from django.test import TestCase

django.setup()

from dcim.models import DeviceBayTemplate, DeviceType, Manufacturer

from netbox_blade_chassis.forms import DeviceBayTemplateForm, _layout_requested
from netbox_blade_chassis.models import DeviceBayTemplateLayout


class LayoutRequestedTest(TestCase):
    def test_layout_requested_requires_both_coordinates(self):
        self.assertFalse(_layout_requested(None, 0))
        self.assertFalse(_layout_requested(0, None))
        self.assertFalse(_layout_requested(None, None))
        self.assertTrue(_layout_requested(0, 0))
        self.assertTrue(_layout_requested(1, 2))


class DeviceBayTemplateFormLayoutTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        manufacturer = Manufacturer.objects.create(name='Test', slug='test-forms')
        cls.device_type = DeviceType.objects.create(
            manufacturer=manufacturer,
            model='Blade Chassis Forms',
            slug='blade-chassis-forms',
            subdevice_role='parent',
        )
        cls.template = DeviceBayTemplate.objects.create(
            device_type=cls.device_type,
            name='Bay 1',
        )

    def _form_data(self, **overrides):
        data = {
            'device_type': self.device_type.pk,
            'name': self.template.name,
            'enabled': True,
            'position_x': '',
            'position_y': '',
        }
        data.update(overrides)
        return data

    def test_form_save_without_positions_deletes_layout(self):
        DeviceBayTemplateLayout.objects.create(
            device_bay_template=self.template,
            position_x=0,
            position_y=0,
        )
        form = DeviceBayTemplateForm(
            data=self._form_data(),
            instance=self.template,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        self.assertFalse(
            DeviceBayTemplateLayout.objects.filter(device_bay_template=self.template).exists()
        )

    def test_form_save_with_positions_creates_layout(self):
        form = DeviceBayTemplateForm(
            data=self._form_data(position_x=0, position_y=0),
            instance=self.template,
        )
        self.assertTrue(form.is_valid(), form.errors)
        form.save()
        layout = DeviceBayTemplateLayout.objects.get(device_bay_template=self.template)
        self.assertEqual(layout.position_x, 0)
        self.assertEqual(layout.position_y, 0)
