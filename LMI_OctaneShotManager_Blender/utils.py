import os
import math
from mathutils import Matrix
from functools import wraps
import time
import csv

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
CSV_EXTENSION = 'csv'
ABC_EXTENSION = 'abc'
ORBX_EXTENSION = 'orbx'

# -----------------------------------------------------------------------------
# Directory Helpers
# -----------------------------------------------------------------------------
def ensure_directory(path):
    """
    Create the directory if it doesn't exist.

    :param path: Filesystem path to a directory
    :returns: None
    """
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)


def find_layer_collection(layer_collection, collection):
    """Recursively find the LayerCollection corresponding to a Collection."""
    if layer_collection.collection == collection:
        return layer_collection
    for child in layer_collection.children:
        result = find_layer_collection(child, collection)
        if result:
            return result
    return None

# -----------------------------------------------------------------------------
# Filename Generators
# -----------------------------------------------------------------------------
def generate_export_filename(parts, ext):
    """
    Join non-empty tokens with underscores and append an extension.

    :param parts: List of string tokens
    :param ext: File extension without dot
    :returns: Filename string
    """
    name = '_'.join(str(p) for p in parts if p)
    return f"{name}.{ext}"

# -----------------------------------------------------------------------------
# Prefix Helpers
# -----------------------------------------------------------------------------
def sanitize_token(token):
    """Replace spaces with underscores to keep paths clean."""
    return str(token).replace(' ', '_') if token else ''


def build_scene_shot_prefix(scene_name, shot_name):
    """Return a prefix string like 'Scene-XXX_Shot-YYY'."""
    scene_tok = sanitize_token(scene_name)
    shot_tok = sanitize_token(shot_name)
    parts = []
    if scene_tok:
        parts.append(f"Scene-{scene_tok}")
    if shot_tok:
        parts.append(f"Shot-{shot_tok}")
    return '_'.join(parts)

# -----------------------------------------------------------------------------
# Matrix Builders
# -----------------------------------------------------------------------------
def build_asset_world_matrices():
    """
    Return two correction matrices:
      - asset_mat: +90° rotation on X
      - world_mat: -90° rotation on X

    :returns: (asset_mat, world_mat) as mathutils.Matrix
    """
    asset_mat = Matrix.Rotation(math.radians(90.0), 4, 'X')
    world_mat = Matrix.Rotation(math.radians(-90.0), 4, 'X')
    return asset_mat, world_mat

def flatten_matrices_to_list(matrix_list):
    """
    Convert a list of 4x4 matrices to a list of flat row-major lists (3x4 only).

    :param matrix_list: Iterable of mathutils.Matrix
    :returns: List of flattened rows
    """
    flat = []
    for m in matrix_list:
        # Extract 3 rows and 4 columns
        flat.append([m[i][j] for i in range(3) for j in range(4)])
    return flat

# -----------------------------------------------------------------------------
# Timing Decorator
# -----------------------------------------------------------------------------
def timed(func):
    """
    Decorator to measure and report execution time of functions.

    Usage:
        @timed
        def my_func(...):
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"[TIMED] {func.__name__} took {elapsed:.4f}s")
        return result
    return wrapper

# -----------------------------------------------------------------------------
# CSV Writer Utility
# -----------------------------------------------------------------------------
def write_csv_groups(groups, base_dir, subfolder, overwrite, frame_suffix=None, pc_suffix=False, prefix_parts=None):
    """
    Write instance transform groups to CSV files.

    :param groups: Dict[str, List[List[float]]] mapping object names to rows
    :param base_dir: Root directory path
    :param subfolder: Subdirectory name (or None)
    :param overwrite: Bool, whether to overwrite existing files
    :param frame_suffix: Optional int to append as frame suffix
    :param pc_suffix: Bool, whether to append '_PC' to object names
    :param prefix_parts: Optional list of tokens to prepend to filenames
    :returns: None
    """
    out_dir = os.path.join(base_dir, subfolder) if subfolder else base_dir
    ensure_directory(out_dir)

    header = [f"M{r}{c}" for r in range(3) for c in range(4)] + ['ID']
    for obj_name, rows in groups.items():
        # Build base token (with PC suffix if requested)
        base_token = f"{obj_name}_PC" if pc_suffix else obj_name
        # Assemble tokens for filename
        parts = []
        if prefix_parts:
            parts.extend(prefix_parts)
        parts.append(base_token)
        if frame_suffix is not None:
            parts.append(str(frame_suffix))
        filename = generate_export_filename(parts, CSV_EXTENSION)
        filepath = os.path.join(out_dir, filename)
        if os.path.exists(filepath) and not overwrite:
            continue
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            for idx, row in enumerate(rows):
                writer.writerow(row + [idx])

# -----------------------------------------------------------------------------
# Frame Range Parser
# -----------------------------------------------------------------------------
def parse_frame_range(frame_range_str):
    """
    Parse a string of frames/ranges into a sorted list of unique frame ints.

    Supported formats:
      - Single frames: "2,5,10"
      - Ranges: "1-5"
      - Combined: "1,3-5,10"

    :param frame_range_str: String input
    :returns: Sorted list of frame numbers (ints)
    """
    frames = set()
    tokens = frame_range_str.split(',') if frame_range_str else []
    for tok in tokens:
        tok = tok.strip()
        if '-' in tok:
            parts = tok.split('-', 1)
            try:
                start, end = int(parts[0]), int(parts[1])
            except ValueError:
                continue
            step = 1 if start <= end else -1
            frames.update(range(start, end + step, step))
        else:
            try:
                frames.add(int(tok))
            except ValueError:
                continue
    return sorted(frames)


def iter_chunk_ranges(start, end, size):
    """Yield inclusive frame range tuples split by ``size``."""
    size = max(1, int(size))
    for s in range(int(start), int(end) + 1, size):
        e = min(s + size - 1, int(end))
        yield s, e


def wait_for_file(path, timeout=30.0, step=0.1):
    """Return True when ``path`` exists or ``timeout`` seconds elapse."""
    start = time.perf_counter()
    while (time.perf_counter() - start) < timeout:
        if os.path.exists(path):
            return True
        time.sleep(step)
    return os.path.exists(path)


