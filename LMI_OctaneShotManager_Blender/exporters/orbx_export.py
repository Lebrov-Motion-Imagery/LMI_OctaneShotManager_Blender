import os
import bpy
from bpy.types import Operator

from ..properties import OctanePointCloudProperties
from ..utils import (
    ensure_directory,
    build_scene_shot_prefix,
)
from ..Workflows.TAGs import utils as tag_utils


# -----------------------------------------------------------------------------
# Helper functions
# -----------------------------------------------------------------------------

def chunk_frame_ranges(start: int, end: int, step: int):
    """Return a list of (start, end) ranges split by step size."""
    ranges = []
    cur = start
    while cur <= end:
        chunk_end = min(cur + step - 1, end)
        ranges.append((cur, chunk_end))
        cur = chunk_end + 1
    return ranges


def export_orbx_chunk(frame_start: int, frame_end: int, export_dir: str, base_name: str):
    """Trigger Octane ORBX export for the given frame range."""
    scene = bpy.context.scene
    scene.render.engine = 'octane'
    scene.frame_start = frame_start
    scene.frame_end = frame_end

    name = f"{base_name}_{frame_start:03d}-{frame_end:03d}.orbx"
    filepath = os.path.join(export_dir, name)

    bpy.ops.export.orbx(
        'EXEC_DEFAULT',
        filepath=filepath,
        check_existing=False,
        filename=name,
        frame_start=frame_start,
        frame_end=frame_end,
        frame_subframe=0.0,
        filter_glob="*.orbx",
    )

    return filepath


def is_file_created(filepath: str):
    """Return True once the ORBX file appears on disk."""
    return os.path.exists(filepath)


def unsolo_all(context):
    """Reset all collection exclusions."""
    layer = context.view_layer.layer_collection

    def _reset(lc):
        for child in lc.children:
            _reset(child)
            child.exclude = False

    _reset(layer)


def make_export_manager(queue, export_dir, prefix, poll_interval=3.0):
    """Return a timer callback managing sequential ORBX exports."""
    state = {'waiting_for': None}

    def manager():
        context = bpy.context
        if state['waiting_for'] is None:
            if not queue:
                unsolo_all(context)
                print("✅ All TAG exports done.")
                return None

            coll, frm, to = queue.pop(0)
            tag_utils.solo_collection(context, coll)
            base_name = f"{prefix}_{coll.name}"
            fp = export_orbx_chunk(frm, to, export_dir, base_name)
            state['waiting_for'] = fp
            return poll_interval
        else:
            fp = state['waiting_for']
            if is_file_created(fp):
                print(f"✔ Done {os.path.basename(fp)}")
                state['waiting_for'] = None
            else:
                print(f"…waiting for {os.path.basename(fp)}")
            return poll_interval

    return manager


# -----------------------------------------------------------------------------
# Operator
# -----------------------------------------------------------------------------
class LMB_OT_export_tags_orbx(Operator):
    """Export all tagged collections to ORBX files."""

    bl_idname = "lmb.export_tags_orbx"
    bl_label = "Export All Tags to ORBX"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props: OctanePointCloudProperties = context.scene.otpc_props
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

        tagged = tag_utils.get_tagged_collections(scene)
        if not tagged:
            self.report({'INFO'}, "No tagged collections to export.")
            return {'CANCELLED'}

        start_f = props.tag_frame_start
        end_f = props.tag_frame_end
        if start_f > end_f:
            start_f, end_f = end_f, start_f

        if props.tag_use_chunks:
            ranges = chunk_frame_ranges(start_f, end_f, max(1, props.tag_chunk_size))
        else:
            ranges = [(start_f, end_f)]

        scene_name = resolve_scene_name()
        shot_name = resolve_shot_name()

        base_root = bpy.path.abspath(props.root_output_dir)
        prefix = build_scene_shot_prefix(scene_name, shot_name)
        export_dir = os.path.join(base_root, "Shot_Manager", "TAGs", prefix)
        ensure_directory(export_dir)

        queue = [(coll, frm, to) for coll in tagged for (frm, to) in ranges]
        manager = make_export_manager(queue, export_dir, prefix, poll_interval=3.0)
        bpy.app.timers.register(manager, first_interval=0.0)

        self.report({'INFO'}, "ORBX export started.")
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
