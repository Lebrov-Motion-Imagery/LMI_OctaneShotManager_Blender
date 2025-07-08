bl_info = {
    "name": "LMI PointCloud Baker",
    "author": "Arseniy Kolenchenko (Lebrov Motion Imagery) & OTOY Inc.",
    "version": (1, 1, 0),
    "blender": (4, 4, 3),
    "location": "View3D > Sidebar > LMI PointCloud Baker",
    "description": (
        "Export Geometry Nodes scattered instances to Octane-compatible "
        "CSVs Scatters and optional instances into Alembic files"
    ),
    "category": "Import-Export",
}

from . import registration


def register():
    """Register all classes and properties."""
    registration.register()


def unregister():
    """Unregister all classes and properties."""
    registration.unregister()


if __name__ == "__main__":
    register()
