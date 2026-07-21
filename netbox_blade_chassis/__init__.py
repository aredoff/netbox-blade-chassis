from netbox.plugins import PluginConfig


class NetboxBladeChassisConfig(PluginConfig):
    name = 'netbox_blade_chassis'
    verbose_name = 'NetBox Blade Chassis'
    description = 'Visualize blade server bays inside chassis devices in rack elevations.'
    version = '0.1.0'
    base_url = 'blade-chassis'
    min_version = '4.6.0'
    max_version = '4.7.99'

    default_settings = {
        'enable_inline_elevation': True,
    }

    def ready(self):
        super().ready()
        from . import views  # noqa: F401 — registers plugin views via decorators


config = NetboxBladeChassisConfig
