from notion_mcp.server import NotionMCPServer
import asyncio
from mcp.server import Server
from mcp.runner import run_server

async def main():
    # Create server instance
    server = NotionMCPServer()
    
    print("Starting Notion MCP Server...")
    print(f"Server name: {server.name}")
    print(f"Loading data from: {server.project_root}")
    
    await run_server(
        server,
        host="localhost",
        port=8080,
        name="notion-mcp"
    )

if __name__ == "__main__":
    asyncio.run(main()) 