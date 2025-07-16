import bpy
import os

# ——— 1. Frame‐range chunking —————————————
def chunk_frame_ranges(start, end, step):
    """
    Split [start…end] into non‐overlapping chunks of size 'step':
    e.g. 0–4, 5–9, …, last chunk may be smaller.
    """
    chunks = []
    cur = start
    while cur <= end:
        chunk_end = min(cur + step - 1, end)
        chunks.append((cur, chunk_end))
        cur = chunk_end + 1
    return chunks


# ——— 2. Export one chunk to ORBX ——————————
def export_orbx_chunk(frame_start, frame_end, export_dir, base_name):
    """
    Sets scene frame range, calls bpy.ops.export.orbx,
    returns the full filepath of the just‐kicked‐off export.
    """
    scene = bpy.context.scene
    scene.frame_start = frame_start
    scene.frame_end   = frame_end

    name     = f"{base_name}_{frame_start:03d}-{frame_end:03d}.orbx"
    filepath = os.path.join(export_dir, name)

    print(f"▶ Export {frame_start}–{frame_end} → {name}")
    bpy.ops.export.orbx(
        'EXEC_DEFAULT',
        filepath=filepath,
        check_existing=False,
        filename=name,
        frame_start=frame_start,
        frame_end=frame_end,
        frame_subframe=0.0,
        filter_glob="*.orbx"
    )

    return filepath


# ——— 3. File‐existence check —————————————
def is_file_created(filepath):
    """Return True once the ORBX file appears on disk."""
    return os.path.exists(filepath)


# ——— 4. Timer‐based manager factory ————————
def make_export_manager(frame_queue, export_dir, base_name, poll_interval=3.0):
    """
    Returns a function suitable for bpy.app.timers.register().
    It will:
      • pop the next chunk,
      • call export_orbx_chunk(),
      • then poll every poll_interval seconds until the file exists,
      • then move on to the next chunk.
    """
    state = {'waiting_for': None}

    def manager():
        # A) If not currently waiting on a file, start next export
        if state['waiting_for'] is None:
            if not frame_queue:
                print("✅ All exports done.")
                return None  # stop the timer

            frm, to = frame_queue.pop(0)
            fp = export_orbx_chunk(frm, to, export_dir, base_name)
            state['waiting_for'] = fp
            return poll_interval

        # B) Otherwise poll for file existence
        else:
            fp = state['waiting_for']
            if is_file_created(fp):
                print(f"✔ Done {os.path.basename(fp)}")
                state['waiting_for'] = None
            else:
                print(f"…waiting for {os.path.basename(fp)}")
            return poll_interval

    return manager


# ——— Setup and kick‐off ————————————————
scene = bpy.context.scene
scene.render.engine = 'octane'

export_dir = '/Users/arseniykolenchenko/Resilio Sync/LMI_Projects/_PROJECTS/LMI/LMI_OTOY_ShowCase/Tests/Animated_Points/Root_v3'
os.makedirs(export_dir, exist_ok=True)

base_name = 'Root_v3'
step       = 5
start_f    = scene.frame_start  # e.g. 0
end_f      = scene.frame_end    # e.g. 20

# Build the queue of (start,end) tuples
frame_queue = chunk_frame_ranges(start_f, end_f, step)

# Make and register the timer callback
export_manager = make_export_manager(frame_queue, export_dir, base_name, poll_interval=3.0)
bpy.app.timers.register(export_manager, first_interval=0.0)
