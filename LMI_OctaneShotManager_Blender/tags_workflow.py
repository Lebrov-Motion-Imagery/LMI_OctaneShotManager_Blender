import bpy
import os
from bpy.types import PropertyGroup, Operator, UIList
from bpy.props import PointerProperty, BoolProperty

from .utils import (
    find_layer_collection,
    ensure_directory,
    generate_export_filename,
    build_scene_shot_prefix,
    ORBX_EXTENSION,
    chunk_frame_range,
)


def _is_parent_of(parent, child):
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
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.otpc_props
        idx = props.tag_collections_index
        if 0 <= idx < len(props.tag_collections):
            props.tag_collections.remove(idx)
            props.tag_collections_index = min(idx, len(props.tag_collections) - 1)
        return {'FINISHED'}


class LMB_OT_export_tags_orbx(Operator):
    """Export all tagged collections to ORBX files."""
    bl_idname = "lmb.export_tags_orbx"
    bl_label = "Export All TAGs to ORBX"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        props = context.scene.otpc_props

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
        ranges = [(frame_start, frame_end)]
        if props.tag_use_chunks:
            ranges = chunk_frame_range(frame_start, frame_end, max(1, props.tag_chunk_size))

        for item in props.tag_collections:
            coll = item.collection
            if not coll:
                continue
            coll_name = coll.name
            for r_start, r_end in ranges:
                parts = [prefix, coll_name, f"{r_start}-{r_end}"]
                filename = generate_export_filename(parts, ORBX_EXTENSION)
                filepath = os.path.join(base_dir, filename)
                bpy.ops.export.orbx(filepath=filepath,
                                    frame_start=r_start,
                                    frame_end=r_end)

        self.report({'INFO'}, "ORBX TAG export completed.")
        return {'FINISHED'}


classes = (
    TagCollectionItem,
    LMB_UL_tag_collections,
    LMB_OT_tag_collection_add,
    LMB_OT_tag_collection_remove,
    LMB_OT_export_tags_orbx,
)


def register():
    for cls in classes:
        bpy.utils.register_class(cls)


def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
