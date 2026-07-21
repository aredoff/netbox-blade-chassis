from netbox.plugins import PluginTemplateExtension
from netbox.plugins.utils import get_plugin_config


class ElevationPatchExtension(PluginTemplateExtension):
    def head(self):
        if not get_plugin_config('netbox_blade_chassis', 'enable_inline_elevation', True):
            return ''
        return self.render('netbox_blade_chassis/inc/elevation_patch.html')


template_extensions = [
    ElevationPatchExtension,
]
