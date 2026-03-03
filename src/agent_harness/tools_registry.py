"""In-process MCP tool definitions using the @tool decorator.

This module demonstrates how to define custom tools that run in-process
alongside the agent, without requiring a separate subprocess or Node.js.

To add a new tool:
1. Import the @tool decorator from claude_agent_sdk
2. Define an async function decorated with @tool(name, description, schema)
3. Add the function to the tools list in create_custom_tools_server()
"""

from __future__ import annotations

from typing import Any

from claude_agent_sdk import create_sdk_mcp_server, tool


@tool("lookup_user", "Look up a user by email address", {"email": str})
async def lookup_user(args: dict[str, Any]) -> dict[str, Any]:
    """Look up a user by their email address. Replace with actual lookup logic."""
    email = args["email"]
    return {"content": [{"type": "text", "text": f"User {email}: active, role=admin"}]}


@tool("run_query", "Execute a read-only SQL query", {"sql": str})
async def run_query(args: dict[str, Any]) -> dict[str, Any]:
    """Execute a read-only SQL query. Replace with actual database query logic."""
    sql = args["sql"]
    return {"content": [{"type": "text", "text": f"Query result for: {sql}"}]}


def create_custom_tools_server() -> Any:
    """Create the in-process MCP server with all custom tools."""
    return create_sdk_mcp_server(
        name="custom-tools",
        version="1.0.0",
        tools=[lookup_user, run_query],
    )
