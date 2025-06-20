import os
import math
from mathutils import Matrix
from functools import wraps
import time

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
CSV_EXTENSION = 'csv'
ABC_EXTENSION = 'abc'

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
    :returns: Dict mapping object name to list of flattened rows
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
import csv

def write_csv_groups(groups, base_dir, subfolder, overwrite):
    """
    Write instance transform groups to CSV files.

    :param groups: Dict[str, List[List[float]]] mapping object names to rows
    :param base_dir: Root directory path
    :param subfolder: Subdirectory name (or None)
    :param overwrite: Bool, whether to overwrite existing files
    :returns: None
    """
    out_dir = os.path.join(base_dir, subfolder) if subfolder else base_dir
    ensure_directory(out_dir)

    header = [f"M{r}{c}" for r in range(3) for c in range(4)] + ['ID']
    for obj_name, rows in groups.items():
        filename = generate_export_filename([obj_name, 'PC'], CSV_EXTENSION)
        filepath = os.path.join(out_dir, filename)
        if os.path.exists(filepath) and not overwrite:
            continue
        with open(filepath, 'w', newline='') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(header)
            for idx, row in enumerate(rows):
                writer.writerow(row + [idx])
