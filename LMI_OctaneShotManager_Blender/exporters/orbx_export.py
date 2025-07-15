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
    """Export all TAGged collections to ORBX files."""
    bl_idname = "lmb.export_tags_orbx"
    bl_label = "Export All TAGs to ORBX"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.otpc_props  # type: OctanePointCloudProperties

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

        if not props.tag_collections:
            self.report({'INFO'}, "No TAG collections defined.")
            return {'CANCELLED'}

        base_root = bpy.path.abspath(props.root_output_dir)
        scene_name = resolve_scene_name()
        shot_name = resolve_shot_name()
        prefix = build_scene_shot_prefix(scene_name, shot_name)
        base_dir = os.path.join(base_root, "Shot_Manager", "TAGs", prefix)
        ensure_directory(base_dir)

        frame_start = props.tag_frame_start
        frame_end = props.tag_frame_end

        ranges = []
        if props.tag_use_chunks and props.tag_chunk_size > 0:
            current = frame_start
            while current <= frame_end:
                end_chunk = min(current + props.tag_chunk_size - 1, frame_end)
                ranges.append((current, end_chunk))
                current = end_chunk + 1
        else:
            ranges.append((frame_start, frame_end))

        for item in props.tag_collections:
            coll = item.collection
            if coll is None:
                continue
            objects = list(coll.all_objects)
            if not objects:
                continue

            for r_start, r_end in ranges:
                parts = [prefix, coll.name, f"{r_start}-{r_end}"]
                filename = generate_export_filename(parts, ORBX_EXTENSION)
                filepath = os.path.join(base_dir, filename)

                bpy.ops.object.select_all(action='DESELECT')
                for obj in objects:
                    obj.select_set(True)
                context.view_layer.objects.active = objects[0]

                bpy.ops.export.orbx(
                    filepath=filepath,
                    check_existing=False,
                    frame_start=r_start,
                    frame_end=r_end,
                )

        self.report({'INFO'}, "ORBX export completed.")
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
