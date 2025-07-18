# LMI Octane Shot Manager for Blender

LMI Octane Shot Manager is a Blender add-on designed to simplify exporting scenes, shots and point clouds for rendering in Octane. It provides a TAG-based workflow allowing you to export collections as ORBX files, merge them back together and manage large scenes via chunked frame ranges.

This guide explains installation and everyday use for artists. No programming knowledge is required.

## Installation

1. Download the repository as a `.zip` file from GitHub.
2. In Blender open **Edit → Preferences → Add-ons** and click **Install…**.
3. Choose the downloaded zip (or the `LMI_OctaneShotManager_Blender` folder) and confirm.
4. Enable the add-on named **LMI Octane Shot Manager**.

For ORBX merging you also need **Octane Standalone**. Set the path to the executable in the add-on panel before merging.

## Naming and Output Paths

All exports share a common **Output Root Directory**. Inside it the add-on creates a `Shot_Manager` folder with subfolders for each export type. File names start with a prefix built from the scene and shot names:

```
Scene-{SCENE_NAME}_Shot-{SHOT_NAME}
```

The scene name can come from the current `.blend` file, the scene itself or be entered manually. The shot name can come from a selected camera or be entered manually.

### Example

With an output directory of `/project/shot1`, scene name `MyScene` and shot name `MainCam` the prefix becomes `Scene-MyScene_Shot-MainCam` and exports are stored like:

```
/project/shot1/Shot_Manager/
 ├── TAGs/Scene-MyScene_Shot-MainCam/...
 ├── CSVs/Scene-MyScene_Shot-MainCam/...
 └── ABCs/Scene-MyScene_Shot-MainCam/...
```

## TAGs Workflow

The TAGs workflow lets you export specific collections as standalone ORBX files. Collections added to the TAG list can be **soloed**, cycled through or exported.

1. In the panel enable **LMI TAGs Workflow**.
2. Select one or more collections in the Outliner and click **+** to tag them.
3. Use the **Solo** checkboxes to include or exclude collections during export.

### Chunking

Large frame ranges can be split into smaller pieces called **chunks**. Each chunk creates a separate ORBX file spanning a fixed number of frames. Chunking keeps individual ORBX files small so they load easily on the OTOY Render Network.

Best practice is to keep the same chunk size for all exports of a scene. The default of 25 frames works well for most projects.

### Per‑Tag ORBX Export

Use **Export all Tags to a 'Per Tag' ORBX** to export each tagged collection separately. This takes more time but greatly reduces the RAM/VRAM used during export, which is essential for heavy scenes. The resulting files are saved under:

```
{Output Root}/Shot_Manager/TAGs/{PREFIX}/Per_Tag_ORBX/
```

File naming when chunking is enabled:

```
{PREFIX}_{COLLECTION}_pt{PART}_{START}-{END}.orbx
```

Without chunking the part number is omitted:

```
{PREFIX}_{COLLECTION}_{START}-{END}.orbx
```

### Direct Merged ORBX Export

The **Export directly to a Merged ORBX** option creates a single ORBX sequence containing all tagged collections without producing per-tag files. Output goes to:

```
{Output Root}/Shot_Manager/TAGs/{PREFIX}/Merged_ORBX/
```

Filenames follow the same chunked or unchunked pattern but use `Merged` instead of the collection name.

### Automatic Merging

After exporting per-tag files you can merge them back into a single ORBX sequence using **Merge selected Tags** or **Merge all Tags**. Set the path to the Octane Standalone executable first. Merged files are placed in `Merged_ORBX` using this naming:

```
{PREFIX}_Merged_pt{PART}_{START}-{END}.orbx
```

## Manual ORBX Merge

The Manual ORBX Merge section allows you to combine arbitrary ORBX files.

1. Choose a save directory and base scene name.
2. Pick a destination ORBX and one or more source ORBX files.
3. Click **Merge ORBX** to generate merged files in the chosen directory.

If the selected files already include frame ranges, the add-on preserves those ranges and creates filenames like:

```
{BASE_NAME}_pt{PART}_{START}-{END}.orbx
```

Otherwise a single file `{BASE_NAME}.orbx` is produced.

## PointCloud CSV and Alembic Export

The panel also provides tools to export CSV point clouds and Alembic files. Files are stored under `CSVs` and `ABCs` folders using the same scene/shot prefix.

## Best Practices

- Set your Output Root Directory before exporting to keep files organized.
- Keep chunk size consistent across exports. Changing it mid‑project can lead to mismatched file names.
- For large scenes use **Per Tag ORBX** export with chunking. Although export times increase, memory usage is minimized and files work better on the OTOY Render Network.
- When re‑exporting files enable **Overwrite ORBX** to replace existing chunks safely.
- Verify that your Octane Standalone path is correct before running merge operations.

With these tips you can manage complex shots and massive frame ranges with predictable file names and folder structures.

