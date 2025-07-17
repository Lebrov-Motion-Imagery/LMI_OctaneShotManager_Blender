from . import registration

bl_info = {
    "name": "LMI_OctaneShotManager_Blender",
    "author": "Arseniy Kolenchenko (Lebrov Motion Imagery) & Render Foundation.",
    "version": (1, 1, 0),
    "blender": (4, 4, 3),
    "location": "View3D > Sidebar > LMI Octane ShotManager",
    "description": (
        "LMI Octane ShotManager for Blender"
        "Manages TAGs workflow for Octane Render in Blender"
        "Exports selected collections to separate ORBX files with ability to merge them back to a single scene"
        "Export Geometry Nodes scattered instances to Octane-compatible "
        "CSVs Scatters and optional instances into Alembic files"
    ),
    "category": "Import-Export",
}


def register():
    """Register all classes and properties."""
    registration.register()


def unregister():
    """Unregister all classes and properties."""
    registration.unregister()


if __name__ == "__main__":
    register()
