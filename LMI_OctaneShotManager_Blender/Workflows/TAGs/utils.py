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
    """Split ``start``..``end`` range into sequential chunks of ``step`` size."""
    chunks = []
    cur = start
    while cur <= end:
        chunk_end = min(cur + step - 1, end)
        chunks.append((cur, chunk_end))
        cur = chunk_end + 1
    return chunks


def calculate_part_ranges(start, end, chunk):
    """Return ``(part_no, frm, to)`` tuples for the given frame range."""
    parts = []
    part_no = 1
    for frm, to in chunk_frame_ranges(start, end, chunk):
        parts.append((part_no, frm, to))
        part_no += 1
    return parts


def parse_orbx_sequence(export_dir, base_name):
    """Parse existing ORBX files and return part ranges and chunk sizes."""
    import re

    regex = re.compile(rf"^{re.escape(base_name)}_pt(\d+)_(\d+)-(\d+)\.orbx$")
    parts = {}
    sizes = set()
    if not os.path.isdir(export_dir):
        return parts, sizes
    for fname in os.listdir(export_dir):
        match = regex.match(fname)
        if not match:
            continue
        part = int(match.group(1))
        frm = int(match.group(2))
        to = int(match.group(3))
        parts[part] = (frm, to)
        sizes.add(to - frm + 1)
    return parts, sizes


def filter_missing_parts(parts, export_dir, base_name, overwrite):
    """Return only missing parts based on existing files in ``export_dir``."""
    existing_parts, chunk_sizes = parse_orbx_sequence(export_dir, base_name)

    if chunk_sizes and not overwrite:
        requested_size = max(to - frm + 1 for _, frm, to in parts)
        existing_size = max(chunk_sizes)
        if existing_size != requested_size:
            first_part_start = parts[0][1]
            min_existing_start = min(frm for frm, _ in existing_parts.values())
            sugg_start = (
                (first_part_start - min_existing_start) // existing_size
            ) * existing_size + min_existing_start
            sugg_end = sugg_start + existing_size - 1
            raise ValueError(
                f"Existing sequence uses chunk size {existing_size}. "
                f"Try exporting {sugg_start}-{sugg_end} instead."
            )

    missing = []
    for part_no, frm, to in parts:
        filename = f"{base_name}_pt{part_no}_{frm:03d}-{to:03d}.orbx"
        filepath = os.path.join(export_dir, filename)
        if overwrite or not os.path.exists(filepath):
            missing.append((part_no, frm, to))
    return missing


def export_orbx_chunk(part_no, frame_start, frame_end, export_dir, base_name):
    """Launch ORBX export for a frame chunk and return filepath."""
    scene = bpy.context.scene
    scene.frame_start = frame_start
    scene.frame_end = frame_end

    name = f"{base_name}_pt{part_no}_{frame_start:03d}-{frame_end:03d}.orbx"
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
                coll, part_no, frm, to = task_queue.pop(0)
                solo_collection(bpy.context, coll)
                base_name = f"{prefix}_{coll.name}"
                filename = f"{base_name}_pt{part_no}_{frm:03d}-{to:03d}.orbx"
                filepath = os.path.join(export_dir, filename)
                if os.path.exists(filepath) and not overwrite:
                    print(f"Skipping existing {filename}")
                    continue
                fp = export_orbx_chunk(part_no, frm, to, export_dir, base_name)
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
