import os
import bpy
from bpy.types import Operator

from ..properties import OctanePointCloudProperties
from ..utils import (
    ensure_directory,
    generate_export_filename,
    build_scene_shot_prefix,
    find_layer_collection,
)


class LMB_OT_export_tags_orbx(Operator):
    """Export all tagged collections to ORBX files in sequence."""

    bl_idname = "lmb.export_tags_orbx"
    bl_label = "Export All TAGs to ORBX"
    bl_options = {'REGISTER', 'UNDO'}

    _queue = None
    _current = None
    _log_file = None
    _log_pos = 0
    _view_layer = None

    # ------------------------------------------------------------------
    # Helper functions
    # ------------------------------------------------------------------
    @classmethod
    def _toggle_layer(cls, layer_coll, state):
        for child in layer_coll.children:
            cls._toggle_layer(child, state)
            child.exclude = state

    @classmethod
    def _solo_collection(cls, collection):
        cls._toggle_layer(cls._view_layer.layer_collection, True)
        layer = find_layer_collection(cls._view_layer.layer_collection, collection)
        if layer:
            layer.exclude = False
        print(f"[DEBUG] soloed collection {collection.name}")

    @classmethod
    def _restore_layers(cls):
        cls._toggle_layer(cls._view_layer.layer_collection, False)
        print("[DEBUG] restored layer visibility")

    @classmethod
    def _open_log(cls):
        """Open Octane server log for monitoring if available."""
        if cls._log_file:
            return
        try:
            cfg_dir = bpy.utils.user_resource('CONFIG')
            log_path = os.path.join(cfg_dir, "OctaneServer.log")
            cls._log_file = open(log_path, 'r', encoding='utf-8')
            cls._log_file.seek(0, os.SEEK_END)
            cls._log_pos = cls._log_file.tell()
            print(f"[DEBUG] monitoring log {log_path}")
        except Exception as exc:
            print(f"[DEBUG] failed to open Octane log: {exc}")
            cls._log_file = None

    @classmethod
    def _read_log(cls):
        if not cls._log_file:
            return []
        cls._log_file.seek(cls._log_pos)
        lines = cls._log_file.readlines()
        cls._log_pos = cls._log_file.tell()
        return [l.strip() for l in lines]

    # ------------------------------------------------------------------
    # Queue processing
    # ------------------------------------------------------------------
    @classmethod
    def _start_next(cls, props):
        if not cls._queue:
            cls._restore_layers()
            if cls._log_file:
                cls._log_file.close()
                cls._log_file = None
            print("TAG ORBX export completed.")
            return None

        coll, filepath, filename, start, end = cls._queue.pop(0)
        cls._solo_collection(coll)
        cls._current = {
            'filepath': filepath,
            'filename': filename,
        }
        print(f"[DEBUG] starting export {filename}")
        bpy.ops.export.orbx(
            filepath=filepath,
            check_existing=not props.overwrite_orbx,
            filename=filename,
            frame_start=start,
            frame_end=end,
            frame_subframe=0,
            filter_glob="*.orbx",
        )
        return 0.5

    @classmethod
    def _process_queue(cls):
        props = bpy.context.scene.otpc_props
        cls._open_log()
        for line in cls._read_log():
            if 'Exporting frame' in line:
                print(line)
            if cls._current and 'Export Success' in line and cls._current['filename'] in line:
                print(f"[DEBUG] finished {cls._current['filename']}")
                cls._current = None

        if cls._current:
            return 0.5

        return cls._start_next(props)

    # ------------------------------------------------------------------
    # Execute
    # ------------------------------------------------------------------
    def _resolve_scene_name(self, context, props):
        if props.scene_name_source == 'FILE':
            filepath = bpy.data.filepath
            return os.path.splitext(os.path.basename(filepath))[0] if filepath else ""
        if props.scene_name_source == 'SCENE':
            return context.scene.name
        return props.scene_name_manual

    def _resolve_shot_name(self, context, props):
        if props.shot_name_source == 'OBJECT':
            obj = props.shot_object_source
            return obj.name if obj else ""
        return props.shot_name_manual

    def execute(self, context):
        props: OctanePointCloudProperties = context.scene.otpc_props
        collections = [item.collection for item in props.tag_collections if item.collection]

        if not collections:
            self.report({'ERROR'}, "No TAG collections defined.")
            return {'CANCELLED'}

        base_root = bpy.path.abspath(props.root_output_dir)
        if not base_root:
            self.report({'ERROR'}, "Output directory not set.")
            return {'CANCELLED'}

        scene_name = self._resolve_scene_name(context, props)
        shot_name = self._resolve_shot_name(context, props)
        prefix = build_scene_shot_prefix(scene_name, shot_name)

        export_dir = os.path.join(base_root, "Shot_Manager", "TAGs", prefix)
        ensure_directory(export_dir)

        frame_start = props.tag_frame_start
        frame_end = props.tag_frame_end

        if props.tag_use_chunks:
            chunk_size = max(props.tag_chunk_size, 1)
            ranges = []
            for start in range(frame_start, frame_end + 1, chunk_size):
                end = min(start + chunk_size - 1, frame_end)
                ranges.append((start, end))
        else:
            ranges = [(frame_start, frame_end)]

        cls = self.__class__
        cls._queue = []
        cls._current = None
        cls._view_layer = context.view_layer

        print(f"[DEBUG] preparing exports for {len(collections)} collections {ranges}")

        for coll in collections:
            for start, end in ranges:
                name_parts = [prefix, coll.name, f"{start}-{end}"]
                filename = generate_export_filename(name_parts, "orbx")
                filepath = os.path.join(export_dir, filename)
                if os.path.exists(filepath) and not props.overwrite_orbx:
                    print(f"[DEBUG] skipping existing {filepath}")
                    continue
                cls._queue.append((coll, filepath, filename, start, end))

        if not cls._queue:
            self.report({'INFO'}, "Nothing to export.")
            return {'CANCELLED'}

        bpy.app.timers.register(cls._process_queue)
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
