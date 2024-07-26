bl_info = {
    "name": "Unigine Import-Export",
    "blender": (4, 0, 2),
    "category": "Object",
    "author": "Vamps(Swapnil)",
    "version": (4, 0),
    "description": "Import and Export from Blender to Unigine",
}

import bpy
import os
import tempfile
import subprocess
import shutil
import glob
from bpy.types import Operator, Panel
from bpy.props import StringProperty
import xml.etree.ElementTree as ET

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
        <transform>0.999999940395 0 0 0.0 0 0.999999940395 0 0.0 0 0 0.999999940395 0.0 0 0 0 1.0</transform>
    </node>
</nodes>"""

    node_file_path = os.path.join(destination_folder, node_name)
    try:
        with open(node_file_path, "w") as node_file:
            node_file.write(node_content)
        print(f"Node file created at {node_file_path}")
    except Exception as e:
        print(f"Failed to create node file: {e}")
        raise e

class Blender_OT_Export(Operator):
    bl_idname = "blender.export"
    bl_label = "Export to Blender"
    bl_description = "Export model to another Blender instance"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context):
        filepath = os.path.join(tempfile.gettempdir(), "Blender_TMP.fbx")
        try:
            export_filepath = export_to_fbx(filepath)
            self.report({'INFO'}, 'Blender - Export Done!')
            print("Export to FBX done.")
        except Exception as e:
            self.report({'ERROR'}, f'Export failed: {e}')
            print(f"Export to FBX failed: {e}")
            return {'CANCELLED'}

        meshimport_exe = r"C:\Bl_Unigine\meshimport_x64.exe"
        if not os.path.exists(meshimport_exe):
            self.report({'ERROR'}, f"Executable not found at '{meshimport_exe}'")
            print(f"Executable not found at '{meshimport_exe}'")
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
            box.prop(scene, "mesh_destination_folder", text="Destination Folder")
            box.separator()

        # Export and Import
        
        box.label(text="Export / Import:")
        box.prop(scene, "new_mesh_name", text="New Mesh Name")
        box.operator('blender.export', icon='EXPORT', text="Export to Unigine")
        box.operator('blender.import', icon='IMPORT', text="Import .mesh file")
        box.separator()

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

        # Ensure the output folder exists
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

# Registration

classes = (
    Blender_OT_Export,
    VIEW3D_PT_Blender,
    SetDestinationFolderOperator,
    Blender_OT_Import,
    FetchMATDataOperator,
)

def register():
    bpy.types.Scene.mesh_destination_folder = StringProperty(
        name="Mesh Destination Folder",
        default="C:/DestinationFolder",
        description="Folder where the latest .mesh file will be moved"
    )
    bpy.types.Scene.new_mesh_name = StringProperty(
        name="New Mesh Name",
        default="new_mesh",
        description="New name for the .mesh file"
    )
    bpy.types.Scene.project_name = StringProperty(
        name="Project Name",
        default="INRSW9TrainSim",
        description="Project Name for the MAT Data"
    )
    bpy.types.Scene.show_mesh_dest = bpy.props.BoolProperty(
        name="Show Mesh Destination",
        default=False
    )
    bpy.types.Scene.mesh_destination_folder = bpy.props.StringProperty(
        name="Destination Folder",
        default="",
        subtype='DIR_PATH'
    )

    for cls in classes:
        bpy.utils.register_class(cls)
    print("Unigine Export add-on registered.")

def unregister():
    del bpy.types.Scene.mesh_destination_folder
    del bpy.types.Scene.new_mesh_name
    del bpy.types.Scene.project_name
    del bpy.types.Scene.show_mesh_dest
    del bpy.types.Scene.mesh_destination_folder
    
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
    print("Unigine Export add-on unregistered.")

if __name__ == "__main__":
    register()
