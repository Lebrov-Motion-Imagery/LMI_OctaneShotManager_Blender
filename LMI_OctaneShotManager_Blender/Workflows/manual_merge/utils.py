import bpy
import os
from ..TAGs.utils import _ORBX_RE


def parse_orbx_filename(path):
    """Return (base, part_no, start, end) tuple if name matches the ORBX pattern."""
    name = os.path.basename(path)
    m = _ORBX_RE.match(name)
    if not m:
        return None
    return (
        m.group("base"),
        int(m.group("part")),
        int(m.group("start")),
        int(m.group("end")),
    )


def build_manual_merge_tasks(dest_path, source_paths, save_dir, base_name):
    """Build merge tasks for :func:`make_orbx_merge_manager`.

    Parameters
    ----------
    dest_path : str
        Path to the destination ORBX file used for all merges.
    source_paths : list[str]
        List of ORBX files to merge with the destination.
    save_dir : str
        Directory where merged ORBX files will be saved.
    base_name : str
        Base name for the output files.
    """
    all_paths = [dest_path] + list(source_paths)
    resolved = []
    for p in all_paths:
        abspath = os.path.abspath(bpy.path.abspath(p)) if hasattr(bpy, 'path') else os.path.abspath(p)
        if not os.path.isfile(abspath):
            raise FileNotFoundError(abspath)
        resolved.append(abspath)
    dest_abspath = resolved[0]
    src_abspaths = resolved[1:]

    chunk_sizes = set()
    groups = {}

    info = parse_orbx_filename(dest_abspath)
    if info:
        chunk_sizes.add(info[3] - info[2] + 1)

    for path in src_abspaths:
        info = parse_orbx_filename(path)
        if info:
            start, end = info[2], info[3]
            chunk_sizes.add(end - start + 1)
            groups.setdefault((start, end), []).append(path)
        else:
            groups.setdefault(None, []).append(path)

    if len(chunk_sizes) > 1:
        raise ValueError("All ORBX files must use the same chunk size")

    tasks = []
    generic = groups.get(None, [])
    ranges = sorted(k for k in groups.keys() if k is not None)

    if not ranges:
        save_path = os.path.join(save_dir, f"{base_name}.orbx")
        tasks.append([save_path, dest_abspath] + generic)
        return tasks

    for part_no, (start, end) in enumerate(ranges, 1):
        name = f"{base_name}_pt{part_no}_{start:03d}-{end:03d}.orbx"
        save_path = os.path.join(save_dir, name)
        files = groups[(start, end)]
        task = [save_path, dest_abspath] + generic + files
        tasks.append(task)

    return tasks
