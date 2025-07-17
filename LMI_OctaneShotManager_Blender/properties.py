import bpy
import os
from bpy.props import (
    BoolProperty,
    EnumProperty,
    PointerProperty,
    StringProperty,
    CollectionProperty,
    IntProperty,
)

from .Workflows.TAGs.tags_workflow import TagCollectionItem
from .utils import resolve_octane_executable


def _update_octane_path(self, context):
    """Resolve and store an absolute path to the Octane executable."""
    if not self.octane_standalone_path:
        return
    resolved = resolve_octane_executable(self.octane_standalone_path)
    if resolved:
        self["octane_standalone_path"] = resolved
    else:
        abs_path = os.path.abspath(bpy.path.abspath(self.octane_standalone_path))
        self["octane_standalone_path"] = abs_path


class OctanePointCloudProperties(bpy.types.PropertyGroup):
    """
    Holds all user-configurable settings for CSV and Alembic exports.
    """

    # CSV Source configuration
    csv_src_type: EnumProperty(
        name="CSV Source Type",
        description="Export from single object or collection for CSV",
        items=[
            ('OBJECT', "Object", "Export a single instancer object"),
            ('COLLECTION', "Collection", "Export all objects in a collection"),
        ],
        default='OBJECT',
    ) # type: ignore
    csv_object_source: PointerProperty(
        name="CSV Object",
        description="Instancer object for CSV export",
        type=bpy.types.Object,
    )
    csv_collection_source: PointerProperty(
        name="CSV Collection",
        description="Collection of instancer objects for CSV export",
        type=bpy.types.Collection,
    )

    # Multi-frame CSV export
    multi_frame_export: BoolProperty(
        name="Multi-frame CSV Export",
        description="Enable exporting CSVs over a frame sequence",
        default=False,
    )
    frame_range: StringProperty(
        name="Frame Range",
        description="Comma-separated frames or ranges (e.g. '1,5,10-20')",
        default="",
    )

    # Naming
    scene_name_source: EnumProperty(
        name="Scene Name Source",
        description="How to determine the scene name token",
        items=[
            ('FILE', "Blender File", "Use the .blend file name"),
            ('SCENE', "Scene Name", "Use the current scene name"),
            ('MANUAL', "Manual", "Input scene name manually"),
        ],
        default='MANUAL',
    )
    scene_name_manual: StringProperty(
        name="Scene Name",
        description="Manual scene name token",
        default="",
    )

    shot_name_source: EnumProperty(
        name="Shot Name Source",
        description="How to determine the shot name token",
        items=[
            ('OBJECT', "Selected Camera", "Use the chosen object's name"),
            ('MANUAL', "Manual", "Input shot name manually"),
        ],
        default='MANUAL',
    )
    shot_object_source: PointerProperty(
        name="Shot Camera",
        description="Object to use for the shot name",
        type=bpy.types.Object,
    )
    shot_name_manual: StringProperty(
        name="Shot Name",
        description="Manual shot name token",
        default="",
    )

    # Output root directory used for all exports
    root_output_dir: StringProperty(
        name="Output Root Directory",
        description="Top directory for all Shot Manager exports",
        subtype='DIR_PATH',
    )
    overwrite_csv: BoolProperty(
        name="Overwrite CSVs",
        description="Allow overwriting existing CSV files",
        default=False,
    )

    # Alembic export settings
    export_abc: BoolProperty(
        name="Export Alembic",
        description="Enable exporting instancer sources as Alembic",
        default=False,
    )
    abc_src_type: EnumProperty(
        name="ABC Source Type",
        description="Export single object or collection as Alembic",
        items=[
            ('OBJECT', "Object", "Export a single Alembic file"),
            ('COLLECTION', "Collection", "Export multiple Alembic files from a collection"),
        ],
        default='OBJECT',
    )
    abc_object_source: PointerProperty(
        name="ABC Object",
        description="Object to export as Alembic",
        type=bpy.types.Object,
    )
    abc_collection_source: PointerProperty(
        name="ABC Collection",
        description="Collection of objects to export as multiple Alembics",
        type=bpy.types.Collection,
    )
    overwrite_abc: BoolProperty(
        name="Overwrite ABCs",
        description="Allow overwriting existing Alembic files",
        default=False,
    )

    # UI toggles
    show_pointcloud_baker: BoolProperty(
        name="Show PointCloud Baker",
        description="Display PointCloud Baker settings",
        default=False,
    )
    show_naming_settings: BoolProperty(
        name="Show Naming Settings",
        description="Display scene and shot naming options",
        default=True,
    )
    show_tags_workflow: BoolProperty(
        name="Show TAGs Workflow",
        description="Display LMI TAGs Workflow settings",
        default=False,
    )

    tag_collections: CollectionProperty(type=TagCollectionItem)
    tag_collections_index: IntProperty(default=-1)
    tag_cycle_index: IntProperty(default=-1, options={'HIDDEN'})

    # TAGs frame range and chunk settings
    tag_frame_start: IntProperty(
        name="First Frame",
        description="First frame to export TAGs",
        default=1,
    )
    tag_frame_end: IntProperty(
        name="Last Frame",
        description="Last frame to export TAGs",
        default=250,
    )
    tag_use_chunks: BoolProperty(
        name="Use Chunking",
        description="Split TAG export into equal sized chunks",
        default=True,
    )
    tag_chunk_size: IntProperty(
        name="Chunk Size",
        description="Number of frames per chunk when exporting TAGs",
        default=25,
        min=1,
    )

    overwrite_orbx: BoolProperty(
        name="Overwrite ORBX",
        description="Allow overwriting existing ORBX files",
        default=False,
    )

    octane_standalone_path: StringProperty(
        name="Octane Standalone",
        description="Absolute path to the Octane executable",
        subtype='FILE_PATH',
        update=_update_octane_path,
    )
