"""Tests for the create_bpy_operator MCP tool."""

import os
import tempfile
from pathlib import Path

import pytest

from bpy_mcp.server import create_bpy_operator


class TestCreateBpyOperator:
    """Test the create_bpy_operator tool."""

    @pytest.mark.asyncio
    async def test_basic_operator_generation(self):
        """Test basic operator generation with minimal parameters."""
        result = await create_bpy_operator(
            name="Test Operator",
            description="A simple test operator"
        )
        
        assert result.success
        assert result.class_name == "TestOperatorOperator"
        assert result.bl_idname == "object.test_operator"
        assert "class TestOperatorOperator(Operator):" in result.operator_code
        assert "bl_idname = \"object.test_operator\"" in result.operator_code
        assert "bl_label = \"Test Operator\"" in result.operator_code
        assert "def execute(self, context:" in result.operator_code
        assert "def register():" in result.registration_code
        assert "bpy.utils.register_class(TestOperatorOperator)" in result.registration_code

    @pytest.mark.asyncio
    async def test_operator_with_custom_category(self):
        """Test operator generation with custom category."""
        result = await create_bpy_operator(
            name="Add Cube",
            description="Add a cube to the scene",
            category="MESH"
        )
        
        assert result.success
        assert result.bl_idname == "mesh.add_cube"
        assert result.class_name == "AddCubeOperator"

    @pytest.mark.asyncio
    async def test_operator_with_methods(self):
        """Test operator generation with optional methods."""
        result = await create_bpy_operator(
            name="Interactive Tool",
            description="An interactive operator",
            include_invoke=True,
            include_poll=True,
            include_modal=True
        )
        
        assert result.success
        assert "def invoke(self, context:" in result.operator_code
        assert "def poll(cls, context:" in result.operator_code
        assert "def modal(self, context:" in result.operator_code

    @pytest.mark.asyncio
    async def test_operator_with_properties(self):
        """Test operator generation with properties."""
        properties = [
            {
                "name": "scale_factor",
                "type": "FloatProperty",
                "description": "Scale factor",
                "default": 1.0
            },
            {
                "name": "use_smooth",
                "type": "BoolProperty",
                "description": "Use smooth shading",
                "default": True
            }
        ]
        
        result = await create_bpy_operator(
            name="Scale Object",
            description="Scale an object",
            properties=properties
        )
        
        assert result.success
        assert "from bpy.props import BoolProperty, FloatProperty" in result.operator_code or \
               "from bpy.props import FloatProperty, BoolProperty" in result.operator_code
        assert "scale_factor: FloatProperty(" in result.operator_code
        assert "use_smooth: BoolProperty(" in result.operator_code
        assert "default=1.0" in result.operator_code
        assert "default=True" in result.operator_code

    @pytest.mark.asyncio
    async def test_operator_file_creation(self):
        """Test that operator file is actually created."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = Path(temp_dir) / "test_operator.py"
            
            result = await create_bpy_operator(
                name="File Test",
                description="Test file creation",
                output_file=str(output_file)
            )
            
            assert result.success
            assert result.file_path == str(output_file)
            assert output_file.exists()
            
            # Verify file content
            content = output_file.read_text(encoding='utf-8')
            assert "class FileTestOperator(Operator):" in content
            assert "bl_idname = \"object.file_test\"" in content
            assert "def register():" in content

    @pytest.mark.asyncio
    async def test_validation_errors(self):
        """Test validation of invalid inputs."""
        # Empty name
        result = await create_bpy_operator(
            name="",
            description="Valid description"
        )
        assert not result.success
        assert "Operator name cannot be empty" in result.errors
        
        # Empty description
        result = await create_bpy_operator(
            name="Valid Name",
            description=""
        )
        assert not result.success
        assert "Operator description cannot be empty" in result.errors

    @pytest.mark.asyncio
    async def test_property_validation(self):
        """Test property validation and warnings."""
        properties = [
            {
                "name": "",  # Invalid: empty name
                "type": "StringProperty",
                "description": "Empty name property"
            },
            {
                "name": "valid_prop",
                "type": "IntProperty",
                "description": "Valid property",
                "default": 42
            }
        ]
        
        result = await create_bpy_operator(
            name="Property Test",
            description="Test property validation",
            properties=properties
        )
        
        assert result.success
        assert len(result.warnings) > 0
        assert "valid_prop: IntProperty(" in result.operator_code
        assert "default=42" in result.operator_code

    @pytest.mark.asyncio
    async def test_special_characters_in_name(self):
        """Test handling of special characters in operator name."""
        result = await create_bpy_operator(
            name="Add UV-Sphere (Advanced)",
            description="Add a UV sphere with advanced options"
        )
        
        assert result.success
        assert result.class_name == "AddUvSphereAdvancedOperator"
        assert result.bl_idname == "object.add_uv_sphere_advanced"

    @pytest.mark.asyncio
    @pytest.mark.skipif(os.name == 'nt', reason="Windows temp directory cleanup issues")
    async def test_default_file_creation(self):
        """Test default file creation when no output_file is specified."""
        # Change to temp directory for this test
        original_cwd = Path.cwd()

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                os.chdir(temp_path)

                result = await create_bpy_operator(
                    name="Default File",
                    description="Test default file creation"
                )

                assert result.success
                assert "operators" in result.file_path
                assert "default_file_operator.py" in result.file_path

                file_path = Path(result.file_path)
                assert file_path.exists()

                # Read and immediately close the file to avoid permission issues on Windows
                content = file_path.read_text(encoding='utf-8')
                assert "class DefaultFileOperator(Operator):" in content

        finally:
            # Always restore original directory
            os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__])
