# LMI PointCloud Baker - Cinema 4D 2025.3.0 C++ Port Plan

## Target Environment
- **Cinema 4D SDK**: 2025.3.0 (https://developers.maxon.net/docs/cpp/2025_3_0/)
- **Octane Render**: 2025.x
- **Platform**: Windows, macOS, Linux

## Addon Overview

The **LMI PointCloud Baker** is a Blender addon designed to export Geometry Nodes scattered instances to Octane-compatible CSV files and optional Alembic files. It's specifically tailored for VFX workflows where point cloud data needs to be exported for use in Octane Render.

## Core Functionality

### 1. CSV Export System
- **Purpose**: Exports scattered instance transforms to CSV files compatible with Octane's point cloud system
- **Input**: Geometry Nodes instancer objects or collections containing instancers
- **Output**: CSV files with 3x4 transformation matrices (12 values) + ID per instance
- **Features**:
  - Single object or collection-based export
  - Multi-frame export support with custom frame ranges
  - Automatic file naming with scene/shot tokens
  - Coordinate system conversion (Blender to Octane)

### 2. Alembic Export System
- **Purpose**: Exports source geometry as Alembic files for use as instances
- **Input**: Objects or collections containing geometry
- **Output**: Alembic files with face sets
- **Features**:
  - Single object or collection-based export
  - Automatic centering for export
  - Face set preservation

### 3. Coordinate System Handling
- **Asset Matrix**: +90° rotation on X-axis
- **World Matrix**: -90° rotation on X-axis
- **Purpose**: Convert between Blender's coordinate system and Octane's expected format

## Technical Architecture

### File Structure
```
LMI_PointCloud_Baker/
├── __init__.py          # Main entry point and registration
├── properties.py        # UI properties and data structures
├── ui.py               # User interface panel
├── utils.py            # Core utility functions
├── registration.py     # Class registration system
├── icons.py            # Custom icon management
├── exporters/
│   ├── csv_export.py   # CSV export operator
│   └── abc_export.py   # Alembic export operator
└── Icons/
    └── LMI_SOP_Octane_Pointcloud_Bake.svg
```

### Key Components

#### 1. Properties System (`properties.py`)
- **OctanePointCloudProperties**: Main property group containing all UI settings
- **Settings include**:
  - CSV source type (Object/Collection)
  - Alembic source type (Object/Collection)
  - Output directories
  - Multi-frame export settings
  - Naming tokens (Scene/Shot)
  - Overwrite flags

#### 2. CSV Export Logic (`exporters/csv_export.py`)
- **Main Operator**: `LMB_OT_export_csv`
- **Process**:
  1. Parse frame range if multi-frame export enabled
  2. Determine source objects/collections
  3. For each frame:
     - Set scene frame
     - Get evaluated objects from dependency graph
     - Collect instance transforms from instancer objects
    4. Apply coordinate system transformations
    5. Write CSV files per object with proper naming

#### 3. Alembic Export Logic (`exporters/abc_export.py`)
- **Main Operator**: `LMB_OT_export_abc`
- **Process**:
  1. Determine source objects/collections
  2. For each object:
     - Center object at origin
     - Export as Alembic with face sets
     - Restore original position

#### 4. Utility Functions (`utils.py`)
- **Matrix Operations**: Coordinate system conversions
- **File Operations**: Directory creation, filename generation
- **CSV Writing**: Structured CSV output with headers
- **Frame Parsing**: Parse frame ranges (e.g., "1,3-5,10")

## Cinema 4D Port Architecture

### Plugin Structure
```
LMI_PointCloudBaker/
├── LMI_PointCloudBaker.cpp          # Main plugin entry point
├── LMI_PointCloudBaker.h            # Main plugin header
├── LMI_PointCloudBakerDialog.cpp    # UI dialog implementation
├── LMI_PointCloudBakerDialog.h      # UI dialog header
├── LMI_PointCloudBakerData.cpp      # Data structures and properties
├── LMI_PointCloudBakerData.h        # Data structures header
├── LMI_PointCloudBakerExporter.cpp  # Export logic implementation
├── LMI_PointCloudBakerExporter.h    # Export logic header
├── LMI_PointCloudBakerUtils.cpp     # Utility functions
├── LMI_PointCloudBakerUtils.h       # Utility functions header
├── resource.h                        # Resource definitions
├── LMI_PointCloudBaker.rc           # Resource file
└── CMakeLists.txt                   # Build configuration
```

### Core Classes

#### 1. Main Plugin Class
```cpp
class LMI_PointCloudBaker : public CommandData
{
public:
    virtual Bool Execute(BaseDocument* doc) override;
    virtual Bool GetResourceID(Int32& pluginid, Int32& stringid) override;
    virtual Bool GetCommandString(Int32 pluginid, Int32 stringid, String& str) override;
    
private:
    static Bool RegisterPlugin();
    static Bool UnregisterPlugin();
};

// Plugin registration
Bool RegisterLMI_PointCloudBaker()
{
    return RegisterCommandPlugin(ID_LMI_POINTCLOUD_BAKER, 
                                GeLoadString(IDS_LMI_POINTCLOUD_BAKER), 
                                0, 
                                nullptr, 
                                String(), 
                                NewObjClear(LMI_PointCloudBaker));
}
```

#### 2. Dialog Class
```cpp
class LMI_PointCloudBakerDialog : public GeDialog
{
private:
    // UI element IDs
    enum {
        ID_CSV_GROUP = 1000,
        ID_ABC_GROUP,
        ID_SCENE_NAME_EDIT,
        ID_SHOT_NAME_EDIT,
        ID_CSV_OUTPUT_DIR_EDIT,
        ID_ABC_OUTPUT_DIR_EDIT,
        ID_MULTI_FRAME_CHECK,
        ID_FRAME_RANGE_EDIT,
        ID_OVERWRITE_CSV_CHECK,
        ID_OVERWRITE_ABC_CHECK,
        ID_CSV_SOURCE_TYPE_COMBO,
        ID_ABC_SOURCE_TYPE_COMBO,
        ID_CSV_OBJECT_LINK,
        ID_ABC_OBJECT_LINK,
        ID_CSV_LAYER_LINK,
        ID_ABC_LAYER_LINK,
        ID_EXPORT_ABC_CHECK,
        ID_EXPORT_CSV_BUTTON,
        ID_EXPORT_ABC_BUTTON
    };
    
public:
    virtual Bool CreateLayout() override;
    virtual Bool InitValues() override;
    virtual Bool Command(Int32 id, const BaseContainer& msg) override;
    virtual Bool AskClose() override;
    
private:
    void UpdateUI();
    Bool ValidateInputs();
};
```

#### 3. Data Structure Class
```cpp
class LMI_PointCloudBakerData
{
public:
    // CSV Settings
    enum CSVSourceType { CSV_OBJECT, CSV_LAYER };
    CSVSourceType csvSourceType;
    BaseObject* csvObjectSource;
    BaseObject* csvLayerSource;  // Layer object containing instance objects
    maxon::String csvOutputDir;
    Bool overwriteCSV;
    Bool multiFrameExport;
    maxon::String frameRange;
    
    // Alembic Settings
    Bool exportABC;
    enum ABCSourceType { ABC_OBJECT, ABC_LAYER };
    ABCSourceType abcSourceType;
    BaseObject* abcObjectSource;
    BaseObject* abcLayerSource;  // Layer object containing geometry objects
    maxon::String abcOutputDir;
    Bool overwriteABC;
    
    // Naming
    maxon::String sceneName;
    maxon::String shotName;
    
    // Methods
    Bool Load(const BaseContainer& bc);
    Bool Save(BaseContainer& bc) const;
    Bool Validate() const;
    
    // Constructor
    LMI_PointCloudBakerData();
};
```

#### 4. Exporter Class
```cpp
class LMI_PointCloudBakerExporter
{
public:
    // CSV Export
    Bool ExportCSV(BaseDocument* doc, const LMI_PointCloudBakerData& data);
    Bool ExportCSVFrame(BaseDocument* doc, const LMI_PointCloudBakerData& data, Int32 frame);
    Bool WriteCSVFile(const maxon::Url& filepath, const maxon::Vector<InstanceData>& instances, 
                     const Matrix& assetMat, const Matrix& worldMat);
    
    // Instance Collection Methods
    Bool CollectInstancesFromObject(BaseObject* obj, maxon::Vector<InstanceData>& instances);
    Bool CollectInstancesFromLayer(BaseObject* layer, maxon::Vector<InstanceData>& instances);
    
    // Instance Type Handlers
    Bool CollectMoGraphClonerInstances(BaseObject* cloner, maxon::Vector<InstanceData>& instances);
    Bool CollectMatrixInstances(BaseObject* matrixObj, maxon::Vector<InstanceData>& instances);
    Bool CollectOctaneScatterInstances(BaseObject* scatterObj, maxon::Vector<InstanceData>& instances);
    
    // Alembic Export
    Bool ExportAlembic(BaseDocument* doc, const LMI_PointCloudBakerData& data);
    Bool ExportAlembicObject(BaseObject* obj, const maxon::Url& filepath);
    
private:
    // Utility methods
    Matrix BuildAssetMatrix();
    Matrix BuildWorldMatrix();
    maxon::Vector<Int32> ParseFrameRange(const maxon::String& frameRange);
    maxon::String GenerateFilename(const maxon::BaseArray<maxon::String>& parts, const maxon::String& extension);
    Bool EnsureDirectory(const maxon::Url& path);
    
    // Instance data structure
    struct InstanceData {
        maxon::String objectName;
        Matrix transform;
        Int32 instanceId;
    };
};
```

### Key Implementation Differences

#### 1. Instance Collection
- **Blender**: Uses `depsgraph.object_instances` to get scattered instances
- **Cinema 4D**: Support for multiple instance types:
  - **MoGraph Cloner**: Access cloner instance matrices via `BaseObject::GetDeformCache()`
  - **Matrix Object**: Extract instance transforms from matrix object data
  - **Octane Scatter**: Access Octane scatter instance data through Octane API
  - **Layer Selection**: Export all instance objects within a selected layer

#### 2. Coordinate System
- **Blender**: Y-up coordinate system
- **Cinema 4D**: Y-up coordinate system (similar, but matrix operations may differ)

#### 3. File Operations
- **Blender**: Python `os` module
- **Cinema 4D**: C++ `Filename` class and `GeFOpen()` functions

#### 4. UI System
- **Blender**: Panel-based UI in 3D viewport
- **Cinema 4D**: Modal dialog with standard C4D UI elements

### Implementation Steps

#### Phase 1: Core Infrastructure
1. Create main plugin class with registration
2. Implement data structure class
3. Create basic dialog UI
4. Implement utility functions

#### Phase 2: Instance Collection System
1. Implement instance detection and collection methods
2. Create MoGraph Cloner instance extraction
3. Create Matrix Object instance extraction
4. Create Octane Scatter instance extraction
5. Implement layer-based instance collection

#### Phase 3: CSV Export
1. Integrate instance collection with CSV export
2. Create coordinate system conversion matrices
3. Implement CSV file writing
4. Add multi-frame support

#### Phase 4: Alembic Export
1. Implement Alembic export using C4D's Alembic API
2. Add face set support
3. Implement object centering logic

#### Phase 5: UI Polish
1. Add proper validation
2. Implement progress reporting
3. Add error handling
4. Create resource file with icons

### Instance Collection Methods

#### 1. MoGraph Cloner Instance Extraction
```cpp
Bool LMI_PointCloudBakerExporter::CollectMoGraphClonerInstances(BaseObject* cloner, maxon::Vector<InstanceData>& instances)
{
    if (!cloner || cloner->GetType() != Ocloner)
        return false;
    
    // Get the cloner's deform cache which contains instance data
    BaseObject* deformCache = cloner->GetDeformCache();
    if (!deformCache)
        return false;
    
    // Get cloner data using 2025.3.0 API
    ClonerData* clonerData = static_cast<ClonerData*>(cloner->GetDataInstance());
    if (!clonerData)
        return false;
    
    // Get instance count
    Int32 instanceCount = clonerData->GetCount();
    
    // Get the source object (what's being cloned)
    BaseObject* sourceObj = cloner->GetDown();
    if (!sourceObj)
        return false;
    
    maxon::String sourceName = sourceObj->GetName();
    
    // Extract instance matrices using 2025.3.0 API
    for (Int32 i = 0; i < instanceCount; i++)
    {
        Matrix instanceMatrix = clonerData->GetMatrix(i);
        
        InstanceData instance;
        instance.objectName = sourceName;
        instance.transform = instanceMatrix;
        instance.instanceId = i;
        
        instances.Append(instance);
    }
    
    return true;
}
```

#### 2. Matrix Object Instance Extraction
```cpp
Bool LMI_PointCloudBakerExporter::CollectMatrixInstances(BaseObject* matrixObj, maxon::Vector<InstanceData>& instances)
{
    if (!matrixObj || matrixObj->GetType() != Omatrix)
        return false;
    
    // Get matrix data using 2025.3.0 API
    MatrixData* matrixData = static_cast<MatrixData*>(matrixObj->GetDataInstance());
    if (!matrixData)
        return false;
    
    // Get the source object
    BaseObject* sourceObj = matrixObj->GetDown();
    if (!sourceObj)
        return false;
    
    maxon::String sourceName = sourceObj->GetName();
    
    // Get matrix count
    Int32 matrixCount = matrixData->GetCount();
    
    // Extract instance matrices using 2025.3.0 API
    for (Int32 i = 0; i < matrixCount; i++)
    {
        Matrix instanceMatrix = matrixData->GetMatrix(i);
        
        InstanceData instance;
        instance.objectName = sourceName;
        instance.transform = instanceMatrix;
        instance.instanceId = i;
        
        instances.Append(instance);
    }
    
    return true;
}
```

#### 3. Octane Scatter Instance Extraction
```cpp
Bool LMI_PointCloudBakerExporter::CollectOctaneScatterInstances(BaseObject* scatterObj, maxon::Vector<InstanceData>& instances)
{
    if (!scatterObj || scatterObj->GetType() != Ooctane_scatter)
        return false;
    
    // Get Octane scatter data through Octane 2025 API
    // Note: This requires Octane 2025 SDK integration
    OctaneScatterData* scatterData = static_cast<OctaneScatterData*>(scatterObj->GetDataInstance());
    if (!scatterData)
        return false;
    
    // Get the source object
    BaseObject* sourceObj = scatterObj->GetDown();
    if (!sourceObj)
        return false;
    
    maxon::String sourceName = sourceObj->GetName();
    
    // Get scatter instance count using Octane 2025 API
    Int32 instanceCount = scatterData->GetInstanceCount();
    
    // Extract instance matrices using Octane 2025 API
    for (Int32 i = 0; i < instanceCount; i++)
    {
        Matrix instanceMatrix = scatterData->GetInstanceMatrix(i);
        
        InstanceData instance;
        instance.objectName = sourceName;
        instance.transform = instanceMatrix;
        instance.instanceId = i;
        
        instances.Append(instance);
    }
    
    return true;
}
```

#### 4. Layer-Based Instance Collection
```cpp
Bool LMI_PointCloudBakerExporter::CollectInstancesFromLayer(BaseObject* layer, maxon::Vector<InstanceData>& instances)
{
    if (!layer || layer->GetType() != Olayer)
        return false;
    
    // Recursively traverse all objects in the layer using 2025.3.0 API
    BaseObject* child = layer->GetDown();
    while (child)
    {
        // Check if this object is an instance generator
        if (IsInstanceGenerator(child))
        {
            CollectInstancesFromObject(child, instances);
        }
        
        // Recursively check children
        if (child->GetDown())
        {
            CollectInstancesFromLayer(child, instances);
        }
        
        child = child->GetNext();
    }
    
    return true;
}

Bool LMI_PointCloudBakerExporter::IsInstanceGenerator(BaseObject* obj)
{
    if (!obj)
        return false;
    
    // Check for supported instance generator types using 2025.3.0 API
    switch (obj->GetType())
    {
        case Ocloner:        // MoGraph Cloner
        case Omatrix:        // Matrix Object
        case Ooctane_scatter: // Octane Scatter
            return true;
        default:
            return false;
    }
}
```

#### 5. Main Instance Collection Method
```cpp
Bool LMI_PointCloudBakerExporter::CollectInstancesFromObject(BaseObject* obj, maxon::Vector<InstanceData>& instances)
{
    if (!obj)
        return false;
    
    switch (obj->GetType())
    {
        case Ocloner:
            return CollectMoGraphClonerInstances(obj, instances);
            
        case Omatrix:
            return CollectMatrixInstances(obj, instances);
            
        case Ooctane_scatter:
            return CollectOctaneScatterInstances(obj, instances);
            
        case Olayer:
            return CollectInstancesFromLayer(obj, instances);
            
        default:
            return false;
    }
}
```

### Technical Considerations

#### 1. Instance Detection
- **MoGraph Cloner**: Use `BaseObject::GetDeformCache()` and `ClonerData` to access instance matrices
- **Matrix Object**: Use `MatrixData` to access stored transformation matrices
- **Octane Scatter**: Requires Octane SDK integration to access scatter instance data
- **Layer Objects**: Recursively traverse layer hierarchy to find instance generators

#### 2. Matrix Operations
- C4D uses different matrix conventions than Blender
- Test coordinate system conversions thoroughly
- Consider using C4D's built-in matrix utilities

#### 3. UI Implementation for Layer Selection
```cpp
Bool LMI_PointCloudBakerDialog::CreateLayout()
{
    // Create main layout using 2025.3.0 API
    if (!GroupBegin(ID_CSV_GROUP, "CSV Settings", BFH_SCALEFIT | BFV_SCALEFIT, 0, 0))
        return false;
    
    // Naming section
    if (!GroupBegin(0, "Naming", BFH_SCALEFIT | BFV_FIT, 0, 0))
        return false;
    AddEditText(ID_SCENE_NAME_EDIT, BFH_SCALEFIT, 0, 0, "Scene Name");
    AddEditText(ID_SHOT_NAME_EDIT, BFH_SCALEFIT, 0, 0, "Shot Name");
    GroupEnd();
    
    // CSV Source Type Selection
    AddComboBox(ID_CSV_SOURCE_TYPE_COMBO, BFH_SCALEFIT, 0, 0, "CSV Source Type");
    AddChild(ID_CSV_SOURCE_TYPE_COMBO, CSV_OBJECT, "Single Object");
    AddChild(ID_CSV_SOURCE_TYPE_COMBO, CSV_LAYER, "Layer");
    
    // CSV Object/Layer Selection
    AddLinkBox(ID_CSV_OBJECT_LINK, BFH_SCALEFIT, 0, 0, "CSV Object");
    AddLinkBox(ID_CSV_LAYER_LINK, BFH_SCALEFIT, 0, 0, "CSV Layer");
    
    // CSV Settings
    AddEditText(ID_CSV_OUTPUT_DIR_EDIT, BFH_SCALEFIT, 0, 0, "CSV Output Directory");
    AddCheckBox(ID_OVERWRITE_CSV_CHECK, BFH_SCALEFIT, 0, 0, "Overwrite CSVs");
    AddCheckBox(ID_MULTI_FRAME_CHECK, BFH_SCALEFIT, 0, 0, "Multi-frame Export");
    AddEditText(ID_FRAME_RANGE_EDIT, BFH_SCALEFIT, 0, 0, "Frame Range");
    
    AddButton(ID_EXPORT_CSV_BUTTON, BFH_SCALEFIT, 0, 0, "Export CSV");
    GroupEnd();
    
    // Alembic section
    AddCheckBox(ID_EXPORT_ABC_CHECK, BFH_SCALEFIT, 0, 0, "Export Alembic");
    
    if (!GroupBegin(ID_ABC_GROUP, "Alembic Settings", BFH_SCALEFIT | BFV_SCALEFIT, 0, 0))
        return false;
    
    // Alembic Source Type Selection
    AddComboBox(ID_ABC_SOURCE_TYPE_COMBO, BFH_SCALEFIT, 0, 0, "Alembic Source Type");
    AddChild(ID_ABC_SOURCE_TYPE_COMBO, ABC_OBJECT, "Single Object");
    AddChild(ID_ABC_SOURCE_TYPE_COMBO, ABC_LAYER, "Layer");
    
    // Alembic Object/Layer Selection
    AddLinkBox(ID_ABC_OBJECT_LINK, BFH_SCALEFIT, 0, 0, "ABC Object");
    AddLinkBox(ID_ABC_LAYER_LINK, BFH_SCALEFIT, 0, 0, "ABC Layer");
    
    AddEditText(ID_ABC_OUTPUT_DIR_EDIT, BFH_SCALEFIT, 0, 0, "ABC Output Directory");
    AddCheckBox(ID_OVERWRITE_ABC_CHECK, BFH_SCALEFIT, 0, 0, "Overwrite ABCs");
    AddButton(ID_EXPORT_ABC_BUTTON, BFH_SCALEFIT, 0, 0, "Export Alembic");
    GroupEnd();
    
    return true;
}

Bool LMI_PointCloudBakerDialog::Command(Int32 id, const BaseContainer& msg)
{
    switch (id)
    {
        case ID_CSV_SOURCE_TYPE_COMBO:
        {
            Int32 selection = GetInt32(ID_CSV_SOURCE_TYPE_COMBO);
            Bool showObject = (selection == CSV_OBJECT);
            Bool showLayer = (selection == CSV_LAYER);
            
            Show(ID_CSV_OBJECT_LINK, showObject);
            Show(ID_CSV_LAYER_LINK, showLayer);
            break;
        }
        
        case ID_ABC_SOURCE_TYPE_COMBO:
        {
            Int32 selection = GetInt32(ID_ABC_SOURCE_TYPE_COMBO);
            Bool showObject = (selection == ABC_OBJECT);
            Bool showLayer = (selection == ABC_LAYER);
            
            Show(ID_ABC_OBJECT_LINK, showObject);
            Show(ID_ABC_LAYER_LINK, showLayer);
            break;
        }
        
        case ID_EXPORT_ABC_CHECK:
        {
            Bool exportABC = GetBool(ID_EXPORT_ABC_CHECK);
            Show(ID_ABC_GROUP, exportABC);
            break;
        }
        
        case ID_EXPORT_CSV_BUTTON:
        {
            // Handle CSV export
            break;
        }
        
        case ID_EXPORT_ABC_BUTTON:
        {
            // Handle Alembic export
            break;
        }
    }
    
    return true;
}
```

#### 4. Object Type Validation
```cpp
Bool LMI_PointCloudBakerExporter::ValidateCSVSource(BaseObject* obj, CSVSourceType sourceType)
{
    if (!obj)
        return false;
    
    if (sourceType == CSV_OBJECT)
    {
        // Validate single object is an instance generator
        return IsInstanceGenerator(obj);
    }
    else if (sourceType == CSV_LAYER)
    {
        // Validate layer contains at least one instance generator
        return ContainsInstanceGenerator(obj);
    }
    
    return false;
}

Bool LMI_PointCloudBakerExporter::ContainsInstanceGenerator(BaseObject* obj)
{
    if (!obj)
        return false;
    
    // Check if this object is an instance generator
    if (IsInstanceGenerator(obj))
        return true;
    
    // Recursively check children
    BaseObject* child = obj->GetDown();
    while (child)
    {
        if (ContainsInstanceGenerator(child))
            return true;
        child = child->GetNext();
    }
    
    return false;
}
```

#### 3. File I/O
- Use C4D's `Filename` class for path operations
- Implement proper error handling for file operations
- Consider using C4D's progress system for large exports

#### 5. CSV Export Integration
```cpp
Bool LMI_PointCloudBakerExporter::ExportCSV(BaseDocument* doc, const LMI_PointCloudBakerData& data)
{
    if (!doc)
        return false;
    
    // Determine frames to export using 2025.3.0 API
    maxon::Vector<Int32> frames;
    if (data.multiFrameExport && data.frameRange.GetLength() > 0)
    {
        frames = ParseFrameRange(data.frameRange);
    }
    else
    {
        frames.Append(doc->GetTime().GetFrame(doc->GetFps()));
    }
    
    // Determine sources based on source type
    maxon::Vector<BaseObject*> sources;
    maxon::String rootFolder;
    
    if (data.csvSourceType == CSV_OBJECT)
    {
        if (data.csvObjectSource)
        {
            sources.Append(data.csvObjectSource);
            rootFolder = "";
        }
    }
    else if (data.csvSourceType == CSV_LAYER)
    {
        if (data.csvLayerSource)
        {
            // Collect all instance generators from the layer
            CollectInstanceGeneratorsFromLayer(data.csvLayerSource, sources);
            rootFolder = data.csvLayerSource->GetName() + "_CSVs";
        }
    }
    
    if (sources.GetCount() == 0)
    {
        // Report error: no valid sources
        return false;
    }
    
    // Prepare output directory using 2025.3.0 API
    maxon::Url baseDir = maxon::Url(data.csvOutputDir);
    if (!EnsureDirectory(baseDir))
        return false;
    
    // Prepare transform matrices
    Matrix assetMat = BuildAssetMatrix();
    Matrix worldMat = BuildWorldMatrix();
    
    // Iterate through frames and sources
    for (Int32 frame : frames)
    {
        // Set document time using 2025.3.0 API
        BaseTime frameTime = BaseTime(frame, doc->GetFps());
        doc->SetTime(frameTime);
        
        for (BaseObject* source : sources)
        {
            maxon::Vector<InstanceData> instances;
            
            // Collect instances from this source
            if (!CollectInstancesFromObject(source, instances))
                continue;
            
            // Group instances by object name using 2025.3.0 API
            maxon::HashMap<maxon::String, maxon::Vector<InstanceData>> groups;
            for (const InstanceData& instance : instances)
            {
                groups.Insert(instance.objectName, maxon::Vector<InstanceData>()).GetValue().Append(instance);
            }
            
            // Write CSV files per object
            maxon::String subfolder = rootFolder.IsEmpty() ? source->GetName() : 
                                     (rootFolder + "/" + source->GetName());
            
            for (auto& group : groups)
            {
                maxon::String objectName = group.GetKey();
                maxon::Vector<InstanceData>& objectInstances = group.GetValue();
                
                // Generate filename
                maxon::BaseArray<maxon::String> parts;
                parts.Append(objectName + "_PC");
                if (data.multiFrameExport)
                    parts.Append(maxon::String::IntToString(frame));
                
                maxon::String filename = GenerateFilename(parts, "csv");
                maxon::Url filepath = baseDir + subfolder + "/" + filename;
                
                // Write CSV file
                if (!WriteCSVFile(filepath, objectInstances, assetMat, worldMat))
                    continue;
            }
        }
    }
    
    return true;
}

Bool LMI_PointCloudBakerExporter::WriteCSVFile(const maxon::Url& filepath, 
                                               const maxon::Vector<InstanceData>& instances,
                                               const Matrix& assetMat, 
                                               const Matrix& worldMat)
{
    // Create directory if it doesn't exist using 2025.3.0 API
    maxon::Url dir = filepath.GetDirectory();
    if (!EnsureDirectory(dir))
        return false;
    
    // Open file for writing using 2025.3.0 API
    maxon::BaseFile<maxon::FileInterface> file;
    if (file.Open(filepath, maxon::FileInterface::OPENMODE_WRITE) != maxon::OK)
        return false;
    
    // Write CSV header
    maxon::String header = "M00,M01,M02,M03,M10,M11,M12,M13,M20,M21,M22,M23,ID\n";
    file.Write(header.GetCStringCopy());
    
    // Write instance data
    for (Int32 i = 0; i < instances.GetCount(); i++)
    {
        const InstanceData& instance = instances[i];
        
        // Apply coordinate system transformations
        Matrix finalMatrix = worldMat * (instance.transform * assetMat);
        
        // Flatten matrix to CSV row using 2025.3.0 API
        maxon::String row;
        for (Int32 r = 0; r < 3; r++)
        {
            for (Int32 c = 0; c < 4; c++)
            {
                if (r > 0 || c > 0)
                    row += ",";
                row += maxon::String::FloatToString(finalMatrix(r, c), 6);
            }
        }
        row += "," + maxon::String::IntToString(i) + "\n";
        
        file.Write(row.GetCStringCopy());
    }
    
    return true;
}
```

#### 4. Memory Management
- C4D C++ requires careful memory management
- Use C4D's memory allocation functions
- Implement proper cleanup in destructors

### Testing Strategy

#### 1. Unit Tests
- Test matrix operations independently
- Test frame range parsing
- Test filename generation

#### 2. Integration Tests
- Test with MoGraph cloner objects
- Test with different coordinate systems
- Test multi-frame exports

#### 3. Performance Tests
- Test with large numbers of instances
- Test memory usage during export
- Test export speed vs. Blender version

### Required Includes and Dependencies

#### 1. Main Plugin Header
```cpp
// LMI_PointCloudBaker.h
#pragma once

#include "c4d.h"
#include "c4d_baseobject.h"
#include "c4d_basedocument.h"
#include "c4d_commanddata.h"
#include "c4d_gedialog.h"
#include "c4d_file.h"
#include "c4d_time.h"
#include "c4d_mograph.h"
#include "c4d_matrix.h"

// Maxon API includes for 2025.3.0
#include "maxon/string.h"
#include "maxon/vector.h"
#include "maxon/hashmap.h"
#include "maxon/basearray.h"
#include "maxon/url.h"
#include "maxon/file.h"
#include "maxon/error.h"

// Octane includes (if available)
#ifdef OCTANE_AVAILABLE
#include "octane_scatter.h"
#endif

// Plugin IDs
#define ID_LMI_POINTCLOUD_BAKER 1050001
#define IDS_LMI_POINTCLOUD_BAKER 1050002
```

#### 2. CMakeLists.txt for C4D 2025.3.0
```cmake
cmake_minimum_required(VERSION 3.20)
project(LMI_PointCloudBaker)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find Cinema 4D SDK
find_package(Cinema4D REQUIRED)

# Include directories
include_directories(${CINEMA4D_INCLUDE_DIRS})

# Source files
set(SOURCES
    LMI_PointCloudBaker.cpp
    LMI_PointCloudBakerDialog.cpp
    LMI_PointCloudBakerData.cpp
    LMI_PointCloudBakerExporter.cpp
    LMI_PointCloudBakerUtils.cpp
)

# Create plugin
add_library(LMI_PointCloudBaker SHARED ${SOURCES})

# Link libraries
target_link_libraries(LMI_PointCloudBaker
    ${CINEMA4D_LIBRARIES}
    maxon
    c4d
)

# Set output directory
set_target_properties(LMI_PointCloudBaker PROPERTIES
    LIBRARY_OUTPUT_DIRECTORY ${CINEMA4D_PLUGIN_DIR}
)
```

#### 3. Resource File
```rc
// LMI_PointCloudBaker.rc
#include "resource.h"

ID_LMI_POINTCLOUD_BAKER    PLUGIN    "LMI_PointCloudBaker.res"
IDS_LMI_POINTCLOUD_BAKER   STRING    "LMI PointCloud Baker"
```

### Build and Installation

#### 1. Prerequisites
- Cinema 4D 2025.3.0 SDK installed
- CMake 3.20 or later
- Visual Studio 2019/2022 (Windows) or Xcode (macOS)
- Octane 2025 SDK (optional, for Octane scatter support)

#### 2. Build Steps
```bash
# Create build directory
mkdir build && cd build

# Configure with CMake
cmake .. -DCINEMA4D_SDK_PATH=/path/to/c4d/sdk

# Build
cmake --build . --config Release
```

#### 3. Installation
- Copy the built plugin to Cinema 4D's plugin directory
- Restart Cinema 4D
- The plugin will appear in the Plugins menu

This port plan provides a comprehensive roadmap for converting the Blender addon to a Cinema 4D 2025.3.0 C++ plugin while maintaining all core functionality and adapting to C4D's modern API architecture and conventions.