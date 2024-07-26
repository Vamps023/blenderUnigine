# Blender to Unigine .Mesh File Exporter

This Blender add - on allows you to
export Blender meshes to the Unigine.mesh file format, making it easier to integrate Blender models into Unigine projects.

# # Installation

1. Open Blender.
2. Navigate to `Edit` > `Preferences` > `Add-ons`.
3. Click on the `Install...`
button.
4. Select the file `unigineExport.py`
and install the add - on.
5. Copy the `Bl_Unigine`
folder into your `C`
drive.

# # Usage

1. Ensure the Unigine Exporter add - on is enabled in Blender.
2. Select the mesh(es) you want to
export.
3. Choose a destination folder and specify the file name.
4. Click `Export`.


Certainly! Let's break down the Blender add-on code into even more detailed sections, explaining the purpose and functionality of each part.

## Add-on Metadata
The `bl_info` dictionary contains metadata about the add-on. This information is displayed in Blender's add-on manager.
```python
bl_info = {
    "name": "Unigine Import-Export",
    "blender": (4, 0, 2),
    "category": "Object",
    "author": "Vamps(Swapnil)",
    "version": (4, 0),
    "description": "Import and Export from Blender to Unigine",
}
```
- **name**: The name of the add-on.
- **blender**: The version of Blender that the add-on is compatible with.
- **category**: The category under which the add-on will be listed in Blender's add-on manager.
- **author**: The author of the add-on.
- **version**: The version of the add-on.
- **description**: A brief description of what the add-on does.

## Imports
The add-on uses various libraries for its functionality.
```python
import bpy
import os
import tempfile
import subprocess
import shutil
import glob
from bpy.types import Operator, Panel
from bpy.props import StringProperty
import xml.etree.ElementTree as ET
```
- **bpy**: The main Blender Python API module.
- **os**, **tempfile**, **subprocess**, **shutil**, **glob**: Standard Python modules for file and process handling.
- **xml.etree.ElementTree**: A module for parsing XML files, used for processing material files.

## Utility Functions
These functions handle specific tasks required by the add-on.

### `process_mat_file`
Parses a `.mat` file to extract the material name and GUID.
```python
def process_mat_file(file_path):
    """Process a single .mat file to extract name and GUID."""
    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
        
        name = root.attrib.get('name')
        guid = root.attrib.get('guid')
        
        return name, guid
    except Exception as e:
        print(f"Error processing file {file_path}: {e}")
        return None, None
```
- **file_path**: Path to the `.mat` file.
- **tree**: An ElementTree object representing the XML tree of the file.
- **root**: The root element of the XML tree.
- **name** and **guid**: Attributes extracted from the root element.

### `generate_guid_mapping`
Generates a GUID mapping file from `.mat` files found in the specified base path.
```python
def generate_guid_mapping(base_path, output_file):
    """Generate a GUID mapping file from .mat files."""
    guid_mapping = {}
    
    for root_dir, _, files in os.walk(base_path):
        for file_name in files:
            if file_name.endswith(".mat"):
                file_path = os.path.join(root_dir, file_name)
                name, guid = process_mat_file(file_path)
                
                if name and guid:
                    guid_mapping[name] = guid
    
    with open(output_file, "w") as f:
        for name, guid in guid_mapping.items():
            f.write(f'"{name}" : "{guid}"\n')
    
    print(f"GUID mapping generated and saved to {output_file}")
```
- **base_path**: The directory to search for `.mat` files.
- **output_file**: The file to save the GUID mappings.
- **guid_mapping**: A dictionary to store the mappings of material names to GUIDs.
- **os.walk(base_path)**: Iterates through the directory tree rooted at `base_path`.

### `load_guid_mappings`
Loads GUID mappings from a specified file.
```python
def load_guid_mappings(guid_mapping_file):
    """Load GUID mappings from the GUID_MAPPING_FILE."""
    guid_mappings = {}
    if os.path.exists(guid_mapping_file):
        with open(guid_mapping_file, "r") as f:
            for line in f:
                parts = line.strip().split(' : ')
                if len(parts) == 2:
                    name, guid = parts
                    guid_mappings[name.strip('"')] = guid.strip('"')
    return guid_mappings
```
- **guid_mapping_file**: The file containing the GUID mappings.
- **guid_mappings**: A dictionary to store the loaded mappings.

