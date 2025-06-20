import os
import bpy
import bpy.utils.previews

icon_collections = {}

def load_icons():
    """
    Load custom icons and store them in icon_collections['main'].
    """
    pcoll = bpy.utils.previews.new()
    icons_dir = os.path.join(os.path.dirname(__file__), "Icons")
    # You can load multiple; here we load one
    pcoll.load(
        "pointcloud_bake",  # internal key
        os.path.join(icons_dir, "LMI_SOP_Octane_Pointcloud_Bake.svg"),
        'IMAGE'
    )
    icon_collections['main'] = pcoll


def unload_icons():
    for pcoll in icon_collections.values():
        bpy.utils.previews.remove(pcoll)
    icon_collections.clear()