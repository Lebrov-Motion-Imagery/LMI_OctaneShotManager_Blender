import bpy
from bpy.types import PropertyGroup, Operator, UIList
from bpy.props import PointerProperty, BoolProperty

from .utils import find_layer_collection

class TagCollectionItem(PropertyGroup):
    collection: PointerProperty(
        name="Collection",
        type=bpy.types.Collection,
    )

    def update_exclude(self, context):
        coll = self.collection
        if not coll:
            return
        layer = find_layer_collection(context.view_layer.layer_collection, coll)
        if layer:
            layer.exclude = self.exclude

    exclude: BoolProperty(
        name="Exclude",
        description="Exclude this collection from the view layer",
        default=False,
        update=update_exclude,
    )


class LMB_UL_tag_collections(UIList):
    """UIList to display tagged collections with exclude toggles."""

    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        coll = item.collection
        if coll:
            row = layout.row(align=True)
            row.prop(item, "collection", text="", emboss=False)
            row.prop(item, "exclude", text="")
        else:
            row = layout.row(align=True)
            row.prop(item, "collection", text="", emboss=False, icon='ERROR')
            row.prop(item, "exclude", text="")


class LMB_OT_tag_collection_add(Operator):
    bl_idname = "lmb.tag_collection_add"
    bl_label = "Add Collection to TAG"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.otpc_props

        selected_cols = [id for id in getattr(context, "selected_ids", [])
                         if isinstance(id, bpy.types.Collection)]

        if not selected_cols:
            # Try to fetch selection from an Outliner area since this operator is
            # executed from another editor where ``context.selected_ids`` is
            # empty.
            for window in context.window_manager.windows:
                for area in window.screen.areas:
                    if area.type != 'OUTLINER':
                        continue
                    region = next((r for r in area.regions if r.type == 'WINDOW'), None)
                    if region is None:
                        continue
                    with context.temp_override(window=window, area=area, region=region):
                        selected_cols = [id for id in getattr(bpy.context, "selected_ids", [])
                                         if isinstance(id, bpy.types.Collection)]
                    if selected_cols:
                        break
                if selected_cols:
                    break

        if not selected_cols:
            self.report({'INFO'},
                        "There are no collections selected, nothing to add.")
            return {'CANCELLED'}

        for coll in selected_cols:
            if any(item.collection == coll for item in props.tag_collections):
                continue
            item = props.tag_collections.add()
            item.collection = coll

        props.tag_collections_index = len(props.tag_collections) - 1
        return {'FINISHED'}


class LMB_OT_tag_collection_remove(Operator):
    bl_idname = "lmb.tag_collection_remove"
    bl_label = "Remove Collection from TAG"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.otpc_props
        idx = props.tag_collections_index
        if 0 <= idx < len(props.tag_collections):
            props.tag_collections.remove(idx)
            props.tag_collections_index = min(idx, len(props.tag_collections) - 1)
        return {'FINISHED'}


classes = (
    TagCollectionItem,
    LMB_UL_tag_collections,
    LMB_OT_tag_collection_add,
    LMB_OT_tag_collection_remove,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