### `export_to_fbx`
Exports selected Blender objects to an FBX file.
```python
def export_to_fbx(filepath, global_scale=0.01):
    """Export the selected scene objects to an FBX file."""
    export_path = r"C:\Bl_Unigine"
    os.makedirs(export_path, exist_ok=True)
    export_filepath = os.path.join(export_path, os.path.basename(filepath))

    try:
        bpy.ops.export_scene.fbx(
            filepath=export_filepath,
            check_existing=True,
            filter_glob="*.fbx",
            use_selection=True,
            use_active_collection=False,
            global_scale=global_scale,
            apply_unit_scale=True,
            apply_scale_options='FBX_SCALE_ALL',
            bake_space_transform=True,
            object_types={'MESH'},
            use_mesh_modifiers=True,
            use_mesh_modifiers_render=True,
            mesh_smooth_type='OFF',
            use_mesh_edges=False,
            use_tspace=False,
            use_custom_props=False,
            add_leaf_bones=False,
            primary_bone_axis='Y',
            secondary_bone_axis='X',
            use_armature_deform_only=False,
            armature_nodetype='NULL',
            bake_anim=False,
            bake_anim_use_all_bones=False,
            bake_anim_use_nla_strips=False,
            bake_anim_use_all_actions=False,
            bake_anim_force_startend_keying=False,
            bake_anim_step=1,
            bake_anim_simplify_factor=1,
            path_mode='AUTO',
            embed_textures=False,
            batch_mode='OFF',
            use_batch_own_dir=True,
            use_metadata=True,
            axis_forward='Y',
            axis_up='Z'
        )
        print("FBX export successful.")
    except Exception as e:
        print(f"FBX export failed: {e}")
        raise e

    move_latest_mesh_file(export_path)
    return export_filepath
```
- **filepath**: The path where the FBX file will be saved.
- **global_scale**: The scale factor for the export.
- **bpy.ops.export_scene.fbx**: Blender's operator for exporting to FBX.
- **export_path**: Directory for the export.
- **export_filepath**: Full path for the exported FBX file.

### `move_latest_mesh_file`
Moves the latest `.mesh` file to the destination folder and creates a `.node` file.
```python
def move_latest_mesh_file(export_path):
    """Move the latest .mesh file to the destination folder and create a .node file."""
    mesh_files = glob.glob(os.path.join(export_path, '*.mesh'))
    if mesh_files:
        latest_mesh_file = max(mesh_files, key=os.path.getmtime)
        destination_folder = bpy.context.scene.mesh_destination_folder
        os.makedirs(destination_folder, exist_ok=True)
        new_mesh_name = bpy.context.scene.new_mesh_name + ".mesh"
        new_node_name = bpy.context.scene.new_mesh_name + ".node"

        try:
            shutil.move(latest_mesh_file, os.path.join(destination_folder, new_mesh_name))
            print(f"Moved {latest_mesh_file} to {os.path.join(destination_folder, new_mesh_name)}.")
            create_node_file(destination_folder, new_mesh_name, new_node_name)
        except Exception as e:
            print(f"Failed to move mesh file: {e}")
            raise e
    else:
        print("No .mesh files found to move.")
```
- **export_path**: Directory where the `.mesh` files are located.
- **mesh_files**: List of `.mesh` files in the export directory.
- **latest_mesh_file**: The most recently modified `.mesh` file.
- **destination_folder**: Folder to move the `.mesh` file to.
- **new_mesh_name** and **new_node_name**: Names for the moved `.mesh` file and the created `.node` file.

