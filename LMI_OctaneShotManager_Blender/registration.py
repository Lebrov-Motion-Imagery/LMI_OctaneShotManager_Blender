import bpy
from .icons import load_icons, unload_icons

from .properties import OctanePointCloudProperties
from .exporters.csv_export import LMB_OT_export_csv
from .exporters.abc_export import LMB_OT_export_abc
from .tags_workflow import (
    TagCollectionItem,
    LMB_UL_tag_collections,
    LMB_OT_tag_collection_add,
    LMB_OT_tag_collection_remove,
    LMB_OT_export_tags_orbx,
)
from .ui import POINTCLOUD_PT_panel

classes = (
    # Register the PropertyGroup used by OctanePointCloudProperties first so
    # Blender can resolve the CollectionProperty reference on registration.
    TagCollectionItem,
    OctanePointCloudProperties,
    LMB_OT_export_csv,
    LMB_OT_export_abc,
    LMB_UL_tag_collections,
    LMB_OT_tag_collection_add,
    LMB_OT_tag_collection_remove,
    LMB_OT_export_tags_orbx,
    POINTCLOUD_PT_panel,
)


def register():
    """Load icons and register all classes and properties.

    This function is safe to call multiple times. It avoids the "already
    registered" errors that can occur when the add-on is reloaded while
    developing in Blender."""

    load_icons()
    for cls in classes:
        # ``is_registered`` is provided by Blender for all RNA classes.
        if getattr(cls, "is_registered", False):
            continue
        bpy.utils.register_class(cls)

    if not hasattr(bpy.types.Scene, "otpc_props"):
        bpy.types.Scene.otpc_props = bpy.props.PointerProperty(
            type=OctanePointCloudProperties
        )

        # Initialize TAGs frame range properties from the scene
        for scene in bpy.data.scenes:
            props = scene.otpc_props
            props.tag_frame_start = scene.frame_start
            props.tag_frame_end = scene.frame_end
            props.tag_use_chunks = True
            if props.tag_chunk_size <= 0:
                props.tag_chunk_size = 25


def unregister():
    """Unregister classes and clean up custom properties and icons."""

    for cls in reversed(classes):
        if getattr(cls, "is_registered", False):
            bpy.utils.unregister_class(cls)

    unload_icons()

    if hasattr(bpy.types.Scene, "otpc_props"):
        del bpy.types.Scene.otpc_props
