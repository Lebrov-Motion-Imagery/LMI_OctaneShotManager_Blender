import bpy
import os
from ...utils import find_layer_collection


def get_tagged_collections(scene):
    """Return a list of collections tagged for the TAGs workflow."""
    return [item.collection for item in scene.otpc_props.tag_collections if item.collection]


def _set_exclude_recursive(layer_coll, state):
    for child in layer_coll.children:
        _set_exclude_recursive(child, state)
        child.exclude = state


def _unexclude_recursive(layer_coll):
    layer_coll.exclude = False
    for child in layer_coll.children:
        _unexclude_recursive(child)


def solo_collection(context, collection):
    """Solo the given collection by excluding all others in the view layer."""
    root_layer = context.view_layer.layer_collection
    _set_exclude_recursive(root_layer, True)
    layer = find_layer_collection(root_layer, collection)
    if layer:
        _unexclude_recursive(layer)


def cycle_tag_collections(context):
    """Cycle through tagged collections, soloing each one in sequence."""
    props = context.scene.otpc_props
    collections = get_tagged_collections(context.scene)
    if not collections:
        return None

    props.tag_cycle_index = (props.tag_cycle_index + 1) % len(collections)
    coll = collections[props.tag_cycle_index]

    for item in props.tag_collections:
        item["exclude"] = item.collection == coll

    solo_collection(context, coll)
    return coll


def chunk_frame_ranges(start, end, step):
    """Split [start..end] into sequential chunks of size 'step'."""
    chunks = []
    cur = start
    while cur <= end:
        chunk_end = min(cur + step - 1, end)
        chunks.append((cur, chunk_end))
        cur = chunk_end + 1
    return chunks


def export_orbx_chunk(frame_start, frame_end, export_dir, base_name):
    """Launch ORBX export for a frame chunk and return filepath."""
    scene = bpy.context.scene
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


def is_file_created(filepath):
    """Return True when the file appears on disk."""
    return os.path.exists(filepath)


def make_orbx_export_manager(task_queue, export_dir, prefix, overwrite, poll_interval=3.0):
    """Create a timer callback to sequentially export ORBX chunks."""
    state = {'waiting_for': None, 'current_fp': None}

    def manager():
        if state['waiting_for'] is None:
            while task_queue:
                coll, frm, to = task_queue.pop(0)
                solo_collection(bpy.context, coll)
                base_name = f"{prefix}_{coll.name}"
                filename = f"{base_name}_{frm:03d}-{to:03d}.orbx"
                filepath = os.path.join(export_dir, filename)
                if os.path.exists(filepath) and not overwrite:
                    print(f"Skipping existing {filename}")
                    continue
                fp = export_orbx_chunk(frm, to, export_dir, base_name)
                state['waiting_for'] = fp
                state['current_fp'] = fp
                return poll_interval

            print("✅ All exports done.")
            return None
        else:
            fp = state['waiting_for']
            name = os.path.basename(fp)
            if is_file_created(fp):
                print(f"✔ Done {name}")
                state['waiting_for'] = None
                state['current_fp'] = None
            else:
                print(f"…waiting for {name}")
            return poll_interval

    return manager
