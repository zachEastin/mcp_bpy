"""Tests for streaming functionality in the Blender MCP server."""

from unittest.mock import AsyncMock, patch

import pytest

from bpy_mcp.server import run_python


class FakeStreamingBlenderListener:
    """Mock Blender listener that simulates streaming responses."""

    def __init__(self, stream_chunks=None, final_output="", error=None):
        """Initialize the fake listener.

        Args:
            stream_chunks: List of chunks to stream (if None, uses default test chunks)
            final_output: Final output to include in the completion message
            error: Error message to simulate (if any)
        """
        self.stream_chunks = stream_chunks if stream_chunks is not None else ["chunk 0", "chunk 1", "chunk 2"]
        self.final_output = final_output
        self.error = error
        self.messages_received = []
        self.current_message_id = None

    async def receive_message_handler(self, reader):
        """Simulate receiving a message and return appropriate responses."""
        # Subsequent calls - return streaming responses
        if not hasattr(self, "_stream_index"):
            self._stream_index = 0

        if self._stream_index < len(self.stream_chunks):
            # Return streaming chunk
            response = {
                "id": self.current_message_id,
                "chunk": self.stream_chunks[self._stream_index],
                "stream_end": False,
            }
            self._stream_index += 1
            return response
        else:
            # Return final response
            response = {
                "id": self.current_message_id,
                "output": self.final_output,
                "error": self.error,
                "stream_end": True,
            }
            return response

    async def send_message_handler(self, writer, message):
        """Simulate sending a message to the listener."""
        self.messages_received.append(message)
        self.current_message_id = message.get("id")


@pytest.fixture
def fake_streaming_connection():
    """Provide a fake streaming connection for testing."""
    fake_listener = FakeStreamingBlenderListener()

    # Mock the global connection variables
    with patch("bpy_mcp.server._reader", AsyncMock()), patch("bpy_mcp.server._writer", AsyncMock()):
        # Mock send_message and receive_message
        with (
            patch("bpy_mcp.server.send_message", fake_listener.send_message_handler),
            patch("bpy_mcp.server.receive_message", fake_listener.receive_message_handler),
        ):
            yield fake_listener


@pytest.mark.asyncio
async def test_streaming_basic_functionality(fake_streaming_connection):
    """Test basic streaming functionality."""
    fake_listener = fake_streaming_connection

    # Execute streaming code
    result = await run_python("for i in range(3): print(f'chunk {i}')", stream=True)

    # Verify the message was sent correctly
    assert len(fake_listener.messages_received) == 1
    message = fake_listener.messages_received[0]
    assert message["code"] == "for i in range(3): print(f'chunk {i}')"
    assert message["stream"] is True

    # Verify the result contains all chunks
    expected_output = "chunk 0\nchunk 1\nchunk 2"
    assert result["output"] == expected_output
    assert result["error"] is None


@pytest.mark.asyncio
async def test_streaming_with_error():
    """Test streaming with an error response."""
    fake_listener = FakeStreamingBlenderListener(
        stream_chunks=["output line 1"], error="NameError: name 'undefined_var' is not defined"
    )

    with patch("bpy_mcp.server._reader", AsyncMock()), patch("bpy_mcp.server._writer", AsyncMock()):
        with (
            patch("bpy_mcp.server.send_message", fake_listener.send_message_handler),
            patch("bpy_mcp.server.receive_message", fake_listener.receive_message_handler),
        ):
            # Execute code that should fail
            with pytest.raises(Exception) as exc_info:
                await run_python("print(undefined_var)", stream=True)

            # Verify the error is properly propagated
            assert "Blender execution error" in str(exc_info.value)
            assert "NameError" in str(exc_info.value)


@pytest.mark.asyncio
async def test_streaming_empty_output():
    """Test streaming with no output chunks."""
    fake_listener = FakeStreamingBlenderListener(
        stream_chunks=[], final_output="Code executed successfully with no output"
    )

    with patch("bpy_mcp.server._reader", AsyncMock()), patch("bpy_mcp.server._writer", AsyncMock()):
        with (
            patch("bpy_mcp.server.send_message", fake_listener.send_message_handler),
            patch("bpy_mcp.server.receive_message", fake_listener.receive_message_handler),
        ):
            result = await run_python("# Silent code", stream=True)

            assert result["output"] == "Code executed successfully with no output"
            assert result["error"] is None


@pytest.mark.asyncio
async def test_streaming_large_output():
    """Test streaming with many chunks."""
    # Generate 10 chunks
    chunks = [f"Line {i}" for i in range(10)]
    fake_listener = FakeStreamingBlenderListener(stream_chunks=chunks)

    with patch("bpy_mcp.server._reader", AsyncMock()), patch("bpy_mcp.server._writer", AsyncMock()):
        with (
            patch("bpy_mcp.server.send_message", fake_listener.send_message_handler),
            patch("bpy_mcp.server.receive_message", fake_listener.receive_message_handler),
        ):
            result = await run_python("for i in range(10): print(f'Line {i}')", stream=True)

            expected_output = "\n".join(chunks)
            assert result["output"] == expected_output
            assert result["error"] is None


@pytest.mark.asyncio
async def test_non_streaming_mode_still_works():
    """Test that non-streaming mode continues to work as before."""
    fake_listener = FakeStreamingBlenderListener()

    # Override receive_message to return non-streaming response
    async def non_streaming_receive(reader):
        return {
            "id": fake_listener.current_message_id,
            "output": "Non-streaming output",
            "error": None,
            "stream_end": True,
        }

    with patch("bpy_mcp.server._reader", AsyncMock()), patch("bpy_mcp.server._writer", AsyncMock()):
        with (
            patch("bpy_mcp.server.send_message", fake_listener.send_message_handler),
            patch("bpy_mcp.server.receive_message", non_streaming_receive),
        ):
            result = await run_python("print('hello')", stream=False)

            # Verify non-streaming request was sent
            message = fake_listener.messages_received[0]
            assert message["stream"] is False

            # Verify result
            assert result["output"] == "Non-streaming output"
            assert result["error"] is None


@pytest.mark.asyncio
async def test_message_id_handling():
    """Test that message IDs are properly handled in streaming mode."""
    fake_listener = FakeStreamingBlenderListener()

    with patch("bpy_mcp.server._reader", AsyncMock()), patch("bpy_mcp.server._writer", AsyncMock()):
        with (
            patch("bpy_mcp.server.send_message", fake_listener.send_message_handler),
            patch("bpy_mcp.server.receive_message", fake_listener.receive_message_handler),
        ):
            await run_python("print('test')", stream=True)

            # Verify message ID was generated and used
            message = fake_listener.messages_received[0]
            assert "id" in message
            assert len(message["id"]) > 0  # Should be a UUID
            assert fake_listener.current_message_id == message["id"]


if __name__ == "__main__":
    # Run tests directly
    pytest.main([__file__, "-v"])
