import os
import bpy
from bpy.types import Operator

from ..properties import OctanePointCloudProperties
from ..utils import (
    ensure_directory,
    generate_export_filename,
    build_scene_shot_prefix,
    sanitize_token,
    ORBX_EXTENSION,
)


class LMB_OT_export_tags_orbx(Operator):
    """Export all tagged collections to individual ORBX files."""
    bl_idname = "lmb.export_tags_orbx"
    bl_label = "Export All TAGs to ORBX"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.otpc_props  # type: OctanePointCloudProperties

        if not props.tag_collections:
            self.report({'ERROR'}, "No tagged collections defined.")
            return {'CANCELLED'}
        if not props.root_output_dir:
            self.report({'ERROR'}, "Output root directory is not set.")
            return {'CANCELLED'}

        def resolve_scene_name():
            if props.scene_name_source == 'FILE':
                filepath = bpy.data.filepath
                return os.path.splitext(os.path.basename(filepath))[0] if filepath else ""
            if props.scene_name_source == 'SCENE':
                return context.scene.name
            return props.scene_name_manual

        def resolve_shot_name():
            if props.shot_name_source == 'OBJECT':
                obj = props.shot_object_source
                return obj.name if obj else ""
            return props.shot_name_manual

        scene_name = resolve_scene_name()
        shot_name = resolve_shot_name()

        base_root = bpy.path.abspath(props.root_output_dir)
        prefix = build_scene_shot_prefix(scene_name, shot_name)
        base_dir = os.path.join(base_root, "Shot_Manager", "TAGs", prefix)
        ensure_directory(base_dir)

        exported = 0
        for item in props.tag_collections:
            coll = item.collection
            if not coll:
                continue
            objects = list(coll.all_objects)
            if not objects:
                continue

            coll_token = sanitize_token(coll.name)
            filename = generate_export_filename([prefix, coll_token], ORBX_EXTENSION)
            filepath = os.path.join(base_dir, filename)

            bpy.ops.object.select_all(action='DESELECT')
            for obj in objects:
                obj.select_set(True)
            context.view_layer.objects.active = objects[0]

            try:
                bpy.ops.octane.export_orbx(filepath=filepath)
            except Exception as e:
                self.report({'WARNING'}, f"Failed to export {coll.name}: {e}")
                continue
            finally:
                for obj in objects:
                    obj.select_set(False)

            exported += 1

        if not exported:
            self.report({'ERROR'}, "No ORBX files exported.")
            return {'CANCELLED'}

        self.report({'INFO'}, f"Exported {exported} ORBX file(s).")
        return {'FINISHED'}


classes = (
    LMB_OT_export_tags_orbx,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
