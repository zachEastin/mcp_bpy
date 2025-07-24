# Addon Development Template

This prompt template assists with Blender addon development tasks.

## Usage

Use this template when developing, debugging, or modifying Blender addons.

## Template

```
**🔧 ADDON DEVELOPMENT REQUEST**

**Task Type:** {{task_type}}
- [ ] Create new addon
- [ ] Debug existing addon
- [ ] Add functionality
- [ ] Fix compatibility
- [ ] Optimize performance

**Addon Details:**
- Name: {{addon_name}}
- Version: {{addon_version}}
- Blender Compatibility: {{blender_versions}}
- Category: {{addon_category}}

**Current State:**
{{addon_current_state}}

**Desired Changes:**
{{change_description}}

**Technical Requirements:**
- Blender Version: {{target_blender}}
- Python Features: {{python_features}}
- UI Requirements: {{ui_requirements}}
- Integration: {{integration_needs}}

**Code Structure Needed:**
```python
bl_info = {
    "name": "{{addon_name}}",
    "blender": {{minimum_blender}},
    "category": "{{category}}",
    # ... other metadata
}

# Class definitions
# Operator classes
# Panel classes
# Property groups
# Registration functions
```

**Specific Questions:**
{{specific_questions}}

**Testing Criteria:**
{{testing_requirements}}

Please provide:
1. 📝 Complete addon code structure
2. 🔧 Implementation details
3. 🧪 Testing instructions
4. 📚 Usage documentation
5. ⚠️ Known limitations or caveats
```

## Parameters

| Parameter | Description | Example |
|-----------|-------------|---------|
| `task_type` | Type of development task | "Create new addon" |
| `addon_name` | Name of the addon | "My Modeling Tools" |
| `addon_version` | Current or target version | "1.0.0" |
| `blender_versions` | Supported Blender versions | "4.0+" |
| `addon_category` | Blender addon category | "Mesh" |
| `addon_current_state` | Current status/code | "Basic structure exists, needs operators" |
| `change_description` | What you want to achieve | "Add UV unwrapping automation" |
| `target_blender` | Target Blender version | "4.2.0" |
| `python_features` | Required Python features | "Type hints, dataclasses" |
| `ui_requirements` | UI/UX needs | "Sidebar panel with presets" |
| `integration_needs` | Integration requirements | "Works with existing modeling workflow" |
| `minimum_blender` | Minimum Blender version | "(4, 0, 0)" |
| `category` | Addon category for bl_info | "Mesh" |
| `specific_questions` | Particular issues/questions | "How to handle operator undo?" |
| `testing_requirements` | How to test the addon | "Test with complex meshes" |

## Quick Development Requests

### New Operator
```
🔧 **New Operator**: {{operator_name}}
🎯 **Function**: {{what_it_does}}
🎨 **UI**: {{where_it_appears}}
📝 **Please provide complete operator class**
```

### Panel Creation
```
🎨 **Panel**: {{panel_name}}
📍 **Location**: {{panel_location}}
🔧 **Controls**: {{ui_elements}}
📝 **Please provide panel class**
```

### Property System
```
⚙️ **Properties**: {{property_group_name}}
📊 **Data**: {{property_types}}
🔗 **Usage**: {{how_properties_used}}
📝 **Please provide property group**
```

### Registration
```
🔄 **Register**: {{classes_to_register}}
⚠️ **Dependencies**: {{required_modules}}
🧪 **Validation**: {{registration_checks}}
📝 **Please provide register/unregister functions**
```
