import os
import bpy
from bpy.types import Operator
from typing import TYPE_CHECKING
from ..utils import (
    ensure_directory,
    build_asset_world_matrices,
    write_csv_groups,
    build_scene_shot_prefix,
    parse_frame_range,
)

if TYPE_CHECKING:  # pragma: no cover - for type hints only
    from ..properties import OctanePointCloudProperties  # noqa: F401


class LMB_OT_export_csv(Operator):
    """Export scattered instances to per-object CSV files, optionally over a frame sequence."""
    bl_idname = "lmb.export_csv"
    bl_label = "Export Pointcloud CSV"
    bl_description = "Export selected instancers to CSV files"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.otpc_props  # type: OctanePointCloudProperties
        depsgraph = context.evaluated_depsgraph_get()
        scene = context.scene

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

        # Determine frames to export
        if props.multi_frame_export and props.frame_range:
            frames = parse_frame_range(props.frame_range)
        else:
            frames = [scene.frame_current]

        # Determine sources
        if props.csv_src_type == 'OBJECT':
            instancers = [props.csv_object_source] if props.csv_object_source else []
            root_folder = None
        else:
            instancers = list(props.csv_collection_source.objects) if props.csv_collection_source else []
            root_folder = f"{props.csv_collection_source.name}_CSVs"

        if not instancers:
            self.report({'ERROR'}, "[ShotManager] No CSV instancer sources defined.")
            return {'CANCELLED'}

        scene_name = resolve_scene_name()
        shot_name = resolve_shot_name()

        # Prepare output directory hierarchy
        base_root = bpy.path.abspath(props.root_output_dir)
        prefix = build_scene_shot_prefix(scene_name, shot_name)
        base_dir = os.path.join(base_root, "Shot_Manager", "CSVs", prefix)
        ensure_directory(base_dir)

        # Prepare transform matrices
        asset_mat, world_mat = build_asset_world_matrices()

        # Iterate through frames and instancers
        for frame in frames:
            scene.frame_set(frame)
            for obj in instancers:
                eval_obj = obj.evaluated_get(depsgraph)
                groups = {}

                # Collect instance transforms at this frame
                for inst in depsgraph.object_instances:
                    if not inst.is_instance or inst.parent != eval_obj:
                        continue
                    name = inst.instance_object.name
                    m = world_mat @ (inst.matrix_world @ asset_mat)
                    flat = [m[i][j] for i in range(3) for j in range(4)]
                    groups.setdefault(name, []).append(flat)

                # Write CSVs per object, preserving the _PC suffix without extra dot
                subfolder = os.path.join(root_folder, obj.name) if root_folder else obj.name
                ensure_directory(os.path.join(base_dir, subfolder))
                write_csv_groups(
                    groups,
                    base_dir,
                    subfolder,
                    props.overwrite_csv,
                    frame_suffix=frame,
                    pc_suffix=True,
                    prefix_parts=[prefix]
                )

        self.report({'INFO'}, "[ShotManager] CSV export completed.")
        return {'FINISHED'}


classes = (
    LMB_OT_export_csv,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
