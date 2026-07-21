# NetBox Blade Chassis Plugin

NetBox plugin that renders blade server bays inside chassis devices in rack SVG elevations.

## Features

- Configure bay grid coordinates (`position_x`, `position_y`) on **Device Bay Template** forms or the **Blade Layout** tab on Device Type
- Empty coordinates: bay is not shown in rack elevation
- Filled coordinates: bay is rendered as a blade cell with child device hostname
- Symmetric grid validation on bulk save (Blade Layout tab)
- Inline rack elevation via plugin SVG endpoint
- Clickable blade cells linking to child devices
