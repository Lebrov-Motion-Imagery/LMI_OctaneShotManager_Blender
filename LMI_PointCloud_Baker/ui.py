import bpy
from bpy.types import Panel

class POINTCLOUD_PT_panel(Panel):
    bl_label = "LMI PointCloud Baker"
    bl_idname = "POINTCLOUD_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LMI PointCloud Baker'

    def draw(self, context):
        layout = self.layout
        p = context.scene.otpc_props

        # Naming
        layout.label(text="Naming", icon='GREASEPENCIL')
        layout.prop(p, 'scene_name')
        layout.prop(p, 'shot_name')
        layout.separator()

        # CSV Settings
        layout.label(text="CSV Settings", icon='TEXT')
        layout.prop(p, 'csv_src_type')
        if p.csv_src_type == 'OBJECT':
            layout.prop(p, 'csv_object_source')
        else:
            layout.prop(p, 'csv_collection_source')
        layout.prop(p, 'csv_output_dir')
        layout.prop(p, 'overwrite_csv')
        layout.operator('lmb.export_csv', text="Export CSV", icon='EXPORT')
        layout.separator()

        # Alembic Settings
        layout.prop(p, 'export_abc')
        if p.export_abc:
            box = layout.box()
            box.label(text="Alembic Settings", icon='MESH_DATA')
            box.prop(p, 'abc_src_type')
            if p.abc_src_type == 'OBJECT':
                box.prop(p, 'abc_object_source')
            else:
                box.prop(p, 'abc_collection_source')
            box.prop(p, 'abc_output_dir')
            box.prop(p, 'overwrite_abc')
            box.operator('lmb.export_abc', text="Export Alembic", icon='EXPORT')
