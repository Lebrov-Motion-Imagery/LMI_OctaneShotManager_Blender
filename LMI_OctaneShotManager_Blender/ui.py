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
        row.label(text="Name your scene, shot and select path for Shot Manager:", icon='GREASEPENCIL')

        if p.show_naming_settings:
            name_box = layout.box()
            name_box.label(text="Decide how to name your scene:")
            row = name_box.row(align=True)
            sub = row.row(align=True)
            sub.enabled = bool(bpy.data.filepath)
            sub.prop_enum(p, 'scene_name_source', 'FILE', text='Blender File')
            row.prop_enum(p, 'scene_name_source', 'SCENE', text='Scene Name')
            row.prop_enum(p, 'scene_name_source', 'MANUAL', text='Manual')
            if p.scene_name_source == 'MANUAL':
                name_box.prop(p, 'scene_name_manual')

            name_box.label(text="Decide how to name your shot:")
            row = name_box.row(align=True)
            row.prop_enum(p, 'shot_name_source', 'OBJECT', text='Selected Camera')
            row.prop_enum(p, 'shot_name_source', 'MANUAL', text='Manual')
            if p.shot_name_source == 'MANUAL':
                name_box.prop(p, 'shot_name_manual')
            elif p.shot_name_source == 'OBJECT':
                name_box.prop(p, 'shot_object_source')

            path_box = layout.box()
            path_box.label(text="Path selection:")
            path_box.prop(p, 'root_output_dir')
            layout.separator()

        # TAGs Workflow dropdown
        row = layout.row()
        arrow = 'TRIA_DOWN' if p.show_tags_workflow else 'TRIA_RIGHT'
        row.prop(p, 'show_tags_workflow', text="", icon=arrow, emboss=False)
        row.label(text="LMI TAGs Workflow", icon='BOOKMARKS')

        if p.show_tags_workflow:
            tag_box = layout.box()
            tag_box.label(text="Select in outliner collections that should be TAGed and click '+' button")
            row = tag_box.row()
            row.template_list('LMB_UL_tag_collections', '', p, 'tag_collections', p, 'tag_collections_index')
            col = row.column(align=True)
            col.operator('lmb.tag_collection_add', icon='ADD', text='')
            col.operator('lmb.tag_collection_remove', icon='REMOVE', text='')

            tag_box.label(text="Frame Range and Chunk:")
            row = tag_box.row(align=True)
            row.prop(p, 'tag_frame_start')
            row.prop(p, 'tag_frame_end')

            row = tag_box.row(align=True)
            row.prop(p, 'tag_use_chunks')
            if p.tag_use_chunks:
                row.prop(p, 'tag_chunk_size', text='Chunk')
            tag_box.operator('lmb.cycle_tag_collection', text='Cycle Collection')
            tag_box.prop(p, 'overwrite_orbx')
            tag_box.operator('lmb.export_orbx_tags', text="Export all Tags to a 'Per Tag' ORBX", icon='EXPORT')
            tag_box.operator('lmb.export_orbx_selected_tags', text="Export selected Tags to an ORBX", icon='EXPORT')
            tag_box.operator('lmb.export_orbx_direct_merged', text="Export directly to a Merged ORBX", icon='EXPORT')
            merge_box = tag_box.box()
            merge_box.prop(p, 'octane_standalone_path')
            merge_box.operator('lmb.merge_selected_tags', text='Merge selected Tags', icon='EXPORT')
            merge_box.operator('lmb.merge_all_tags', text='Merge all Tags', icon='EXPORT')
            layout.separator()

        # Manual ORBX Merge
        row = layout.row()
        arrow = 'TRIA_DOWN' if p.show_manual_orbx_merge else 'TRIA_RIGHT'
        row.prop(p, 'show_manual_orbx_merge', text="", icon=arrow, emboss=False)
        row.label(text="Manual ORBX Merge", icon='SEQ_STRIP_META')
        if p.show_manual_orbx_merge:
            box = layout.box()
            box.prop(p, 'manual_merge_save_dir')
            box.prop(p, 'manual_merge_scene_name')
            box.prop(p, 'manual_merge_overwrite')
            box.prop(p, 'manual_merge_destination')
            row2 = box.row()
            row2.template_list('LMB_UL_manual_merge_sources', '', p, 'manual_merge_sources', p, 'manual_merge_sources_index')
            col = row2.column(align=True)
            col.operator('lmb.manual_merge_source_add', icon='ADD', text='')
            col.operator('lmb.manual_merge_source_remove', icon='REMOVE', text='')
            box.operator('lmb.manual_orbx_merge', text='Merge ORBX', icon='EXPORT')
            layout.separator()
        # PointCloud Baker dropdown
        row = layout.row()
        arrow = 'TRIA_DOWN' if p.show_pointcloud_baker else 'TRIA_RIGHT'
        row.prop(p, 'show_pointcloud_baker', text="", icon=arrow, emboss=False)
        pc_ico = icon_collections['main']["pointcloud_bake"].icon_id
        row.label(text="LMI PointCloud Baker", icon_value=pc_ico)

        if p.show_pointcloud_baker:
            # CSV Settings
            csv_box = layout.box()
            csv_box.label(text="CSV Settings", icon='TEXT')
            csv_box.prop(p, 'csv_src_type')
            if p.csv_src_type == 'OBJECT':
                csv_box.prop(p, 'csv_object_source')
            else:
                csv_box.prop(p, 'csv_collection_source')
            csv_box.prop(p, 'overwrite_csv')
            csv_box.prop(p, 'multi_frame_export')
            if p.multi_frame_export:
                csv_box.prop(p, 'frame_range')
            csv_box.operator('lmb.export_csv', text="Export CSV", icon='EXPORT')
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
                box.prop(p, 'overwrite_abc')
                box.operator('lmb.export_abc', text="Export Alembic", icon='EXPORT')