### `create_node_file`
Creates a `.node` file with the appropriate surface GUIDs.
```python
def create_node_file(destination_folder, mesh_name, node_name):
    """Create a .node file with the appropriate surface GUIDs."""
    mesh_path = os.path.join(destination_folder, mesh_name).replace("\\", "/")
    
    # Update mesh_path if it contains the specific path
    specific_path = "C:/ALL_SVN/INRSW9TrainSim/trunk/content/worlds/"
    if specific_path in mesh_path:
        mesh_path = "../worlds/" + mesh_path.split("/worlds/")[1]

    object_name = bpy.context.scene.new_mesh_name
    surfaces = []

    for obj in bpy.context.selected_objects:
        if obj.type == 'MESH':
            surface_name = obj.name
            guid = bpy.context.scene.surface_guids.get(surface_name, "default_guid")
            surfaces.append(f'<surface name="{surface_name}" material="{guid}" property="surface_base"/>')

    surfaces_str = "\n\t\t".join(surfaces)

    node_content = f"""<?xml version="1.0" encoding="utf-8"?>
<nodes version="2.5.0.2">
    <node type="ObjectMeshStatic" id="268616936" name="{object_name}">
        <mesh_name>{mesh_path}</mesh_name>
        {surfaces_str}
        <transform>0.999999940395 0 0 0.

000000000000 -0.000000010282 0.999999642372 0.000785398236 0.000000000000 0 -0.000785398236 0.999999642372 0 0 0 0 1</transform>
    </node>
</nodes>"""

    try:
        with open(os.path.join(destination_folder, node_name), "w") as f:
            f.write(node_content)
        print(f"Created .node file at {os.path.join(destination_folder, node_name)}.")
    except Exception as e:
        print(f"Failed to create .node file: {e}")
        raise e
```
- **destination_folder**: Folder to save the `.node` file.
- **mesh_name** and **node_name**: Names for the mesh and node files.
- **mesh_path**: Path to the `.mesh` file.
- **object_name**: Name of the Blender object.
- **surfaces**: List of surface definitions for the `.node` file.
- **node_content**: The content of the `.node` file.

## Operator Classes
These classes define the custom operators for the add-on.

### `Blender_OT_Export`
Handles exporting selected objects to Unigine by converting them to FBX.
```python
class Blender_OT_Export(Operator):
    bl_idname = "blender.export"
    bl_label = "Export to Unigine"
    bl_description = "Export selected objects to Unigine"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        new_mesh_name = context.scene.new_mesh_name + ".fbx"
        export_filepath = export_to_fbx(new_mesh_name)

        meshimport_exe = r"C:\Bl_Unigine\meshimport_x64.exe"
        if not os.path.exists(meshimport_exe):
            self.report({'ERROR'}, f"Executable not found at '{meshimport_exe}'")
            return {'CANCELLED'}

        command = [meshimport_exe, export_filepath]
        try:
            subprocess.run(command, check=True)
            self.report({'INFO'}, f'Shell command executed: {" ".join(command)}')
            print(f"Shell command executed: {' '.join(command)}")
        except subprocess.CalledProcessError as e:
            self.report({'ERROR'}, f'Shell command failed: {e}')
            print(f'Shell command failed: {e}')
            return {'CANCELLED'}

        return {'FINISHED'}
```
- **bl_idname**: Unique identifier for the operator.
- **bl_label**: The label for the operator.
- **bl_description**: A brief description of what the operator does.
- **bl_options**: Options for the operator.
- **execute(self, context)**: The function called when the operator is executed.
- **new_mesh_name**: The name for the new mesh.
- **export_filepath**: The path where the FBX file will be saved.
- **meshimport_exe**: Path to the meshimport executable.
- **command**: The command to execute the meshimport tool.

