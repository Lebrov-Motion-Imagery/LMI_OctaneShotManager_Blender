import bpy

from .properties import OctanePointCloudProperties
from .exporters.csv_export import LMB_OT_export_csv
from .exporters.abc_export import LMB_OT_export_abc
from .ui import POINTCLOUD_PT_panel


classes = (
    OctanePointCloudProperties,
    LMB_OT_export_csv,
    LMB_OT_export_abc,
    POINTCLOUD_PT_panel,
)


def register():
    """Register all classes and add the property group to Scene."""
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.otpc_props = bpy.props.PointerProperty(type=OctanePointCloudProperties)


def unregister():
    """Unregister all classes and remove the property group from Scene."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    del bpy.types.Scene.otpc_props
