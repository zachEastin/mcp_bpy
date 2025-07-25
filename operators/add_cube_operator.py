import bpy
from bpy.types import Operator


class AddCubeOperator(Operator):
    """Addacubetothescene."""
    
    bl_idname = "mesh.add_cube"
    bl_label = "Add Cube"
    bl_description = "Add a cube to the scene"
    bl_options = {'REGISTER', 'UNDO'}

    def execute(self, context: bpy.types.Context) -> set[str]:
        """Execute the operator.
        
        Args:
            context: Blender context
            
        Returns:
            set[str]: Execution result (FINISHED, CANCELLED, etc.)
        """
        # TODO: Implement your operator logic here
        self.report({'INFO'}, "Add Cube executed successfully")
        return {'FINISHED'}

def register():
    """Register the operator."""
    bpy.utils.register_class(AddCubeOperator)


def unregister():
    """Unregister the operator."""
    bpy.utils.unregister_class(AddCubeOperator)


if __name__ == "__main__":
    register()