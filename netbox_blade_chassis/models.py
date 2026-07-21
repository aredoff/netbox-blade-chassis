from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _


class DeviceBayTemplateLayout(models.Model):
    device_bay_template = models.OneToOneField(
        to='dcim.DeviceBayTemplate',
        on_delete=models.CASCADE,
        related_name='blade_layout',
    )
    position_x = models.PositiveIntegerField(
        verbose_name=_('position X'),
        default=0,
        help_text=_('Horizontal slot index within the row (0-based, left to right).'),
    )
    position_y = models.PositiveIntegerField(
        verbose_name=_('position Y'),
        default=0,
        help_text=_('Row index within the chassis (0-based, top to bottom).'),
    )

    class Meta:
        ordering = ('position_y', 'position_x')
        verbose_name = _('device bay template layout')
        verbose_name_plural = _('device bay template layouts')

    def __str__(self):
        return f'{self.device_bay_template}: ({self.position_x}, {self.position_y})'

    @property
    def device_type(self):
        return self.device_bay_template.device_type

    def clean(self):
        super().clean()

        if not hasattr(self, 'device_bay_template'):
            return

        device_type = self.device_bay_template.device_type
        duplicates = DeviceBayTemplateLayout.objects.filter(
            device_bay_template__device_type=device_type,
            position_x=self.position_x,
            position_y=self.position_y,
        ).exclude(pk=self.pk)

        if duplicates.exists():
            raise ValidationError({
                'position_x': _(
                    'Another bay template on this device type already uses position ({x}, {y}).'
                ).format(x=self.position_x, y=self.position_y),
            })
