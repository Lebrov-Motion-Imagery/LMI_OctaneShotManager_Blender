import os
import bpy
from bpy.types import Operator

from ..properties import OctanePointCloudProperties
from ..utils import (
    ensure_directory,
    generate_export_filename,
    build_scene_shot_prefix,
    find_layer_collection,
    ORBX_EXTENSION,
)


class LMB_OT_export_orbx_tags(Operator):
    """Export tagged collections to ORBX files."""
    bl_idname = "lmb.export_orbx_tags"
    bl_label = "Export All Tags to ORBX"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.otpc_props  # type: OctanePointCloudProperties
        scene = context.scene

        collections = [item.collection for item in props.tag_collections if item.collection]
        if not collections:
            self.report({'ERROR'}, "No tagged collections defined.")
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

        root_layer = context.view_layer.layer_collection

        saved_states = {}

        def store_states(layer_coll):
            for lc in layer_coll.children:
                saved_states[lc] = lc.exclude
                store_states(lc)

        def set_all(layer_coll, state):
            for lc in layer_coll.children:
                set_all(lc, state)
                lc.exclude = state

        store_states(root_layer)

        def export_range(coll, layer, start, end):
            set_all(root_layer, True)
            layer.exclude = False
            range_str = f"{start}-{end}"
            filename = generate_export_filename([prefix, coll.name, range_str], ORBX_EXTENSION)
            filepath = os.path.join(base_dir, filename)
            if os.path.exists(filepath) and not props.overwrite_orbx:
                return
            scene.render.engine = 'octane'
            bpy.ops.export.orbx(
                'EXEC_DEFAULT',
                filepath=filepath,
                check_existing=True,
                filename=os.path.basename(filepath),
                frame_start=start,
                frame_end=end,
                frame_subframe=0.0,
                filter_glob="*.orbx",
            )
            self.report({'INFO'}, f"Exported ORBX: {filename}")

        for coll in collections:
            layer = find_layer_collection(root_layer, coll)
            if not layer:
                continue
            if props.tag_use_chunking:
                start = props.tag_frame_start
                while start <= props.tag_frame_end:
                    end = min(start + props.tag_chunk_size - 1, props.tag_frame_end)
                    export_range(coll, layer, start, end)
                    start = end + 1
            else:
                export_range(coll, layer, props.tag_frame_start, props.tag_frame_end)

        for lc, state in saved_states.items():
            lc.exclude = state

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
