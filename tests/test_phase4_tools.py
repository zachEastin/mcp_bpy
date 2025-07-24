"""Test the Phase 4 introspection and helper tools."""

import pytest
from unittest.mock import patch

from bpy_mcp.server import inspect_addon, list_objects, reload_addon
from bpy_mcp.server import AddonInspectionResult, AddonReloadResult, ObjectListResult


class TestListObjects:
    """Test the list_objects tool."""

    @pytest.mark.asyncio
    async def test_list_objects_no_filter(self):
        """Test listing all objects without type filter."""
        # Mock the run_python function
        with patch('bpy_mcp.server.run_python') as mock_run_python:
            mock_output = (
                'RESULT:{"objects": [{"name": "Cube", "type": "MESH", '
                '"data_path": "bpy.data.objects[\'Cube\']", "active": true, '
                '"visible": true, "location": [0.0, 0.0, 0.0]}], '
                '"total_count": 1, "filtered_type": null}'
            )
            mock_run_python.return_value = {
                'output': mock_output,
                'error': None
            }

            result = await list_objects()

            assert isinstance(result, ObjectListResult)
            assert result.total_count == 1
            assert len(result.objects) == 1
            assert result.objects[0].name == "Cube"
            assert result.objects[0].type == "MESH"
            assert result.filtered_type is None

    @pytest.mark.asyncio
    async def test_list_objects_with_filter(self):
        """Test listing objects with type filter."""
        with patch('bpy_mcp.server.run_python') as mock_run_python:
            mock_output = (
                'RESULT:{"objects": [{"name": "Camera", "type": "CAMERA", '
                '"data_path": "bpy.data.objects[\'Camera\']", "active": false, '
                '"visible": true, "location": [7.358, -6.926, 4.958]}], '
                '"total_count": 1, "filtered_type": "CAMERA"}'
            )
            mock_run_python.return_value = {
                'output': mock_output,
                'error': None
            }

            result = await list_objects(type="CAMERA")

            assert isinstance(result, ObjectListResult)
            assert result.total_count == 1
            assert result.filtered_type == "CAMERA"
            assert result.objects[0].type == "CAMERA"

    @pytest.mark.asyncio
    async def test_list_objects_empty_scene(self):
        """Test listing objects in empty scene."""
        with patch('bpy_mcp.server.run_python') as mock_run_python:
            mock_output = (
                'RESULT:{"objects": [], "total_count": 0, "filtered_type": null}'
            )
            mock_run_python.return_value = {
                'output': mock_output,
                'error': None
            }

            result = await list_objects()

            assert isinstance(result, ObjectListResult)
            assert result.total_count == 0
            assert len(result.objects) == 0


class TestInspectAddon:
    """Test the inspect_addon tool."""

    @pytest.mark.asyncio
    async def test_inspect_addon_enabled(self):
        """Test inspecting an enabled addon."""
        with patch('bpy_mcp.server.run_python') as mock_run_python:
            mock_output = (
                'RESULT:{"addon_name": "bpy_mcp_addon", "enabled": true, '
                '"version": "1.0.0", "operators": [{"bl_idname": "bpy_mcp.start_server", '
                '"bl_label": "Start MCP Server", "bl_description": "Start the MCP server", '
                '"bl_category": null}], "classes": [{"name": "BPY_MCP_OT_start_server", '
                '"type": "Operator", "bl_idname": "bpy_mcp.start_server", '
                '"bl_label": "Start MCP Server"}], "keymaps": [], '
                '"properties": ["host", "port", "require_token"]}'
            )
            mock_run_python.return_value = {
                'output': mock_output,
                'error': None
            }

            result = await inspect_addon("bpy_mcp_addon")

            assert isinstance(result, AddonInspectionResult)
            assert result.addon_name == "bpy_mcp_addon"
            assert result.enabled is True
            assert result.version == "1.0.0"
            assert len(result.operators) == 1
            assert result.operators[0].bl_idname == "bpy_mcp.start_server"

    @pytest.mark.asyncio
    async def test_inspect_addon_not_found(self):
        """Test inspecting a non-existent addon."""
        with patch('bpy_mcp.server.run_python') as mock_run_python:
            mock_output = (
                'RESULT:{"addon_name": "nonexistent_addon", "enabled": false, '
                '"version": null, "operators": [], "classes": [], "keymaps": [], '
                '"properties": []}'
            )
            mock_run_python.return_value = {
                'output': mock_output,
                'error': None
            }

            result = await inspect_addon("nonexistent_addon")

            assert isinstance(result, AddonInspectionResult)
            assert result.addon_name == "nonexistent_addon"
            assert result.enabled is False
            assert result.version is None
            assert len(result.operators) == 0


