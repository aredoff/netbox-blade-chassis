from django.utils.translation import gettext as _
from svgwrite.container import Hyperlink
from svgwrite.masking import ClipPath
from svgwrite.shapes import Line, Rect
from svgwrite.text import Text, TSpan

from dcim.models import Device
from dcim.svg.racks import RackElevationSVG, truncate_text
from utilities.html import foreground_color

from netbox_blade_chassis.layout import (
    device_has_blade_layout,
    get_blade_label,
    get_chassis_title,
    get_layout_map,
    get_symmetric_column_count,
    group_layout_by_row,
    mirror_column_index,
)


class BladeChassisRackElevationSVG(RackElevationSVG):
    HEADER_HEIGHT = 18
    HEADER_FONT_SIZE = 10
    CELL_FONT_SIZE = 7
    LINE_HEIGHT_RATIO = 1.25

    BLADE_STYLES = """
        svg .blade-chassis { stroke: none; }
        svg .blade-grid-bg { fill: var(--nbx-rack-slot-bg); stroke: none; }
        svg .blade-cell-empty { fill: color-mix(in srgb, var(--nbx-rack-slot-bg) 65%, var(--nbx-rack-bg)); stroke: none; }
        svg .blade-cell-filled { stroke: none; opacity: 0.92; }
        svg .blade-grid-line { stroke: var(--nbx-rack-slot-border); stroke-width: 1; }
        svg .blade-header-label { font-size: 10px; font-weight: 600; }
        svg .blade-cell-label { font-size: 7px; }
        svg .blade-cell-empty-label { font-size: 8px; fill: var(--nbx-rack-unit-color); opacity: 0.45; }
    """

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, user=user, **kwargs)
        self._user = user

    def _setup_drawing(self):
        drawing = super()._setup_drawing()
        drawing.defs.add(drawing.style(self.BLADE_STYLES))
        return drawing

    def _device_is_viewable(self, device):
        if device.pk in self.permitted_device_ids:
            return True
        if self._user is None:
            return True
        return Device.objects.restrict(self._user, 'view').filter(pk=device.pk).exists()

    def draw_device_front(self, device, coords, size):
        if device_has_blade_layout(device.device_type):
            self._draw_blade_chassis(device, coords, size)
        else:
            super().draw_device_front(device, coords, size)

    def draw_device_rear(self, device, coords, size):
        if device_has_blade_layout(device.device_type):
            self._draw_blade_chassis(device, coords, size, mirrored=True)
        else:
            super().draw_device_rear(device, coords, size)

    def _draw_blade_chassis(self, device, coords, size, mirrored=False):
        x, y = coords
        width, height = size
        layout_map = get_layout_map(device.device_type)
        if not layout_map:
            super().draw_device_front(device, coords, size)
            return

        bays_by_name = {bay.name: bay for bay in device.devicebays.all()}
        rows = group_layout_by_row(layout_map)
        row_indices = sorted(rows.keys())
        row_count = len(row_indices)
        column_count = get_symmetric_column_count(rows)

        header_height = min(self.HEADER_HEIGHT, max(height * 0.18, 12))
        inner_y = y + header_height
        inner_height = max(height - header_height, 1)
        row_height = inner_height / row_count if row_count else inner_height
        column_width = width / column_count if column_count else width

        color = device.role.color if device.role else None
        header_bg = f'#{color}' if color else 'var(--nbx-rack-slot-bg)'
        text_color = f'#{foreground_color(color)}' if color else 'var(--nbx-rack-unit-color)'
        is_shaded = self.highlight_devices and device not in self.highlight_devices
        css_extra = ' shaded' if is_shaded else ''

        clip_id = f'blade-clip-{device.pk}'
        clip_path = ClipPath(id=clip_id)
        clip_path.add(Rect((x, inner_y), (width, inner_height)))
        self.drawing.defs.add(clip_path)

        chassis_link = Hyperlink(href=f'{self.base_url}{device.get_absolute_url()}', target='_parent')
        chassis_link.add(Rect(coords, size, style=f'fill: {header_bg}', class_=f'blade-chassis{css_extra}'))
        chassis_link.add(
            Text(
                truncate_text(get_chassis_title(device), width, font_size=self.HEADER_FONT_SIZE),
                insert=(x + width / 2, y + header_height / 2),
                fill=text_color,
                class_=f'blade-header-label{css_extra}',
            )
        )
        self.drawing.add(chassis_link)

        self.drawing.add(Rect((x, inner_y), (width, inner_height), class_=f'blade-grid-bg{css_extra}'))

        for row_number, row_index in enumerate(row_indices):
            cell_y = inner_y + row_number * row_height
            cells_by_x = dict(rows[row_index])

            for position_x in range(column_count):
                bay_name = cells_by_x.get(position_x)
                bay = bays_by_name.get(bay_name) if bay_name else None
                display_x = mirror_column_index(position_x, column_count) if mirrored else position_x
                cell_x = x + display_x * column_width
                self._draw_blade_cell(
                    bay=bay,
                    coords=(cell_x, cell_y),
                    size=(column_width, row_height),
                    css_extra=css_extra,
                    clip_id=clip_id,
                )

        self._draw_blade_grid_lines(
            x=x,
            y=inner_y,
            width=width,
            height=inner_height,
            row_count=row_count,
            column_count=column_count,
            css_extra=css_extra,
        )
        self.drawing.add(Line(
            start=(x, inner_y),
            end=(x + width, inner_y),
            class_=f'blade-grid-line{css_extra}',
        ))

    def _draw_blade_grid_lines(self, x, y, width, height, row_count, column_count, css_extra=''):
        row_height = height / row_count if row_count else height
        column_width = width / column_count if column_count else width

        for column_index in range(1, column_count):
            line_x = x + column_index * column_width
            self.drawing.add(Line(
                start=(line_x, y),
                end=(line_x, y + height),
                class_=f'blade-grid-line{css_extra}',
            ))

        for row_index in range(1, row_count):
            line_y = y + row_index * row_height
            self.drawing.add(Line(
                start=(x, line_y),
                end=(x + width, line_y),
                class_=f'blade-grid-line{css_extra}',
            ))

    def _draw_blade_cell(self, bay, coords, size, css_extra='', clip_id=None):
        cell_x, cell_y = coords
        cell_width, cell_height = size
        clip_attr = {'clip-path': f'url(#{clip_id})'} if clip_id else {}
        text_padding = 2
        text_width = max(cell_width - text_padding * 2, 1)
        text_height = max(cell_height - text_padding * 2, 1)

        installed = bay.installed_device if bay else None
        if installed and self._device_is_viewable(installed):
            label = get_blade_label(installed)
            description = _('Blade: {name}').format(name=label)
            blade_color = installed.role.color if installed.role else None
            fill_style = f'fill: #{blade_color}' if blade_color else None
            label_color = f'#{foreground_color(blade_color)}' if blade_color else 'var(--nbx-rack-unit-color)'

            link = Hyperlink(href=f'{self.base_url}{installed.get_absolute_url()}', target='_parent')
            link.set_desc(description)
            link.add(Rect(coords, size, style=fill_style, class_=f'blade-cell-filled{css_extra}', **clip_attr))
            link.add(self._build_cell_text(
                label,
                center_x=cell_x + cell_width / 2,
                center_y=cell_y + cell_height / 2,
                width=text_width,
                height=text_height,
                fill=label_color,
                css_class=f'blade-cell-label{css_extra}',
                clip_attr=clip_attr,
            ))
            self.drawing.add(link)
        else:
            self.drawing.add(Rect(coords, size, class_=f'blade-cell-empty{css_extra}', **clip_attr))
            if cell_height >= 10 and cell_width >= 10:
                self.drawing.add(Text(
                    '—',
                    insert=(cell_x + cell_width / 2, cell_y + cell_height / 2),
                    class_=f'blade-cell-empty-label{css_extra}',
                    **clip_attr,
                ))

    def _build_cell_text(self, text, center_x, center_y, width, height, fill, css_class, clip_attr=None):
        lines = self._wrap_text(text, width, height, self.CELL_FONT_SIZE)
        line_height = self.CELL_FONT_SIZE * self.LINE_HEIGHT_RATIO
        block_height = line_height * len(lines)
        start_y = center_y - block_height / 2 + line_height / 2

        text_elem = Text('', fill=fill, class_=css_class, **(clip_attr or {}))
        text_elem['text-anchor'] = 'middle'

        for index, line in enumerate(lines):
            if index == 0:
                text_elem.add(TSpan(line, insert=(center_x, start_y)))
            else:
                text_elem.add(TSpan(line, x=[center_x], dy=[f'{self.LINE_HEIGHT_RATIO}em']))

        return text_elem

    def _wrap_text(self, text, max_width, max_height, font_size):
        char_width = font_size * 0.55
        max_chars = max(1, int(max_width / char_width))
        max_lines = max(1, int(max_height / (font_size * self.LINE_HEIGHT_RATIO)))

        chunks = []
        for part in text.split('.'):
            if chunks:
                chunks.append('.')
            if part:
                chunks.append(part)

        lines = []
        current = ''
        for chunk in chunks:
            candidate = current + chunk
            if len(candidate) <= max_chars:
                current = candidate
                continue

            if current:
                lines.append(current)
                current = ''

            while chunk and len(lines) < max_lines:
                if len(chunk) <= max_chars:
                    current = chunk
                    chunk = ''
                    break
                lines.append(chunk[:max_chars])
                chunk = chunk[max_chars:]

        if current and len(lines) < max_lines:
            lines.append(current)

        if not lines:
            lines = [truncate_text(text, max_width, font_size=font_size)]
        elif len(lines) > max_lines:
            lines = lines[:max_lines]

        joined_length = sum(len(line) for line in lines)
        if joined_length < len(text) and lines:
            last = lines[-1]
            if len(last) > 3:
                lines[-1] = last[: max(1, max_chars - 1)] + '…'
            else:
                lines[-1] = '…'

        return lines
