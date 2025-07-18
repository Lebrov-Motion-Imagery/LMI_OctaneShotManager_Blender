import bpy
from bpy.types import PropertyGroup, Operator, UIList
from bpy.props import StringProperty


class ManualMergeSourceItem(PropertyGroup):
    path: StringProperty(name="Source ORBX", subtype='FILE_PATH')


class LMB_UL_manual_merge_sources(UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        layout.prop(item, "path", text="", emboss=False)


class LMB_OT_manual_merge_source_add(Operator):
    bl_idname = "lmb.manual_merge_source_add"
    bl_label = "Add ORBX Source"
    bl_description = "Add an ORBX file to merge"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype='FILE_PATH')

    def execute(self, context):
        props = context.scene.otpc_props
        item = props.manual_merge_sources.add()
        item.path = self.filepath
        props.manual_merge_sources_index = len(props.manual_merge_sources) - 1
        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}


class LMB_OT_manual_merge_source_remove(Operator):
    bl_idname = "lmb.manual_merge_source_remove"
    bl_label = "Remove ORBX Source"
    bl_description = "Remove the selected ORBX source file"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.otpc_props
        idx = props.manual_merge_sources_index
        if 0 <= idx < len(props.manual_merge_sources):
            props.manual_merge_sources.remove(idx)
            props.manual_merge_sources_index = min(idx, len(props.manual_merge_sources) - 1)
        return {'FINISHED'}


classes = (
    ManualMergeSourceItem,
    LMB_UL_manual_merge_sources,
    LMB_OT_manual_merge_source_add,
    LMB_OT_manual_merge_source_remove,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
