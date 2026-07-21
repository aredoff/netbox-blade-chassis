from netbox.plugins import PluginConfig

from .version import __version__


class NetboxBladeChassisConfig(PluginConfig):
    name = 'netbox_blade_chassis'
    verbose_name = 'NetBox Blade Chassis'
    description = 'Visualize blade server bays inside chassis devices in rack elevations.'
    author = 'Aleksandr Krasnov'
    author_email = 'aredoff@gmail.com'
    version = __version__
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
