# Blender Operation Template

This prompt template helps generate proper Blender Python code for common operations.

## Usage

Use this template when you need help creating Blender Python code for specific tasks.

## Template

```
**🎨 BLENDER CODE REQUEST**

**Task:** {{task_description}}

**Context:**
- Blender Version: {{blender_version}}
- Current Scene: {{scene_name}}
- Available Objects: {{object_list}}
- Active Object: {{active_object}}

**Requirements:**
{{requirements_list}}

**Constraints:**
{{constraints_list}}

**Expected Output:**
- Result: {{expected_result}}
- Format: {{output_format}}

**Code Quality Requirements:**
- ✅ Use modern Blender 4.x+ API
- ✅ Include error handling
- ✅ Add helpful comments
- ✅ Follow Blender Python conventions
- ✅ Test for object existence before operations
- ✅ Use context managers where appropriate

**Example Structure Needed:**
```python
import bpy
import bmesh

# Your code here with:
# 1. Input validation
# 2. Main operation
# 3. Error handling
# 4. Result verification
```

Please provide complete, working Python code that can be executed via `run_python()`.
```

## Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `task_description` | What you want to accomplish | "Create a procedural building with windows" |
| `blender_version` | Current Blender version | "4.2.0" |
| `scene_name` | Active scene name | "Scene" |
| `object_list` | List of available objects | "Cube, Camera, Light" |
| `active_object` | Currently selected object | "Cube" or "None" |
| `requirements_list` | Specific requirements | "- Must use geometry nodes\n- Should be parametric" |
| `constraints_list` | Limitations or restrictions | "- No external addons\n- Keep under 100 lines" |
| `expected_result` | What should be created/modified | "A 10-story building with glass windows" |
| `output_format` | How results should be returned | "Print object names and vertex counts" |

## Quick Request Examples

### Modeling
```
🎨 **Create**: {{object_type}}
📐 **Size**: {{dimensions}}
📍 **Location**: {{position}}
🔧 **Please provide Blender Python code**
```

### Animation
```
🎬 **Animate**: {{target_object}}
⏱️ **Duration**: {{frame_range}}
🎯 **Motion**: {{animation_type}}
🔧 **Please provide keyframe code**
```

### Materials
```
🎨 **Material**: {{material_name}}
🎯 **Apply to**: {{target_objects}}
🌟 **Properties**: {{material_properties}}
🔧 **Please provide shader node code**
```
