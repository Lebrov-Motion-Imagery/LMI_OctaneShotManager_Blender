import os
import bpy
from bpy.types import Operator

from ..properties import OctanePointCloudProperties
from ..utils import (
    ensure_directory,
    generate_export_filename,
    build_scene_shot_prefix,
)


class LMB_OT_export_tags_orbx(Operator):
    """Export all tagged collections to ORBX files, optionally in chunks."""

    bl_idname = "lmb.export_tags_orbx"
    bl_label = "Export All TAGs to ORBX"
    bl_options = {'REGISTER', 'UNDO'}

    def _resolve_scene_name(self, context, props):
        if props.scene_name_source == 'FILE':
            filepath = bpy.data.filepath
            return os.path.splitext(os.path.basename(filepath))[0] if filepath else ""
        if props.scene_name_source == 'SCENE':
            return context.scene.name
        return props.scene_name_manual

    def _resolve_shot_name(self, context, props):
        if props.shot_name_source == 'OBJECT':
            obj = props.shot_object_source
            return obj.name if obj else ""
        return props.shot_name_manual

    def execute(self, context):
        props: OctanePointCloudProperties = context.scene.otpc_props
        collections = [item.collection for item in props.tag_collections if item.collection]

        if not collections:
            self.report({'ERROR'}, "No TAG collections defined.")
            return {'CANCELLED'}

        base_root = bpy.path.abspath(props.root_output_dir)
        if not base_root:
            self.report({'ERROR'}, "Output directory not set.")
            return {'CANCELLED'}

        scene_name = self._resolve_scene_name(context, props)
        shot_name = self._resolve_shot_name(context, props)
        prefix = build_scene_shot_prefix(scene_name, shot_name)

        export_dir = os.path.join(base_root, "Shot_Manager", "TAGs", prefix)
        ensure_directory(export_dir)

        frame_start = props.tag_frame_start
        frame_end = props.tag_frame_end

        if props.tag_use_chunks:
            chunk_size = max(props.tag_chunk_size, 1)
            ranges = []
            for start in range(frame_start, frame_end + 1, chunk_size):
                end = min(start + chunk_size - 1, frame_end)
                ranges.append((start, end))
        else:
            ranges = [(frame_start, frame_end)]

        for coll in collections:
            for start, end in ranges:
                name_parts = [prefix, coll.name, f"{start}-{end}"]
                filename = generate_export_filename(name_parts, "orbx")
                filepath = os.path.join(export_dir, filename)

                bpy.ops.export.orbx(
                    filepath=filepath,
                    check_existing=False,
                    filename=filename,
                    frame_start=start,
                    frame_end=end,
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
