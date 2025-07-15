import os
import bpy
from bpy.types import Operator

from ..properties import OctanePointCloudProperties
from ..utils import (
    ensure_directory,
    build_scene_shot_prefix,
    find_layer_collection,
    generate_export_filename,
    chunk_frame_ranges,
    ORBX_EXTENSION,
)


class LMB_OT_export_orbx_tags(Operator):
    """Export each tagged collection as ORBX files."""
    bl_idname = "lmb.export_orbx_tags"
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

        scene_name = resolve_scene_name()
        shot_name = resolve_shot_name()

        # Ensure the export root is an absolute path
        base_root = os.path.abspath(bpy.path.abspath(props.root_output_dir))
        prefix = build_scene_shot_prefix(scene_name, shot_name)
        base_dir = os.path.join(base_root, "Shot_Manager", "TAGs", prefix)
        ensure_directory(base_dir)

        frame_start = props.tags_frame_start
        frame_end = props.tags_frame_end
        ranges = list(chunk_frame_ranges(frame_start, frame_end, props.tags_chunk_size if props.tags_use_chunking else (frame_end - frame_start + 1)))

        bpy.context.scene.render.engine = 'octane'

        root_layer = context.view_layer.layer_collection

        def walk_layers(layer, lst):
            lst.append(layer)
            for ch in layer.children:
                walk_layers(ch, lst)

        all_layers = []
        walk_layers(root_layer, all_layers)
        original_states = {lc: lc.exclude for lc in all_layers}

        def set_all(state):
            for lc in all_layers:
                lc.exclude = state

        def unhide_path(layer_coll):
            if layer_coll is None:
                return
            layer_coll.exclude = False
            parent = getattr(layer_coll, "parent", None)
            if parent:
                unhide_path(parent)

        def unhide_children(layer_coll):
            layer_coll.exclude = False
            for ch in layer_coll.children:
                unhide_children(ch)

        exported = 0
        for item in props.tag_collections:
            coll = item.collection
            if not coll:
                continue
            target_layer = find_layer_collection(root_layer, coll)
            if not target_layer:
                continue

            set_all(True)
            unhide_path(target_layer)
            unhide_children(target_layer)

            base_name = f"{prefix}_{coll.name}"
            for start, end in ranges:
                filename = generate_export_filename([base_name, f"{start}-{end}"], ORBX_EXTENSION)
                filepath = os.path.abspath(os.path.join(base_dir, filename))
                result = bpy.ops.export.orbx(
                    'EXEC_DEFAULT',
                    filepath=filepath,
                    check_existing=True,
                    filename=os.path.basename(filepath),
                    frame_start=start,
                    frame_end=end,
                    frame_subframe=0.0,
                    filter_glob="*.orbx"
                )
                print(f"ORBX export finished: {result} → {filepath}")
                exported += 1

        for lc, val in original_states.items():
            lc.exclude = val

        self.report({'INFO'}, f"Exported {exported} ORBX files.")
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
