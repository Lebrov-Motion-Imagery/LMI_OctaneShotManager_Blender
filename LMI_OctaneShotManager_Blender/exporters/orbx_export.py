import os
import bpy
from bpy.types import Operator

from ..utils import ensure_directory, generate_export_filename, build_scene_shot_prefix
from ..properties import OctanePointCloudProperties


class LMB_OT_export_orbx_tags(Operator):
    """Export each tagged collection to ORBX files."""
    bl_idname = "lmb.export_orbx_tags"
    bl_label = "Export All Tags to ORBX"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.otpc_props  # type: OctanePointCloudProperties
        scene = context.scene

        if not props.root_output_dir:
            self.report({'ERROR'}, "Output root directory is not set.")
            return {'CANCELLED'}
        if not props.tag_collections:
            self.report({'ERROR'}, "No TAG collections defined.")
            return {'CANCELLED'}

        def resolve_scene_name():
            if props.scene_name_source == 'FILE':
                filepath = bpy.data.filepath
                return os.path.splitext(os.path.basename(filepath))[0] if filepath else ""
            if props.scene_name_source == 'SCENE':
                return scene.name
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

        frame_start = props.tag_frame_start
        frame_end = props.tag_frame_end
        chunk_size = max(1, props.tag_chunk_size)
        use_chunks = props.tag_use_chunks

        if use_chunks:
            ranges = []
            f = frame_start
            while f <= frame_end:
                e = min(f + chunk_size - 1, frame_end)
                ranges.append((f, e))
                f = e + 1
        else:
            ranges = [(frame_start, frame_end)]

        for item in props.tag_collections:
            coll = item.collection
            if not coll:
                continue
            coll_name = coll.name
            for fstart, fend in ranges:
                parts = [prefix, coll_name, f"{fstart}-{fend}"]
                filename = generate_export_filename(parts, "orbx")
                filepath = os.path.join(base_dir, filename)

                bpy.ops.export.orbx(
                    filepath=filepath,
                    check_existing=True,
                    filename=filename,
                    frame_start=fstart,
                    frame_end=fend,
                )

        self.report({'INFO'}, "ORBX export completed.")
        return {'FINISHED'}


classes = (
    LMB_OT_export_orbx_tags,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