### `Blender_OT_Import`
Handles importing `.mesh` files by converting them to `.obj`.
```python
class Blender_OT_Import(Operator):
    bl_idname = "blender.import"
    bl_label = "Import from Unigine"
    bl_description = "Import .mesh file by converting it to .obj"
    bl_options = {'REGISTER', 'UNDO'}
    
    filepath: StringProperty(subtype="FILE_PATH")

    def execute(self, context):
        mesh_filepath = self.filepath
        output_filepath = r"C:\Bl_Unigine\Import\import.obj"
        os.makedirs(os.path.dirname(output_filepath), exist_ok=True)

        meshimport_exe = r"C:\Bl_Unigine\meshimport_x64.exe"
        if not os.path.exists(meshimport_exe):
            self.report({'ERROR'}, f"Executable not found at '{meshimport_exe}'")
            return {'CANCELLED'}

        command = [meshimport_exe, mesh_filepath, "-o", output_filepath]
        try:
            subprocess.run(command, check=True)
            self.report({'INFO'}, f'Converted {mesh_filepath} to {output_filepath}')
        except subprocess.CalledProcessError as e:
            self.report({'ERROR'}, f'Conversion command failed: {e}')
            return {'CANCELLED'}

        try:
            bpy.ops.wm.obj_import(filepath=output_filepath)
            self.report({'INFO'}, 'Imported .obj file into Blender')
            
            imported_objects = [obj for obj in context.selected_objects if obj.type == 'MESH']
            for obj in imported_objects:
                obj.rotation_euler[0] = 0

        except Exception as e:
            self.report({'ERROR'}, f'Importing .obj file failed: {e}')
            return {'CANCELLED'}

        return {'FINISHED'}

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}
```
- **filepath**: The path to the `.mesh` file to import.
- **mesh_filepath**: The path to the `.mesh` file.
- **output_filepath**: The path where the `.obj` file will be saved.
- **command**: The command to execute the meshimport tool.
- **bpy.ops.wm.obj_import**: Blender's operator for importing `.obj` files.
- **invoke(self, context, event)**: The function called when the operator is invoked.

### `SetDestinationFolderOperator`
Sets the destination folder for the exported `.mesh` file.
```python
class SetDestinationFolderOperator(Operator):
    bl_idname = "mesh.set_destination_folder"
    bl_label = "Set Destination Folder"
    bl_description = "Set the destination folder for the exported .mesh file"

    filepath: bpy.props.StringProperty(subtype="DIR_PATH")

    def execute(self, context):
        context.scene.mesh_destination_folder = self.filepath
        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}
```
- **bl_idname**: Unique identifier for the operator.
- **bl_label**: The label for the operator.
- **bl_description**: A brief description of what the operator does.
- **filepath**: The path to the destination folder.
- **execute(self, context)**: The function called when the operator is executed.
- **invoke(self, context, event)**: The function called when the operator is invoked.

### `FetchMATDataOperator`
Fetches material data from `.mat` files and generates GUID mapping.
```python
class FetchMATDataOperator(Operator):
    bl_idname = "mesh.fetch_mat_data"
    bl_label = "Fetch MAT Data"
    bl_description = "Fetch material data from .mat files and generate GUID mapping"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        project_name = context.scene.project_name
        base_path = fr"C:\ALL_SVN\{project_name}\trunk\content\worlds"
        output_folder = r"C:\Bl_Unigine"
        guid_mapping_file = os.path.join(output_folder, f"{project_name}_surface_guid_mapping.txt")

        os.makedirs(output_folder, exist_ok=True)

        try:
            generate_guid_mapping(base_path, guid_mapping_file)
            global SURFACE_GUIDS
            SURFACE_GUIDS = load_guid_mappings(guid_mapping_file)
            self.report({'INFO'}, f'GUID mapping generated and updated.')
            print(f"GUID mapping generated and updated at {guid_mapping_file}.")
        except Exception as e:
            self.report({'ERROR'}, f'Failed to generate GUID mapping: {e}')
            print(f"Failed to generate GUID mapping: {e}")
            return {'CANCELLED'}
        
        return {'FINISHED'}
```
- **bl_idname**: Unique identifier for the operator.
- **bl_label**: The label for the operator.
- **bl_description**: A brief description of what the operator does.
- **bl_options**: Options for the operator.
- **execute(self, context)**: The function called when the operator is executed.
- **project_name**: The name of the project.
- **base_path**: The base directory for the project.
- **output_folder**: The folder where the GUID mapping file will be saved.
- **guid_mapping_file**: The file to save the GUID mappings.

