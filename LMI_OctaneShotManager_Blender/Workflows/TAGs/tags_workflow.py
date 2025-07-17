import bpy
from bpy.types import PropertyGroup, Operator, UIList
from bpy.props import PointerProperty, BoolProperty

from ...utils import find_layer_collection
from .utils import cycle_tag_collections


def _is_parent_of(parent, child):
    """Return True if ``parent`` collection contains ``child`` in its hierarchy."""
    for sub in parent.children:
        if sub == child or _is_parent_of(sub, child):
            return True
    return False


def has_hierarchy_relation(col_a, col_b):
    """Return True if collections have a parent-child relationship."""
    return _is_parent_of(col_a, col_b) or _is_parent_of(col_b, col_a)

class TagCollectionItem(PropertyGroup):
    collection: PointerProperty(
        name="Collection",
        type=bpy.types.Collection,
    )

    def update_exclude(self, context):
        """Update view layer exclusion state when the Solo toggle changes."""
        props = context.scene.otpc_props

        def toggle_layer(layer_coll, state):
            for lc in layer_coll.children:
                toggle_layer(lc, state)
                lc.exclude = state

        selected_layers = []
        for item in props.tag_collections:
            if not item.exclude:
                continue
            coll = item.collection
            if not coll:
                continue
            layer = find_layer_collection(context.view_layer.layer_collection, coll)
            if layer:
                selected_layers.append(layer)

        if selected_layers:
            toggle_layer(context.view_layer.layer_collection, True)
            for layer in selected_layers:
                layer.exclude = False
        else:
            toggle_layer(context.view_layer.layer_collection, False)

    exclude: BoolProperty(
        name="Solo",
        description="Include checked collections only, hiding all others",
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
    bl_description = "Add selected collections to the TAG list"
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

        existing = [item.collection for item in props.tag_collections]
        to_add = []
        for coll in selected_cols:
            if any(item.collection == coll for item in props.tag_collections):
                continue
            for other in existing + to_add:
                if has_hierarchy_relation(coll, other):
                    self.report({'INFO'},
                                "Child or parent collections can not be tagged. Only the same level of collection hierarchy is allowed to TAG")
                    return {'CANCELLED'}
            to_add.append(coll)

        for coll in to_add:
            item = props.tag_collections.add()
            item.collection = coll

        props.tag_collections_index = len(props.tag_collections) - 1
        return {'FINISHED'}


class LMB_OT_tag_collection_remove(Operator):
    bl_idname = "lmb.tag_collection_remove"
    bl_label = "Remove Collection from TAG"
    bl_description = "Remove the selected collection from the TAG list"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.otpc_props
        idx = props.tag_collections_index
        if 0 <= idx < len(props.tag_collections):
            props.tag_collections.remove(idx)
            props.tag_collections_index = min(idx, len(props.tag_collections) - 1)
        return {'FINISHED'}


class LMB_OT_cycle_tag_collection(Operator):
    bl_idname = "lmb.cycle_tag_collection"
    bl_label = "Cycle Tagged Collections"
    bl_description = "Solo each tagged collection one after another"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        coll = cycle_tag_collections(context)
        if coll is None:
            self.report({'INFO'}, "No tagged collections found")
            return {'CANCELLED'}
        return {'FINISHED'}


classes = (
    TagCollectionItem,
    LMB_UL_tag_collections,
    LMB_OT_tag_collection_add,
    LMB_OT_tag_collection_remove,
    LMB_OT_cycle_tag_collection,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
