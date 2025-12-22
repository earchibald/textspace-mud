#!/usr/bin/env python3
"""
TextSpace MCP Client - Direct client for testing MCP server
"""

import asyncio
import json
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async def main():
    """Test the TextSpace MCP server"""
    
    # Connect to MCP server
    server_params = StdioServerParameters(
        command="python3",
        args=["/Users/earchibald/scratch/006-mats/textspace_mcp_server.py"]
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize
            await session.initialize()
            
            # List available tools
            tools = await session.list_tools()
            print("Available tools:")
            for tool in tools.tools:
                print(f"  - {tool.name}: {tool.description}")
            
            # Test server status
            print("\n🔍 Testing server status...")
            result = await session.call_tool("server_status", {})
            print(f"Status: {result.content[0].text}")
            
            # Test config reading
            print("\n📖 Testing config reading...")
            result = await session.call_tool("read_config", {"config_type": "rooms"})
            print("Rooms config loaded successfully")
            
            # Test validation
            print("\n✅ Testing config validation...")
            test_config = """
rooms:
  test_room:
    name: "Test Room"
    description: "A test room"
    exits: {}
    items: []
"""
            result = await session.call_tool("validate_config", {
                "config_type": "rooms",
                "content": test_config
            })
            validation = json.loads(result.content[0].text)
            print(f"Validation result: {validation['valid']}")
            
            print("\n✅ MCP server test completed!")

if __name__ == "__main__":
    asyncio.run(main())
