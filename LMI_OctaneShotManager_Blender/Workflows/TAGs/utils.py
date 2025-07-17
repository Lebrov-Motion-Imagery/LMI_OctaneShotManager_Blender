import bpy
import os
import re
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


def calculate_part_ranges(start, end, chunk):
    """Return list of (part_no, start, end) tuples for the given range."""
    ranges = []
    cur = start
    part_no = 1
    while cur <= end:
        chunk_end = min(cur + chunk - 1, end)
        ranges.append((part_no, cur, chunk_end))
        cur = chunk_end + 1
        part_no += 1
    return ranges


_ORBX_RE = re.compile(r"^(?P<base>.+)_pt(?P<part>\d+)_(?P<start>\d+)-(?P<end>\d+)\.orbx$", re.I)


def parse_orbx_sequence(export_dir, base_name):
    """Parse existing ORBX files and return parts and chunk sizes."""
    parts = []
    chunk_sizes = set()
    if not os.path.isdir(export_dir):
        return parts, chunk_sizes

    for fname in os.listdir(export_dir):
        m = _ORBX_RE.match(fname)
        if not m:
            continue
        if not fname.startswith(base_name + "_"):
            continue
        part_no = int(m.group("part"))
        start_f = int(m.group("start"))
        end_f = int(m.group("end"))
        parts.append((part_no, start_f, end_f))
        chunk_sizes.add(end_f - start_f + 1)

    parts.sort(key=lambda x: x[0])
    return parts, chunk_sizes


def filter_missing_parts(parts, export_dir, base_name, overwrite, chunk_size=None):
    """Return subset of parts that need exporting with numbering adjusted.

    When ``overwrite`` is ``True`` mismatched existing chunks are deleted so they
    can be replaced. If ``overwrite`` is ``False`` and a chunk differs from what
    is on disk, an error is raised prompting the user to enable overwriting.
    """
    # When chunk_size is ``None`` we skip all chunk detection logic and simply
    # check whether the resulting files exist. This mode is used when the user
    # disables chunking entirely.
    if chunk_size is None:
        results = []
        for part_no, frm, to in parts:
            filename = f"{base_name}_pt{part_no}_{frm:03d}-{to:03d}.orbx"
            filepath = os.path.join(export_dir, filename)
            if os.path.exists(filepath) and not overwrite:
                continue
            results.append((part_no, frm, to))
        return results

    existing_parts, _chunk_sizes = parse_orbx_sequence(export_dir, base_name)

    # Use explicitly requested chunk size if provided, otherwise derive from
    # the supplied part ranges.
    if chunk_size:
        req_chunk = chunk_size
    elif parts:
        req_chunk = max(to - frm + 1 for _, frm, to in parts)
    else:
        req_chunk = 0

    # Determine the prevalent chunk size among existing parts so we don't rely
    # on the last (often shorter) chunk in the sequence.
    exist_chunk = None
    first_frame = None
    last_frame = None
    if existing_parts:
        counts = {}
        for _, start_f, end_f in existing_parts:
            c = end_f - start_f + 1
            counts[c] = counts.get(c, 0) + 1
        exist_chunk = max(sorted(counts.items()), key=lambda kv: kv[1])[0]
        first_frame = min(s for _, s, _ in existing_parts)
        last_frame = max(e for _, _, e in existing_parts)

    if exist_chunk and req_chunk and exist_chunk != req_chunk:
        raise ValueError(
            "Existing ORBX sequence uses chunk size "
            f"{exist_chunk}, but requested {req_chunk}. "
            f"Use chunk size {exist_chunk}."
        )

    if overwrite and existing_parts:
        req_start = parts[0][1] if parts else None
        req_end = parts[-1][2] if parts else None
        if req_start is not None and req_start != first_frame:
            raise ValueError(
                "Requested start frame does not match existing sequence. "
                f"Use {first_frame} as start frame."
            )
        if req_end is not None and req_end < last_frame:
            raise ValueError(
                "Requested end frame is before existing sequence end. "
                f"Use {last_frame} or later as end frame."
            )

    chunk = exist_chunk or req_chunk
    base_start = (
        min((s for _, s, _ in existing_parts), default=parts[0][1] if parts else 1)
        if chunk
        else (parts[0][1] if parts else 1)
    )

    existing_map = {pn: (s, e) for pn, s, e in existing_parts}

    def delete_mismatched(pn, s, e):
        name = f"{base_name}_pt{pn}_{s:03d}-{e:03d}.orbx"
        path = os.path.join(export_dir, name)
        try:
            os.remove(path)
        except FileNotFoundError:
            pass

    results = []
    for _, frm, to in parts:
        part_no = ((frm - base_start) // chunk) + 1 if chunk else 1
        expected_start = base_start + (part_no - 1) * chunk
        expected_end = expected_start + chunk - 1
        if frm != expected_start:
            raise ValueError(
                f"Frame range {frm}-{to} does not align with chunk size {chunk}. "
                f"Expected start {expected_start}."
            )
        if to != min(expected_end, to):
            raise ValueError(
                f"Frame range {frm}-{to} does not align with chunk size {chunk}."
            )

        existing = existing_map.get(part_no)
        if existing and existing != (frm, to):
            if overwrite:
                delete_mismatched(part_no, *existing)
            else:
                raise ValueError(
                    f"Chunk {part_no} on disk is {existing[0]}-{existing[1]}, "
                    f"but expected {frm}-{to}. Enable 'Overwrite ORBX' to "
                    "replace it."
                )

        filename = f"{base_name}_pt{part_no}_{frm:03d}-{to:03d}.orbx"
        filepath = os.path.join(export_dir, filename)
        if os.path.exists(filepath) and not overwrite:
            continue
        results.append((part_no, frm, to))

    return results


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


def make_compound_orbx_export_manager(task_queue, export_dir, base_name, overwrite, poll_interval=3.0):
    """Create a timer callback to export ORBX chunks without soloing."""
    state = {'waiting_for': None}

    def manager():
        if state['waiting_for'] is None:
            while task_queue:
                part_no, frm, to = task_queue.pop(0)
                filename = f"{base_name}_pt{part_no}_{frm:03d}-{to:03d}.orbx"
                filepath = os.path.join(export_dir, filename)
                if os.path.exists(filepath) and not overwrite:
                    print(f"Skipping existing {filename}")
                    continue
                fp = export_orbx_chunk(part_no, frm, to, export_dir, base_name)
                state['waiting_for'] = fp
                return poll_interval

            print("✅ All exports done.")
            return None
        else:
            fp = state['waiting_for']
            name = os.path.basename(fp)
            if is_file_created(fp):
                print(f"✔ Done {name}")
                state['waiting_for'] = None
            else:
                print(f"…waiting for {name}")
            return poll_interval

    return manager
