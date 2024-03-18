bl_info = {
    "name": "Unigine Export",
    "blender": (4, 0, 2),
    "category": "Object",
    "author": "Vamps(Swapnil)",
    "version": (1, 0),
    "description": "Export models to another Blender instance and set destination folders for exported mesh files.",
}
 
import bpy
import os
import tempfile
import subprocess
import shutil
import glob
from bpy.types import Operator, Panel
from bpy.props import StringProperty
 
 
def export_to_fbx(filepath, global_scale=0.01):
    export_path = r"C:\Bl_Unigine"
    os.makedirs(export_path, exist_ok=True)
    export_filepath = os.path.join(export_path, os.path.basename(filepath))
 
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
 
    # Move the latest .mesh file to the specified destination folder with the provided new name
    move_latest_mesh_file(export_path)
 
    return export_filepath
 
 
def move_latest_mesh_file(export_path):
    # Check if any .mesh files exist in the export folder
    mesh_files = glob.glob(os.path.join(export_path, '*.mesh'))
    if mesh_files:
        # Get the latest .mesh file
        latest_mesh_file = max(mesh_files, key=os.path.getmtime)
 
        # Define the destination folder to move the latest .mesh file
        destination_folder = bpy.context.scene.mesh_destination_folder
        os.makedirs(destination_folder, exist_ok=True)
 
        # Define the new name for the .mesh file
        new_mesh_name = bpy.context.scene.new_mesh_name + ".mesh"
 
        # Move the latest .mesh file to the destination folder with the new name
        shutil.move(latest_mesh_file, os.path.join(destination_folder, new_mesh_name))
 
 
class Blender_OT_Export(Operator):
    bl_idname = "blender.export"
    bl_label = "Export to Blender"
    bl_description = "Export model to another Blender instance"
    bl_options = {'REGISTER', 'UNDO'}
 
    def execute(self, context):
        filepath = os.path.join(tempfile.gettempdir(), "Blender_TMP.fbx")
        export_filepath = export_to_fbx(filepath)
        self.report({'INFO'}, 'Blender - Export Done!')
 
        # Execute the shell command
        meshimport_exe = r"C:\Bl_Unigine\meshimport_x64.exe"  # Replace this with the actual path
        if not os.path.exists(meshimport_exe):
            self.report({'ERROR'}, f"Executable not found at '{meshimport_exe}'")
            return {'CANCELLED'}
 
        command = [meshimport_exe, export_filepath]
        try:
            subprocess.run(command, check=True)
        except subprocess.CalledProcessError as e:
            self.report({'ERROR'}, f'Shell command failed: {e}')
            return {'CANCELLED'}
        else:
            self.report({'INFO'}, f'Shell command executed: {" ".join(command)}')
 
        return {'FINISHED'}
 
 
class VIEW3D_PT_Blender(Panel):
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Uningine'
    bl_label = "Unigine Export"
 
    def draw(self, context):
        layout = self.layout
        scene = context.scene
 
        col = layout.column(align=True)
        col.operator('blender.export', icon='EXPORT', text="Export to Unigine")
 
        col.prop(scene, "mesh_destination_folder", text="Destination Folder")
        col.prop(scene, "new_mesh_name", text="New Mesh Name")
 
        col.operator("mesh.set_destination_folder", text="Select Destination Folder")
 
 
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
 
 
# Registration
 
classes = (
    Blender_OT_Export,
    VIEW3D_PT_Blender,
    SetDestinationFolderOperator,
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
 
    for cls in classes:
        bpy.utils.register_class(cls)
 
 
def unregister():
    del bpy.types.Scene.mesh_destination_folder
    del bpy.types.Scene.new_mesh_name
 
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)
 
 
if __name__ == "__main__":
    register()
