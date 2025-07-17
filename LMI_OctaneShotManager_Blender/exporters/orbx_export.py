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
    make_direct_merged_orbx_export_manager,
    solo_tagged_collections,
)


def _resolve_scene_name(props, scene):
    """Return scene name based on the configured naming source."""
    if props.scene_name_source == 'FILE':
        filepath = bpy.data.filepath
        return os.path.splitext(os.path.basename(filepath))[0] if filepath else ""
    if props.scene_name_source == 'SCENE':
        return scene.name
    return props.scene_name_manual


def _resolve_shot_name(props):
    """Return shot name based on the configured naming source."""
    if props.shot_name_source == 'OBJECT':
        obj = props.shot_object_source
        return obj.name if obj else ""
    return props.shot_name_manual


class LMB_OT_export_orbx_tags(Operator):
    """Export tagged collections to individual ORBX files."""
    bl_idname = "lmb.export_orbx_tags"
    bl_label = "Export all Tags to a 'Per Tag' ORBX"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.otpc_props  # type: OctanePointCloudProperties
        scene = context.scene

        collections = get_tagged_collections(scene)
        if not collections:
            self.report({'ERROR'}, "No tagged collections defined.")
            return {'CANCELLED'}

        solo_tagged_collections(context)

        scene_name = _resolve_scene_name(props, scene)
        shot_name = _resolve_shot_name(props)

        base_root = bpy.path.abspath(props.root_output_dir)
        prefix = build_scene_shot_prefix(scene_name, shot_name)
        export_dir = os.path.join(
            base_root, "Shot_Manager", "TAGs", prefix, "Per_Tag_ORBX"
        )
        ensure_directory(export_dir)

        frame_start = props.tag_frame_start
        frame_end = props.tag_frame_end
        use_chunks = props.tag_use_chunks
        chunk_size = max(1, props.tag_chunk_size)

        ranges = calculate_part_ranges(frame_start, frame_end, chunk_size) if use_chunks else [(1, frame_start, frame_end)]

        task_queue = []
        for coll in collections:
            base_name = f"{prefix}_{coll.name}"
            try:
                parts = filter_missing_parts(
                    ranges,
                    export_dir,
                    base_name,
                    props.overwrite_orbx,
                    chunk_size if use_chunks else None,
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


class LMB_OT_export_orbx_direct_merged(Operator):
    """Export all tagged collections directly into a merged ORBX sequence."""
    bl_idname = "lmb.export_orbx_direct_merged"
    bl_label = "Export directly to a Merged ORBX"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.otpc_props  # type: OctanePointCloudProperties
        scene = context.scene

        collections = get_tagged_collections(scene)
        if not collections:
            self.report({'ERROR'}, "No tagged collections defined.")
            return {'CANCELLED'}

        solo_tagged_collections(context)

        scene_name = _resolve_scene_name(props, scene)
        shot_name = _resolve_shot_name(props)

        base_root = bpy.path.abspath(props.root_output_dir)
        prefix = build_scene_shot_prefix(scene_name, shot_name)
        export_dir = os.path.join(
            base_root, "Shot_Manager", "TAGs", prefix, "Merged_ORBX"
        )
        ensure_directory(export_dir)

        frame_start = props.tag_frame_start
        frame_end = props.tag_frame_end
        use_chunks = props.tag_use_chunks
        chunk_size = max(1, props.tag_chunk_size)

        ranges = calculate_part_ranges(frame_start, frame_end, chunk_size) if use_chunks else [(1, frame_start, frame_end)]

        base_name = f"{prefix}_Merged"
        try:
            parts = filter_missing_parts(
                ranges,
                export_dir,
                base_name,
                props.overwrite_orbx,
                chunk_size if use_chunks else None,
            )
        except ValueError as exc:
            self.report({'ERROR'}, str(exc))
            return {'CANCELLED'}

        task_queue = [(part_no, frm, to) for part_no, frm, to in parts]

        export_manager = make_direct_merged_orbx_export_manager(task_queue, export_dir, base_name, props.overwrite_orbx, poll_interval=3.0)
        bpy.app.timers.register(export_manager, first_interval=0.0)

        self.report({'INFO'}, "ORBX export started.")
        return {'FINISHED'}
