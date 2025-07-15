import os
import bpy
from bpy.types import Operator

from ..properties import OctanePointCloudProperties
from ..utils import (
    ensure_directory,
    generate_export_filename,
    build_scene_shot_prefix,
    ORBX_EXTENSION,
    iter_chunk_ranges,
    find_layer_collection,
)


class LMB_OT_export_tags_orbx(Operator):
    """Export each tagged collection to ORBX files."""
    bl_idname = "lmb.export_tags_orbx"
    bl_label = "Export All TAGs to ORBX"
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

        if not props.tag_collections:
            self.report({'INFO'}, "No TAG collections defined.")
            return {'CANCELLED'}

        scene_name = resolve_scene_name()
        shot_name = resolve_shot_name()

        base_root = bpy.path.abspath(props.root_output_dir)
        prefix = build_scene_shot_prefix(scene_name, shot_name)
        base_dir = os.path.join(base_root, "Shot_Manager", "TAGs", prefix)
        ensure_directory(base_dir)

        frame_start = props.tag_frame_start
        frame_end = props.tag_frame_end
        ranges = list(iter_chunk_ranges(frame_start, frame_end, props.tag_chunk_size)) if props.tag_use_chunks else [(frame_start, frame_end)]

        # store original exclude states
        root_layer = context.view_layer.layer_collection
        original_states = {}

        def record_state(layer):
            original_states[layer] = layer.exclude
            for c in layer.children:
                record_state(c)
        record_state(root_layer)

        def set_all(layer, state):
            layer.exclude = state
            for c in layer.children:
                set_all(c, state)

        def unexclude_parents(layer):
            if layer is None:
                return
            layer.exclude = False
            unexclude_parents(layer.parent)

        def unexclude_children(layer):
            for c in layer.children:
                c.exclude = False
                unexclude_children(c)

        # ensure octane engine
        scene.render.engine = 'octane'

        for item in props.tag_collections:
            coll = item.collection
            if not coll:
                continue

            layer = find_layer_collection(root_layer, coll)
            if layer is None:
                continue

            for r_start, r_end in ranges:
                # Solo collection
                set_all(root_layer, True)
                unexclude_parents(layer)
                unexclude_children(layer)

                parts = [prefix, coll.name, f"{r_start}-{r_end}"]
                filename = generate_export_filename(parts, ORBX_EXTENSION)
                filepath = os.path.join(base_dir, filename)
                ensure_directory(os.path.dirname(filepath))

                bpy.ops.export.orbx(
                    'EXEC_DEFAULT',
                    filepath=filepath,
                    check_existing=True,
                    filename=os.path.basename(filepath),
                    frame_start=r_start,
                    frame_end=r_end,
                    frame_subframe=0.0,
                    filter_glob="*.orbx",
                )

        # restore states
        for layer, val in original_states.items():
            layer.exclude = val

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
