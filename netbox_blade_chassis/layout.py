from collections import defaultdict
from typing import NamedTuple

from dcim.models import Device, DeviceType
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from netbox_blade_chassis.models import DeviceBayTemplateLayout


class LayoutEntry(NamedTuple):
    position_x: int
    position_y: int


def get_layout_map(device_type: DeviceType) -> dict[str, LayoutEntry]:
    layouts = DeviceBayTemplateLayout.objects.filter(
        device_bay_template__device_type=device_type,
    ).select_related('device_bay_template')

    return {
        layout.device_bay_template.name: LayoutEntry(
            layout.position_x,
            layout.position_y,
        )
        for layout in layouts
    }


def device_has_blade_layout(device_type: DeviceType) -> bool:
    return DeviceBayTemplateLayout.objects.filter(
        device_bay_template__device_type=device_type,
    ).exists()


def group_layout_by_row(
    layout_map: dict[str, LayoutEntry],
) -> dict[int, list[tuple[int, str]]]:
    rows: dict[int, list[tuple[int, str]]] = defaultdict(list)
    for name, entry in layout_map.items():
        rows[entry.position_y].append((entry.position_x, name))
    for row in rows.values():
        row.sort(key=lambda item: item[0])
    return dict(rows)


def get_symmetric_column_count(layout_map: dict[int, list[tuple[int, str]]]) -> int:
    if not layout_map:
        return 0
    return max(max(position_x for position_x, _ in cells) + 1 for cells in layout_map.values())


def mirror_column_index(position_x: int, column_count: int) -> int:
    return column_count - 1 - position_x


def validate_grid_symmetry(layout_map: dict[str, LayoutEntry]) -> None:
    rows: dict[int, set[int]] = defaultdict(set)
    for entry in layout_map.values():
        rows[entry.position_y].add(entry.position_x)

    if not rows:
        return

    row_column_counts = [max(columns) + 1 for columns in rows.values()]
    if len(set(row_column_counts)) > 1:
        raise ValidationError(_('All blade rows must have the same number of columns.'))


def get_chassis_title(device: Device) -> str:
    return device.name or device.device_type.model


def get_blade_label(device: Device) -> str:
    name = device.name or str(device.device_type)
    if '#' in name:
        return name.split('#', 1)[0]
    return name
