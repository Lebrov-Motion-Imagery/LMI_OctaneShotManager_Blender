import bpy
from ...utils import find_layer_collection


def get_tagged_collections(scene):
    """Return a list of collections tagged for the TAGs workflow."""
    return [item.collection for item in scene.otpc_props.tag_collections if item.collection]


def _set_exclude_recursive(layer_coll, state):
    for child in layer_coll.children:
        _set_exclude_recursive(child, state)
        child.exclude = state


def _unexclude_recursive(layer_coll):
    layer_coll.exclude = False
    for child in layer_coll.children:
        _unexclude_recursive(child)


def solo_collection(context, collection):
    """Solo the given collection by excluding all others in the view layer."""
    root_layer = context.view_layer.layer_collection
    _set_exclude_recursive(root_layer, True)
    layer = find_layer_collection(root_layer, collection)
    if layer:
        _unexclude_recursive(layer)


def cycle_tag_collections(context):
    """Cycle through tagged collections, soloing each one in sequence."""
    props = context.scene.otpc_props
    collections = get_tagged_collections(context.scene)
    if not collections:
        return None

    props.tag_cycle_index = (props.tag_cycle_index + 1) % len(collections)
    coll = collections[props.tag_cycle_index]
    solo_collection(context, coll)
    return coll