## User Interface (UI) Panel
Defines the UI panel in the 3D view for the Unigine export tool.
```python
class VIEW3D_PT_Blender(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Unigine Tool'
    bl_label = "Unigine Export"

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        # Project settings
        box = layout.column(align=True)

        box = layout.box()
        box.label(text="Project Name And Fetch Mat Data:")
        box.prop(scene, "project_name", text="Project Name")

        box.operator('mesh.fetch_mat_data', icon='FILE_REFRESH', text="Fetch MAT Data")
        box.separator()

        # Mesh Destination
        box = layout.box()
        box.label(text="Mesh Destination:")
        box = box.box()
        row = box.row(align=True)
        
        # Display the folder path with a small folder icon button
        box = layout.box()
        row.prop(scene, "mesh_destination_folder", text="Destination Folder", emboss=True,)

        if scene.show_mesh_dest:
            box.prop(scene, "mesh_destination_folder", text="

Destination Folder")
        
        # Operator to set destination folder
        box.operator('mesh.set_destination_folder', icon='FILE_FOLDER', text="Set Destination Folder")
        box.separator()

        # New Mesh Name
        box = layout.box()
        box.label(text="New Mesh Name:")
        box.prop(scene, "new_mesh_name", text="")

        # Export button
        box = layout.box()
        box.operator('blender.export', icon='EXPORT', text="Export")

        # Import button
        box = layout.box()
        box.operator('blender.import', icon='IMPORT', text="Import")

        box.separator()
        box.separator()
```
- **bl_space_type**: Specifies that the panel will be in the 3D View.
- **bl_region_type**: Specifies that the panel will be in the UI region.
- **bl_category**: The category under which the panel will be listed.
- **bl_label**: The label for the panel.
- **draw(self, context)**: The function called to draw the panel.
- **layout**: The layout object for adding UI elements.
- **scene**: The current scene.

## Property Definitions
Defines the custom properties for the Blender scene.
```python
def register():
    bpy.utils.register_class(Blender_OT_Export)
    bpy.utils.register_class(Blender_OT_Import)
    bpy.utils.register_class(SetDestinationFolderOperator)
    bpy.utils.register_class(FetchMATDataOperator)
    bpy.utils.register_class(VIEW3D_PT_Blender)

    bpy.types.Scene.mesh_destination_folder = bpy.props.StringProperty(
        name="Destination Folder",
        description="Folder for exported .mesh file",
        default="",
        subtype='DIR_PATH'
    )
    
    bpy.types.Scene.new_mesh_name = bpy.props.StringProperty(
        name="New Mesh Name",
        description="Name for the new mesh",
        default="NewMesh"
    )

    bpy.types.Scene.surface_guids = {}

    bpy.types.Scene.project_name = bpy.props.StringProperty(
        name="Project Name",
        description="Name of the project",
        default=""
    )

def unregister():
    bpy.utils.unregister_class(Blender_OT_Export)
    bpy.utils.unregister_class(Blender_OT_Import)
    bpy.utils.unregister_class(SetDestinationFolderOperator)
    bpy.utils.unregister_class(FetchMATDataOperator)
    bpy.utils.unregister_class(VIEW3D_PT_Blender)
    
    del bpy.types.Scene.mesh_destination_folder
    del bpy.types.Scene.new_mesh_name
    del bpy.types.Scene.surface_guids
    del bpy.types.Scene.project_name
```
- **register()**: Registers the classes and properties with Blender.
- **unregister()**: Unregisters the classes and properties from Blender.
- **bpy.utils.register_class**: Registers a class with Blender.
- **bpy.utils.unregister_class**: Unregisters a class from Blender.
- **bpy.types.Scene.mesh_destination_folder**: Property for the destination folder.
- **bpy.types.Scene.new_mesh_name**: Property for the new mesh name.
- **bpy.types.Scene.surface_guids**: Dictionary to store surface GUIDs.
- **bpy.types.Scene.project_name**: Property for the project name.

---

This detailed breakdown explains each part of the add-on code, making it easier to understand the purpose and functionality of the various sections and functions.


# # Resources

For more information on the Unigine.mesh file format and related tools, please refer to the[Unigine documentation](https: //developer.unigine.com/en/docs/2.6.1/tools/mesh_import/?rlang=cs&autotranslate=en).

        # # Credits

        This add - on is based on the code and logic provided in the Unigine documentation.

        # # License This software is distributed under the[MIT License](LICENSE).
