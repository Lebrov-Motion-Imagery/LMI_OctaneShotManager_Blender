"""Operators for merging ORBX chunks via Octane standalone."""

from __future__ import annotations

import os
import bpy
from bpy.types import Operator

from ..properties import OctanePointCloudProperties
from ..utils import ensure_directory, build_scene_shot_prefix
from ..Workflows.TAGs.utils import (
    get_tagged_collections,
    get_selected_tagged_collections,
    calculate_part_ranges,
    parse_orbx_sequence,
    make_orbx_merge_manager,
)


def _resolve_scene_name(
    props: OctanePointCloudProperties, scene: bpy.types.Scene
) -> str:
    if props.scene_name_source == 'FILE':
        filepath = bpy.data.filepath
        return (
            os.path.splitext(os.path.basename(filepath))[0]
            if filepath
            else ''
        )
    if props.scene_name_source == 'SCENE':
        return scene.name
    return props.scene_name_manual


def _resolve_shot_name(props: OctanePointCloudProperties) -> str:
    if props.shot_name_source == 'OBJECT':
        obj = props.shot_object_source
        return obj.name if obj else ''
    return props.shot_name_manual


def _collect_parts(directory: str, prefix: str, collections, expected):
    parts_map = {}
    for coll in collections:
        base = f"{prefix}_{coll.name}"
        parts, _ = parse_orbx_sequence(directory, base)
        if sorted(parts) != expected:
            return None, f"Missing ORBX chunks for tag {coll.name}."
        files = {
            pn: os.path.join(directory, f"{base}_pt{pn}_{s:03d}-{e:03d}.orbx")
            for pn, s, e in expected
        }
        parts_map[coll.name] = files
    return parts_map, None


def _build_tasks(parts_map, collections, out_dir, base_name, ranges):
    tasks = []
    coll_names = [c.name for c in collections]
    for part_no, frm, to in ranges:
        save_name = f"{base_name}_pt{part_no}_{frm:03d}-{to:03d}.orbx"
        save_path = os.path.join(out_dir, save_name)
        dest = parts_map[coll_names[0]][part_no]
        sources = [parts_map[name][part_no] for name in coll_names[1:]]
        tasks.append([save_path, dest] + sources)
    return tasks


class LMB_OT_merge_selected_tags(Operator):
    bl_idname = "lmb.merge_selected_tags"
    bl_label = "Merge selected Tags"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.otpc_props  # type: OctanePointCloudProperties
        scene = context.scene

        octane_exec = bpy.path.abspath(props.octane_standalone_path)
        if not os.path.isfile(octane_exec):
            self.report({'ERROR'}, 'Invalid Octane Standalone path')
            return {'CANCELLED'}

        collections = get_selected_tagged_collections(scene)
        if not collections:
            self.report({'ERROR'}, 'No selected tagged collections.')
            return {'CANCELLED'}

        scene_name = _resolve_scene_name(props, scene)
        shot_name = _resolve_shot_name(props)
        base_root = bpy.path.abspath(props.root_output_dir)
        prefix = build_scene_shot_prefix(scene_name, shot_name)
        per_tag_dir = os.path.join(
            base_root, 'Shot_Manager', 'TAGs', prefix, 'Per_Tag_ORBX'
        )
        merge_dir = os.path.join(
            base_root, 'Shot_Manager', 'TAGs', prefix, 'Merged_ORBX'
        )
        ensure_directory(merge_dir)

        frame_start = props.tag_frame_start
        frame_end = props.tag_frame_end
        chunk = max(1, props.tag_chunk_size)
        if props.tag_use_chunks:
            ranges = calculate_part_ranges(frame_start, frame_end, chunk)
        else:
            ranges = [(1, frame_start, frame_end)]

        expected = [(pn, s, e) for pn, s, e in ranges]
        parts_map, err = _collect_parts(
            per_tag_dir,
            prefix,
            collections,
            expected,
        )
        if err:
            self.report({'ERROR'}, err)
            return {'CANCELLED'}

        base_name = f"{prefix}_Merged_{'_'.join(c.name for c in collections)}"
        tasks = _build_tasks(
            parts_map,
            collections,
            merge_dir,
            base_name,
            ranges,
        )

        addon_dir = os.path.dirname(os.path.dirname(__file__))
        script_path = os.path.join(
            addon_dir, 'standalone_scripts', 'ORBXmerger.lua'
        )

        manager = make_orbx_merge_manager(
            tasks,
            octane_exec,
            script_path,
            poll_interval=3.0,
        )
        bpy.app.timers.register(manager, first_interval=0.0)

        self.report({'INFO'}, 'ORBX merging started.')
        return {'FINISHED'}


class LMB_OT_merge_all_tags(Operator):
    bl_idname = "lmb.merge_all_tags"
    bl_label = "Merge all Tags"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.otpc_props  # type: OctanePointCloudProperties
        scene = context.scene

        octane_exec = bpy.path.abspath(props.octane_standalone_path)
        if not os.path.isfile(octane_exec):
            self.report({'ERROR'}, 'Invalid Octane Standalone path')
            return {'CANCELLED'}

        collections = get_tagged_collections(scene)
        if not collections:
            self.report({'ERROR'}, 'No tagged collections defined.')
            return {'CANCELLED'}

        scene_name = _resolve_scene_name(props, scene)
        shot_name = _resolve_shot_name(props)
        base_root = bpy.path.abspath(props.root_output_dir)
        prefix = build_scene_shot_prefix(scene_name, shot_name)
        per_tag_dir = os.path.join(
            base_root, 'Shot_Manager', 'TAGs', prefix, 'Per_Tag_ORBX'
        )
        merge_dir = os.path.join(
            base_root, 'Shot_Manager', 'TAGs', prefix, 'Merged_ORBX'
        )
        ensure_directory(merge_dir)

        frame_start = props.tag_frame_start
        frame_end = props.tag_frame_end
        chunk = max(1, props.tag_chunk_size)
        if props.tag_use_chunks:
            ranges = calculate_part_ranges(frame_start, frame_end, chunk)
        else:
            ranges = [(1, frame_start, frame_end)]

        expected = [(pn, s, e) for pn, s, e in ranges]
        parts_map, err = _collect_parts(
            per_tag_dir,
            prefix,
            collections,
            expected,
        )
        if err:
            self.report({'ERROR'}, err)
            return {'CANCELLED'}

        base_name = f"{prefix}_Merged"
        tasks = _build_tasks(
            parts_map,
            collections,
            merge_dir,
            base_name,
            ranges,
        )

        addon_dir = os.path.dirname(os.path.dirname(__file__))
        script_path = os.path.join(
            addon_dir,
            'standalone_scripts',
            'ORBXmerger.lua',
        )

        manager = make_orbx_merge_manager(
            tasks,
            octane_exec,
            script_path,
            poll_interval=3.0,
        )
        bpy.app.timers.register(manager, first_interval=0.0)

        self.report({'INFO'}, 'ORBX merging started.')
        return {'FINISHED'}


classes = (
    LMB_OT_merge_selected_tags,
    LMB_OT_merge_all_tags,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
