import anyio
from mcp.shared.exceptions import McpError

from bpy_mcp.server import get_node_group_info
import json

def _ensure_jsonable_result(result):
    """Ensure the result can be serialized to JSON. If not return the path to the non-JSONable object."""
    try:
        json.dumps(result)
        return "Result is JSON serializable"
    except TypeError:
        def find_non_jsonable(obj, path):
            try:
                json.dumps(obj)
            except TypeError:
                if isinstance(obj, dict):
                    for k, v in obj.items():
                        bad_path = find_non_jsonable(v, path + [str(k)])
                        if bad_path:
                            return bad_path
                elif isinstance(obj, list | tuple):
                    for idx, v in enumerate(obj):
                        bad_path = find_non_jsonable(v, path + [f"[{idx}]"])
                        if bad_path:
                            return bad_path
                else:
                    return path or ["<root>"]
            return None

        bad_path = find_non_jsonable(result, [])
        return ".".join(bad_path) if bad_path else "Result is JSON serializable"

async def main():
    try:
        result = await get_node_group_info("tvfx_tt_Erosion")
        # result = await get_node_group_info("tt_bake_helper")
    except ConnectionError as e:
        print(f"Failed to connect to Blender MCP server: {e}")
        return
    except McpError as e:
        print(f"Failed to retrieve node group info: {e}")
        return

    d = result.model_dump()
    # print(d)

    r = _ensure_jsonable_result(d)

    if r == "<root>":
        print("<root> is not JSON serializable")
        print(f"type: {type(d)}")
        print("keys:", d.keys())
    else:
        print(r)



if __name__ == "__main__":
    anyio.run(main)
