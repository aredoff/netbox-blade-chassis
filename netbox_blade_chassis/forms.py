from django import forms
from django.utils.translation import gettext_lazy as _

from dcim.forms.model_forms import DeviceBayTemplateForm as BaseDeviceBayTemplateForm
from dcim.forms.object_create import ComponentCreateForm
from utilities.forms.fields import ExpandableNameField
from utilities.forms.rendering import FieldSet

from netbox_blade_chassis.models import DeviceBayTemplateLayout


def _parse_position(value):
    if value in (None, ''):
        return None
    return int(value)


def _layout_requested(position_x, position_y):
    return position_x is not None and position_y is not None


class DeviceBayTemplateLayoutBulkForm(forms.ModelForm):
    position_x = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': 0}),
    )
    position_y = forms.IntegerField(
        required=False,
        min_value=0,
        widget=forms.NumberInput(attrs={'class': 'form-control form-control-sm', 'min': 0}),
    )

    class Meta:
        model = DeviceBayTemplateLayout
        fields = ('position_x', 'position_y')


class DeviceBayTemplateForm(BaseDeviceBayTemplateForm):
    class Meta(BaseDeviceBayTemplateForm.Meta):
        fields = BaseDeviceBayTemplateForm.Meta.fields

    position_x = forms.IntegerField(
        label=_('Position X'),
        min_value=0,
        required=False,
        help_text=_(
            'Horizontal slot index within the row (0-based). Both Position X and Y are required for elevation display.'
        ),
    )
    position_y = forms.IntegerField(
        label=_('Position Y'),
        min_value=0,
        required=False,
        help_text=_(
            'Row index within the blade grid (0-based). Both Position X and Y are required for elevation display.'
        ),
    )

    fieldsets = (
        FieldSet('device_type', 'name', 'label', 'enabled', 'description', name=_('Template')),
        FieldSet('position_x', 'position_y', name=_('Blade Layout')),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            layout = DeviceBayTemplateLayout.objects.filter(device_bay_template=self.instance).first()
            if layout:
                self.fields['position_x'].initial = layout.position_x
                self.fields['position_y'].initial = layout.position_y

    def save(self, commit=True):
        instance = super().save(commit)
        position_x = _parse_position(self.cleaned_data.get('position_x'))
        position_y = _parse_position(self.cleaned_data.get('position_y'))

        if not _layout_requested(position_x, position_y):
            DeviceBayTemplateLayout.objects.filter(device_bay_template=instance).delete()
            return instance

        DeviceBayTemplateLayout.objects.update_or_create(
            device_bay_template=instance,
            defaults={
                'position_x': position_x,
                'position_y': position_y,
            },
        )
        return instance


class DeviceBayTemplateCreateForm(ComponentCreateForm, DeviceBayTemplateForm):
    position_x = ExpandableNameField(
        label=_('Position X'),
        required=False,
        help_text=_('Alphanumeric ranges are supported. (Must match the number of names being created.)'),
    )
    position_y = ExpandableNameField(
        label=_('Position Y'),
        required=False,
        help_text=_('Alphanumeric ranges are supported. (Must match the number of names being created.)'),
    )
    replication_fields = ('name', 'label', 'position_x', 'position_y')

    fieldsets = (
        FieldSet('device_type', 'name', 'label', 'enabled', 'description', name=_('Template')),
        FieldSet('position_x', 'position_y', name=_('Blade Layout')),
    )

    class Meta(DeviceBayTemplateForm.Meta):
        exclude = ('name', 'label', 'position_x', 'position_y')
