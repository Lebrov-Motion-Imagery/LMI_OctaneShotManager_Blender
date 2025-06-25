import os
import bpy
from bpy.types import Operator
from bpy.props import StringProperty, BoolProperty, PointerProperty, EnumProperty

from ..properties import OctanePointCloudProperties
from ..utils import (
    ensure_directory,
    build_asset_world_matrices,
    generate_export_filename,
    CSV_EXTENSION,
)


class LMB_OT_export_csv(Operator):
    """Export scattered instances to per-object CSV files."""
    bl_idname = "lmb.export_csv"
    bl_label = "Export Pointcloud CSV"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.otpc_props  # type: OctanePointCloudProperties
        depsgraph = context.evaluated_depsgraph_get()

        # Determine sources
        if props.csv_src_type == 'OBJECT':
            instancers = [props.csv_object_source] if props.csv_object_source else []
            root_folder = None
        else:
            instancers = list(props.csv_collection_source.objects) if props.csv_collection_source else []
            root_folder = f"{props.csv_collection_source.name}_CSVs"

        if not instancers:
            self.report({'ERROR'}, "No CSV instancer sources defined.")
            return {'CANCELLED'}

        # Prepare output directory
        base_dir = bpy.path.abspath(props.csv_output_dir)
        ensure_directory(base_dir)

        # Prepare transform matrices
        asset_mat, world_mat = build_asset_world_matrices()

        # Iterate instancers
        for obj in instancers:
            # Collect instance transforms via depsgraph
            eval_obj = obj.evaluated_get(depsgraph)
            groups = {}
            for inst in depsgraph.object_instances:
                if not inst.is_instance or inst.parent != eval_obj:
                    continue
                name = inst.instance_object.name
                m = world_mat @ (inst.matrix_world @ asset_mat)
                flat = [m[i][j] for i in range(3) for j in range(4)]
                groups.setdefault(name, []).append(flat)

            # Write CSVs
            subfolder = os.path.join(root_folder, obj.name) if root_folder else obj.name
            write_csv_groups(groups, base_dir, subfolder, props.overwrite_csv)

        self.report({'INFO'}, "CSV export completed.")
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
