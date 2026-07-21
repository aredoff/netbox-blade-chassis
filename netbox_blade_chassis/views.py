from dcim.models import DeviceBayTemplate, DeviceType
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.exceptions import ValidationError
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext_lazy as _
from django.views import View
from netbox.views import generic
from utilities.views import ViewTab, register_model_view

from netbox_blade_chassis.forms import (
    DeviceBayTemplateCreateForm,
    DeviceBayTemplateForm,
    DeviceBayTemplateLayoutBulkForm,
    _layout_requested,
    _parse_position,
)
from netbox_blade_chassis.layout import (
    LayoutEntry,
    get_symmetric_column_count,
    group_layout_by_row,
    validate_grid_symmetry,
)
from netbox_blade_chassis.models import DeviceBayTemplateLayout


@register_model_view(DeviceType, name='blade-layout', path='blade-layout')
class DeviceTypeBladeLayoutView(LoginRequiredMixin, PermissionRequiredMixin, View):
    template_name = 'netbox_blade_chassis/devicetype_blade_layout.html'
    tab = ViewTab(
        label=_('Blade Layout'),
        permission='dcim.view_devicetype',
        weight=450,
    )

    def get_permission_required(self):
        if self.request.method == 'POST':
            return ['dcim.change_devicetype']
        return ['dcim.view_devicetype']

    def get(self, request, pk):
        device_type = get_object_or_404(DeviceType, pk=pk)
        rows = _build_rows(device_type)
        preview_rows = _build_preview(rows)

        return render(request, self.template_name, {
            'object': device_type,
            'rows': rows,
            'preview_rows': preview_rows,
        })

    def post(self, request, pk):
        device_type = get_object_or_404(DeviceType, pk=pk)
        pending = []

        for template in DeviceBayTemplate.objects.filter(device_type=device_type):
            layout = DeviceBayTemplateLayout.objects.filter(device_bay_template=template).first()
            form = DeviceBayTemplateLayoutBulkForm(
                request.POST,
                instance=layout,
                prefix=f'bay-{template.pk}',
            )
            if not form.is_valid():
                messages.error(
                    request,
                    _('Invalid layout for bay template {name}.').format(name=template.name),
                )
                return redirect('dcim:devicetype_blade-layout', pk=pk)
            pending.append((
                template,
                _parse_position(form.cleaned_data.get('position_x')),
                _parse_position(form.cleaned_data.get('position_y')),
            ))

        pending_layout_map = {}
        for template, position_x, position_y in pending:
            if _layout_requested(position_x, position_y):
                pending_layout_map[template.name] = LayoutEntry(position_x, position_y)

        try:
            validate_grid_symmetry(pending_layout_map)
        except ValidationError as exc:
            messages.error(request, exc.messages[0])
            return redirect('dcim:devicetype_blade-layout', pk=pk)

        with transaction.atomic():
            DeviceBayTemplateLayout.objects.filter(
                device_bay_template__device_type=device_type,
            ).delete()
            DeviceBayTemplateLayout.objects.bulk_create([
                DeviceBayTemplateLayout(
                    device_bay_template=template,
                    position_x=position_x,
                    position_y=position_y,
                )
                for template, position_x, position_y in pending
                if _layout_requested(position_x, position_y)
            ])

        messages.success(request, _('Saved {count} bay layout(s).').format(count=len(pending_layout_map)))
        return redirect('dcim:devicetype_blade-layout', pk=pk)


@register_model_view(DeviceBayTemplate, name='add', detail=False)
class DeviceBayTemplateCreateView(generic.ComponentCreateView):
    queryset = DeviceBayTemplate.objects.all()
    form = DeviceBayTemplateCreateForm
    model_form = DeviceBayTemplateForm


@register_model_view(DeviceBayTemplate, name='edit')
class DeviceBayTemplateEditView(generic.ObjectEditView):
    queryset = DeviceBayTemplate.objects.all()
    form = DeviceBayTemplateForm


def _build_rows(device_type):
    rows = []
    for template in DeviceBayTemplate.objects.filter(device_type=device_type).order_by('name'):
        layout = DeviceBayTemplateLayout.objects.filter(device_bay_template=template).first()
        form = DeviceBayTemplateLayoutBulkForm(
            instance=layout,
            prefix=f'bay-{template.pk}',
        )
        if layout is None:
            form.initial.update({
                'position_x': None,
                'position_y': None,
            })
        rows.append({
            'template': template,
            'layout': layout,
            'form': form,
        })
    return rows


def _build_preview(rows):
    layout_map = {
        row['template'].name: LayoutEntry(
            row['layout'].position_x,
            row['layout'].position_y,
        )
        for row in rows
        if row['layout']
    }
    if not layout_map:
        return []

    grouped = group_layout_by_row(layout_map)
    column_count = get_symmetric_column_count(grouped)
    preview = []
    for row_index in sorted(grouped.keys()):
        cells_by_x = {
            position_x: name
            for position_x, name in grouped[row_index]
        }
        preview.append([
            cells_by_x.get(position_x, '')
            for position_x in range(column_count)
        ])
    return preview
