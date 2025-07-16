import os
import bpy
from bpy.types import Operator

from ..properties import OctanePointCloudProperties
from ..utils import (
    ensure_directory,
    build_scene_shot_prefix,
)
from ..Workflows.TAGs.utils import (
    get_tagged_collections,
    calculate_part_ranges,
    filter_missing_parts,
    make_orbx_export_manager,
)


class LMB_OT_export_orbx_tags(Operator):
    """Export tagged collections to ORBX files."""
    bl_idname = "lmb.export_orbx_tags"
    bl_label = "Export All Tags to ORBX"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.otpc_props  # type: OctanePointCloudProperties
        scene = context.scene

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

        collections = get_tagged_collections(scene)
        if not collections:
            self.report({'ERROR'}, "No tagged collections defined.")
            return {'CANCELLED'}

        scene_name = resolve_scene_name()
        shot_name = resolve_shot_name()

        base_root = bpy.path.abspath(props.root_output_dir)
        prefix = build_scene_shot_prefix(scene_name, shot_name)
        export_dir = os.path.join(base_root, "Shot_Manager", "TAGs", prefix)
        ensure_directory(export_dir)

        frame_start = props.tag_frame_start
        frame_end = props.tag_frame_end
        use_chunks = props.tag_use_chunks
        chunk_size = max(1, props.tag_chunk_size)

        part_ranges = calculate_part_ranges(
            frame_start,
            frame_end,
            chunk_size if use_chunks else frame_end - frame_start + 1,
        )

        task_queue = []
        for coll in collections:
            base_name = f"{prefix}_{coll.name}"
            try:
                parts = filter_missing_parts(
                    part_ranges, export_dir, base_name, props.overwrite_orbx
                )
            except ValueError as exc:
                self.report({'ERROR'}, str(exc))
                return {'CANCELLED'}

            for part_no, frm, to in parts:
                task_queue.append((coll, part_no, frm, to))

        export_manager = make_orbx_export_manager(task_queue, export_dir, prefix, props.overwrite_orbx, poll_interval=3.0)
        bpy.app.timers.register(export_manager, first_interval=0.0)

        self.report({'INFO'}, "ORBX export started.")
        return {'FINISHED'}
