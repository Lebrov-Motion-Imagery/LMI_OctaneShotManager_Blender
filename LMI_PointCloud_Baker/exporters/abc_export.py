import os
import bpy
from bpy.types import Operator

from ..properties import OctanePointCloudProperties
from ..utils import (
    ensure_directory,
    generate_export_filename,
    build_asset_world_matrices,
    ABC_EXTENSION,
)


class LMB_OT_export_abc(Operator):
    """Export selected objects or collections as Alembic files with face sets."""
    bl_idname = "lmb.export_abc"
    bl_label = "Export Alembic Instances"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.otpc_props  # type: OctanePointCloudProperties

        # Determine sources
        if props.abc_src_type == 'OBJECT':
            sources = [props.abc_object_source] if props.abc_object_source else []
            root_folder = None
        else:
            sources = list(props.abc_collection_source.objects) if props.abc_collection_source else []
            root_folder = f"{props.abc_collection_source.name}_ABCs"

        if not sources:
            self.report({'ERROR'}, "No Alembic sources defined.")
            return {'CANCELLED'}

        # Prepare output directory
        base_dir = bpy.path.abspath(props.abc_output_dir)
        ensure_directory(base_dir)
        if root_folder:
            base_dir = os.path.join(base_dir, root_folder)
            ensure_directory(base_dir)

        # Export each object
        for obj in sources:
            # Build filename
            parts = [props.scene_name, props.shot_name, obj.name]
            filename = generate_export_filename(parts, ABC_EXTENSION)
            filepath = os.path.join(base_dir, filename)

            # Skip if exists and not overwriting
            if os.path.exists(filepath) and not props.overwrite_abc:
                continue

            # Ensure object is at origin for export
            orig_loc = obj.location.copy()
            obj.location = (0.0, 0.0, 0.0)

            # Select and export
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj
            bpy.ops.wm.alembic_export(
                filepath=filepath,
                selected=True,
                face_sets=True
            )

            # Restore location
            obj.location = orig_loc
            self.report({'INFO'}, f"Exported Alembic: {filename}")

        self.report({'INFO'}, "Alembic export completed.")
        return {'FINISHED'}


classes = (
    LMB_OT_export_abc,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
