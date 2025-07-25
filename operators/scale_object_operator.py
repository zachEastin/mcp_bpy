import bpy
from bpy.types import Operator
from bpy.props import BoolProperty, FloatProperty


class ScaleObjectOperator(Operator):
    """Scaleanobject."""
    
    bl_idname = "object.scale_object"
    bl_label = "Scale Object"
    bl_description = "Scale an object"
    bl_options = {'REGISTER', 'UNDO'}

    # Operator properties
    scale_factor: FloatProperty(name="Scale factor", description="Scale factor", default=1.0)
    use_smooth: BoolProperty(name="Use smooth shading", description="Use smooth shading", default=True)

    def execute(self, context: bpy.types.Context) -> set[str]:
        """Execute the operator.
        
        Args:
            context: Blender context
            
        Returns:
            set[str]: Execution result (FINISHED, CANCELLED, etc.)
        """
        # TODO: Implement your operator logic here
        self.report({'INFO'}, "Scale Object executed successfully")
        return {'FINISHED'}

def register():
    """Register the operator."""
    bpy.utils.register_class(ScaleObjectOperator)


def unregister():
    """Unregister the operator."""
    bpy.utils.unregister_class(ScaleObjectOperator)


if __name__ == "__main__":
    register()