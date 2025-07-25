# Blender Operator Generator Example

This document shows how to use the new `create_bpy_operator` MCP tool to generate Blender operator boilerplate code.

## Basic Usage

```python
# Via MCP tool call
result = await create_bpy_operator(
    name="My Custom Operator",
    description="This operator does something useful"
)
```

## Advanced Usage with Properties

```python
# With properties and additional methods
result = await create_bpy_operator(
    name="Advanced Tool",
    description="An advanced operator with properties and methods",
    category="MESH",
    include_invoke=True,
    include_poll=True,
    properties=[
        {
            "name": "scale_factor",
            "type": "FloatProperty",
            "description": "Scale factor for the operation",
            "default": 1.0
        },
        {
            "name": "use_selection",
            "type": "BoolProperty", 
            "description": "Apply to selected objects only",
            "default": True
        },
        {
            "name": "axis",
            "type": "EnumProperty",
            "description": "Axis to operate on",
            "options": ["HIDDEN"]
        }
    ],
    output_file="my_custom_operator.py"
)
```

## Generated Output Structure

The tool generates a complete Blender operator file with:

- **Proper imports**: `bpy`, `bpy.types.Operator`, and any property types
- **Class definition**: Follows Blender naming conventions
- **Blender attributes**: `bl_idname`, `bl_label`, `bl_description`, `bl_options`
- **Properties**: Type-safe property definitions with descriptions and defaults
- **Methods**: `execute()` (required), plus optional `invoke()`, `poll()`, `modal()`
- **Registration**: Complete `register()` and `unregister()` functions
- **Documentation**: Proper docstrings and type hints

## Example Generated Output

```python
import bpy
from bpy.types import Operator
from bpy.props import FloatProperty, BoolProperty

class AdvancedToolOperator(Operator):
    """An advanced operator with properties and methods."""
    
    bl_idname = "mesh.advanced_tool"
    bl_label = "Advanced Tool" 
    bl_description = "An advanced operator with properties and methods"
    bl_options = {'REGISTER', 'UNDO'}

    # Operator properties
    scale_factor: FloatProperty(name="Scale factor for the operation", description="Scale factor for the operation", default=1.0)
    use_selection: BoolProperty(name="Apply to selected objects only", description="Apply to selected objects only", default=True)

    @classmethod
    def poll(cls, context: bpy.types.Context) -> bool:
        """Check if the operator can be executed."""
        # TODO: Implement poll logic here
        return True

    def invoke(self, context: bpy.types.Context, event: bpy.types.Event) -> set[str]:
        """Invoke the operator."""
        # TODO: Implement invoke logic here
        return self.execute(context)

    def execute(self, context: bpy.types.Context) -> set[str]:
        """Execute the operator."""
        # TODO: Implement your operator logic here
        self.report({'INFO'}, "Advanced Tool executed successfully")
        return {'FINISHED'}

def register():
    """Register the operator."""
    bpy.utils.register_class(AdvancedToolOperator)

def unregister():
    """Unregister the operator."""
    bpy.utils.unregister_class(AdvancedToolOperator)

if __name__ == "__main__":
    register()
```

## Naming Conventions

The tool automatically handles naming conversions:

- **Class Name**: "Add Cube" → `AddCubeOperator`
- **bl_idname**: "Add Cube" + category "MESH" → `"mesh.add_cube"`
- **File Name**: "Add Cube" → `add_cube_operator.py`

## Categories

Common categories and their usage:

- `"OBJECT"` (default): General object operations → `object.operator_name`
- `"MESH"`: Mesh editing operations → `mesh.operator_name`
- `"MATERIAL"`: Material operations → `material.operator_name`
- `"CUSTOM"`: Custom addon operations → `custom.operator_name`

## Property Types

Supported Blender property types:

- `StringProperty`: Text input
- `BoolProperty`: Checkbox
- `IntProperty`: Integer input
- `FloatProperty`: Float input
- `EnumProperty`: Dropdown selection
- `FloatVectorProperty`: Vector input (3D coordinates, colors, etc.)
- `PointerProperty`: Reference to other Blender data
- `CollectionProperty`: Array of properties

## Error Handling

The tool validates inputs and provides helpful error messages:

- Empty names or descriptions are rejected
- Invalid property definitions generate warnings
- File system errors are reported with details
- Generated code follows Python and Blender best practices

## Integration with VS Code

This tool is designed to work seamlessly with VS Code and the MCP protocol:

- Generates files in your workspace
- Follows project structure conventions
- Creates operators directory if needed
- Provides structured output for further processing
