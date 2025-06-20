import bpy
from .icons import load_icons, unload_icons

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
    """Load custom icons, register all classes, and attach props to the Scene."""
    load_icons()
    for cls in classes:
        bpy.utils.register_class(cls)
    bpy.types.Scene.otpc_props = bpy.props.PointerProperty(type=OctanePointCloudProperties)


def unregister():
    """Unregister all classes, unload custom icons, and remove props from the Scene."""
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    unload_icons()
    del bpy.types.Scene.otpc_props
