--[[
-- Combine the geometry meshes from two or more ORBX files into a single scene file
-- Use with Octane command line:
-- octane.exe --no-gui --script "ORBXCombiner.lua" -A "C:\temp\saveAsScene.orbx" "C:\temp\destinationScene.orbx" "C:\temp\sourceScene1.orbx" "C:\temp\sourceScene2.orbx" ...
--
-- @description The code creates a new ORBX scene file from two or more existing scenes by integrating the geometry node of the sourcescene into the destinationscene using a geometrygroup node.
-- @author      Padi Frigg padi@rendertoken.com
-- @version     0.3
-- @param       saveAsScene       The path where the combined scene will be saved.
-- @param       destinationScene  The path to the destination scene file.
-- @param       sourceScene1      The path to the first source scene file.
-- @param       sourceScene2      The path to the second source scene file.
-- @param       ...               Additional source scene files.
--]]

-- Function to check if the required command line arguments are provided
-- @param saveAsScene The path where the combined scene will be saved
-- @param destinationScene The path to the destination scene file
-- @return boolean Returns true if both arguments are provided, false otherwise
local function checkRequiredArguments(saveAsScene, destinationScene)
  if not saveAsScene then
    print("saveAsScene required as an -A script argument.")
    return false
  end
  if not destinationScene then
    print("Destination scene required as an -A script argument.")
    return false
  end
  return true
end

-- Function to create a temporary node graph and a geometry group node
-- @return tempGraph The created temporary node graph
-- @return geoGroupNode The created geometry group node
local function createTemporaryGraph()
  local tempGraph = octane.nodegraph.createRootGraph()
  local geoGroupNode = octane.node.create {
    type = octane.NT_GEO_GROUP,
    name = "Geometry group",
    graphOwner = tempGraph,
  }
  return tempGraph, geoGroupNode
end

-- Function to process each source scene file and combine their geometries
-- @param sourceScenes Table containing the paths to the source scene files
-- @param geoGroupNode The geometry group node to connect the source geometries to
local function processSourceScenes(sourceScenes, geoGroupNode)
  for i, sourceScene in ipairs(sourceScenes) do
    print(string.format("Opening source scene: %s", sourceScene))
    octane.project.load(sourceScene)
    local sourceGraph = octane.project.getSceneGraph()
    local sourceRenderTarget = sourceGraph:findFirstNode(octane.NT_RENDERTARGET)
    local sourceGeometry = sourceRenderTarget:getConnectedNode(octane.P_MESH)
    local sourceGeometryCopy = geoGroupNode.graphOwner:copyFromGraph(sourceGraph, {sourceGeometry})[1]
    geoGroupNode:setAttribute(octane.A_PIN_COUNT, i)
    geoGroupNode:connectToIx(i, sourceGeometryCopy)
    geoGroupNode:deleteUnconnectedItems()
  end
end

-- Function to combine the processed source scenes with the destination scene
-- @param destinationScene The path to the destination scene file
-- @param geoGroupNode The geometry group node containing the combined source geometries
local function combineScenes(destinationScene, geoGroupNode)
  print(string.format("Opening destination scene: %s", destinationScene))
  octane.project.load(destinationScene)
  local destinationGraph = octane.project.getSceneGraph()
  local destinationRenderTarget = destinationGraph:findFirstNode(octane.NT_RENDERTARGET)
  local destinationGeometry = destinationRenderTarget:getConnectedNode(octane.P_MESH)
  local destinationGeoGroupNode = destinationGraph:copyFromGraph(geoGroupNode.graphOwner, {geoGroupNode})[1]
  destinationGeoGroupNode:setAttribute(octane.A_PIN_COUNT, #arg + 1)
  destinationGeoGroupNode:connectToIx(#arg + 1, destinationGeometry)
  destinationRenderTarget:connectTo(octane.P_MESH, destinationGeoGroupNode)
end

-- Function to clean up the scene graph and save the combined scene
-- @param saveAsScene The path where the combined scene will be saved
local function cleanUpAndSave(saveAsScene)
  octane.project.getSceneGraph():findFirstNode(octane.NT_RENDERTARGET):deleteUnconnectedItems()
  octane.project.getSceneGraph():unfold()
  print(string.format("Saving combined scene as %s", saveAsScene))
  octane.project.saveAs(saveAsScene)
end

-- Main function serving as the entry point of the script
local function main()
  -- Retrieve the command line arguments
  local saveAsScene = arg[1]       -- The path where the combined scene will be saved
  local destinationScene = arg[2]  -- The path to the destination scene file
  local sourceScenes = {unpack(arg, 3)}  -- Table containing the paths to the source scene files
  
  -- Check if the required arguments are provided
  if not checkRequiredArguments(saveAsScene, destinationScene) then
    return
  end

  -- Check if at least one source scene is provided
  if #sourceScenes == 0 then
    print("At least one source scene required as an -A script argument.")
    return
  end

  -- Create a temporary node graph and a geometry group node
  local tempGraph, geoGroupNode = createTemporaryGraph()
  
  -- Process each source scene file and combine their geometries
  processSourceScenes(sourceScenes, geoGroupNode)
  
  -- Combine the processed source scenes with the destination scene
  combineScenes(destinationScene, geoGroupNode)
  
  -- Clean up the scene graph and save the combined scene
  cleanUpAndSave(saveAsScene)
end

-- Call the main function to start the script execution
main()