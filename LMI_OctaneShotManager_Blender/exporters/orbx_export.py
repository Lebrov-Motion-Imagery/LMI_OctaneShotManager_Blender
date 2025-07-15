import os
import bpy
from bpy.types import Operator

from ..properties import OctanePointCloudProperties
from ..utils import (
    ensure_directory,
    generate_export_filename,
    build_scene_shot_prefix,
    ORBX_EXTENSION,
)


class LMB_OT_export_tags_orbx(Operator):
    """Export tagged collections to ORBX files, optionally in chunks."""
    bl_idname = "lmb.export_tags_orbx"
    bl_label = "Export All Tags to ORBX"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.otpc_props  # type: OctanePointCloudProperties

        if not props.tag_collections:
            self.report({'ERROR'}, "No TAG collections defined.")
            return {'CANCELLED'}

        def resolve_scene_name():
            if props.scene_name_source == 'FILE':
                filepath = bpy.data.filepath
                return os.path.splitext(os.path.basename(filepath))[0] if filepath else ""
            if props.scene_name_source == 'SCENE':
                return context.scene.name
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

        frame_start = props.tag_frame_start
        frame_end = props.tag_frame_end
        use_chunks = props.tag_use_chunks
        chunk = max(1, props.tag_chunk_size)

        for item in props.tag_collections:
            coll = item.collection
            if not coll:
                continue
            objects = list(coll.all_objects)
            if not objects:
                continue

            # Select only objects of this collection
            for obj in bpy.data.objects:
                obj.select_set(False)
            for obj in objects:
                obj.select_set(True)
            context.view_layer.objects.active = objects[0]

            if use_chunks:
                cur = frame_start
                while cur <= frame_end:
                    end_chunk = min(cur + chunk - 1, frame_end)
                    range_str = f"{cur}-{end_chunk}"
                    filename = generate_export_filename([
                        prefix,
                        coll.name,
                        range_str
                    ], ORBX_EXTENSION)
                    filepath = os.path.join(base_dir, filename)
                    bpy.ops.export.orbx(
                        filepath=filepath,
                        check_existing=True,
                        frame_start=cur,
                        frame_end=end_chunk,
                    )
                    cur = end_chunk + 1
            else:
                range_str = f"{frame_start}-{frame_end}"
                filename = generate_export_filename([
                    prefix,
                    coll.name,
                    range_str
                ], ORBX_EXTENSION)
                filepath = os.path.join(base_dir, filename)
                bpy.ops.export.orbx(
                    filepath=filepath,
                    check_existing=True,
                    frame_start=frame_start,
                    frame_end=frame_end,
                )

        self.report({'INFO'}, "ORBX TAGs export completed.")
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
