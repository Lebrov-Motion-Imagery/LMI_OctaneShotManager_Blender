import bpy
from .icons import icon_collections
from bpy.types import Panel

class POINTCLOUD_PT_panel(Panel):
    bl_label = "LMI Octane Shot Manager"
    bl_idname = "POINTCLOUD_PT_panel"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'LMI Octane Shot Manager'

    def draw_header(self, context):
        """Draw custom SVG icon in the panel header."""
        ico = icon_collections['main']["shot_manager"].icon_id
        self.layout.label(text="", icon_value=ico)

    def draw(self, context):
        layout = self.layout
        p = context.scene.otpc_props

        # Naming Section
        row = layout.row()
        arrow = 'TRIA_DOWN' if p.show_naming_settings else 'TRIA_RIGHT'
        row.prop(p, 'show_naming_settings', text="", icon=arrow, emboss=False)
        row.label(text="Name your scene and shot:", icon='GREASEPENCIL')

        if p.show_naming_settings:
            box = layout.box()
            box.label(text="Decide how to name your scene:")
            row = box.row(align=True)
            sub = row.row(align=True)
            sub.enabled = bool(bpy.data.filepath)
            sub.prop_enum(p, 'scene_name_source', 'FILE', text='Blender File')
            row.prop_enum(p, 'scene_name_source', 'SCENE', text='Scene Name')
            row.prop_enum(p, 'scene_name_source', 'MANUAL', text='Manual')
            if p.scene_name_source == 'MANUAL':
                box.prop(p, 'scene_name_manual')

            box.label(text="Decide how to name your shot:")
            row = box.row(align=True)
            row.prop_enum(p, 'shot_name_source', 'OBJECT', text='Selected Camera')
            row.prop_enum(p, 'shot_name_source', 'MANUAL', text='Manual')
            if p.shot_name_source == 'MANUAL':
                box.prop(p, 'shot_name_manual')
            elif p.shot_name_source == 'OBJECT':
                box.prop(p, 'shot_object_source')
            layout.separator()

        # PointCloud Baker dropdown
        row = layout.row()
        arrow = 'TRIA_DOWN' if p.show_pointcloud_baker else 'TRIA_RIGHT'
        row.prop(p, 'show_pointcloud_baker', text="", icon=arrow, emboss=False)
        pc_ico = icon_collections['main']["pointcloud_bake"].icon_id
        row.label(text="LMI PointCloud Baker", icon_value=pc_ico)

        if p.show_pointcloud_baker:
            # CSV Settings
            layout.label(text="CSV Settings", icon='TEXT')
            layout.prop(p, 'csv_src_type')
            if p.csv_src_type == 'OBJECT':
                layout.prop(p, 'csv_object_source')
            else:
                layout.prop(p, 'csv_collection_source')
            layout.prop(p, 'csv_output_dir')
            layout.prop(p, 'overwrite_csv')
            layout.prop(p, 'multi_frame_export')
            if p.multi_frame_export:
                layout.prop(p, 'frame_range')
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