class TestReloadAddon:
    """Test the reload_addon tool."""

    @pytest.mark.asyncio
    async def test_reload_specific_addon(self):
        """Test reloading a specific addon."""
        with patch('bpy_mcp.server.run_python') as mock_run_python:
            mock_output = (
                'RESULT:{"addon_name": "bpy_mcp_addon", "global_reload": false, '
                '"success": true, "reloaded_modules": ["bpy_mcp_addon", '
                '"bpy_mcp_addon.listener"], "errors": []}'
            )
            mock_run_python.return_value = {
                'output': mock_output,
                'error': None
            }

            result = await reload_addon("bpy_mcp_addon")

            assert isinstance(result, AddonReloadResult)
            assert result.addon_name == "bpy_mcp_addon"
            assert result.global_reload is False
            assert result.success is True
            assert len(result.reloaded_modules) == 2
            assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_reload_global(self):
        """Test global script reload."""
        with patch('bpy_mcp.server.run_python') as mock_run_python:
            mock_output = (
                'RESULT:{"addon_name": null, "global_reload": true, "success": true, '
                '"reloaded_modules": ["bpy", "bmesh", "mathutils"], "errors": []}'
            )
            mock_run_python.return_value = {
                'output': mock_output,
                'error': None
            }

            result = await reload_addon()

            assert isinstance(result, AddonReloadResult)
            assert result.addon_name is None
            assert result.global_reload is True
            assert result.success is True
            assert len(result.reloaded_modules) > 0

    @pytest.mark.asyncio
    async def test_reload_with_errors(self):
        """Test reload with errors."""
        with patch('bpy_mcp.server.run_python') as mock_run_python:
            mock_output = (
                'RESULT:{"addon_name": "broken_addon", "global_reload": false, '
                '"success": false, "reloaded_modules": [], '
                '"errors": ["Failed to reload module broken_addon: SyntaxError"]}'
            )
            mock_run_python.return_value = {
                'output': mock_output,
                'error': None
            }

            result = await reload_addon("broken_addon")

            assert isinstance(result, AddonReloadResult)
            assert result.success is False
            assert len(result.errors) == 1
            assert "SyntaxError" in result.errors[0]


class TestToolIntegration:
    """Test integration between tools."""

    @pytest.mark.asyncio
    async def test_workflow_inspect_then_reload(self):
        """Test a typical workflow: inspect an addon, then reload it."""
        with patch('bpy_mcp.server.run_python') as mock_run_python:
            # First call - inspect addon
            mock_output_1 = (
                'RESULT:{"addon_name": "test_addon", "enabled": true, '
                '"version": "1.0.0", "operators": [], "classes": [], '
                '"keymaps": [], "properties": []}'
            )
            mock_run_python.return_value = {
                'output': mock_output_1,
                'error': None
            }

            inspect_result = await inspect_addon("test_addon")
            assert inspect_result.enabled is True

            # Second call - reload addon
            mock_output_2 = (
                'RESULT:{"addon_name": "test_addon", "global_reload": false, '
                '"success": true, "reloaded_modules": ["test_addon"], "errors": []}'
            )
            mock_run_python.return_value = {
                'output': mock_output_2,
                'error': None
            }

            reload_result = await reload_addon("test_addon")
            assert reload_result.success is True
