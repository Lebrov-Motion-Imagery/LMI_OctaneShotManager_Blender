import os
import bpy
from bpy.types import Operator

from ..properties import OctanePointCloudProperties
from ..utils import (
    ensure_directory,
    build_scene_shot_prefix,
    generate_export_filename,
    ORBX_EXTENSION,
)


class LMB_OT_export_tags_orbx(Operator):
    """Export all tagged collections as ORBX files."""
    bl_idname = "lmb.export_tags_orbx"
    bl_label = "Export All TAGs to ORBX"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.otpc_props  # type: OctanePointCloudProperties

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

        # Gather tagged collections
        tag_items = [item.collection for item in props.tag_collections if item.collection]
        if not tag_items:
            self.report({'ERROR'}, "No TAG collections defined.")
            return {'CANCELLED'}

        scene_name = resolve_scene_name()
        shot_name = resolve_shot_name()

        base_root = bpy.path.abspath(props.root_output_dir)
        prefix = build_scene_shot_prefix(scene_name, shot_name)
        base_dir = os.path.join(base_root, "Shot_Manager", "TAGs", prefix)
        ensure_directory(base_dir)

        frame_start = props.tag_frame_start
        frame_end = props.tag_frame_end
        use_chunks = props.tag_use_chunks
        chunk = max(1, props.tag_chunk_size)

        ranges = []
        if use_chunks:
            for st in range(frame_start, frame_end + 1, chunk):
                en = min(st + chunk - 1, frame_end)
                ranges.append((st, en))
        else:
            ranges.append((frame_start, frame_end))

        for coll in tag_items:
            for st, en in ranges:
                tokens = [prefix, coll.name, f"{st}-{en}"]
                filename = generate_export_filename(tokens, ORBX_EXTENSION)
                filepath = os.path.join(base_dir, filename)
                bpy.ops.export.orbx(
                    filepath=filepath,
                    check_existing=False,
                    filename=filename,
                    frame_start=st,
                    frame_end=en,
                    frame_subframe=0,
                )

        self.report({'INFO'}, "TAG ORBX export completed.")
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
