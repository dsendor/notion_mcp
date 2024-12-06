import asyncio
from notion_mcp.server import NotionMCPServer

async def test():
    server = NotionMCPServer()
    # Try a simple search
    results = await server.get_resources("test")
    print(f"Found {len(results)} resources")
    for resource in results:
        print(f"\nTitle: {resource.metadata['title']}")
        # Try loading full content
        full_page = await resource.tools[0].function(resource.id)
        if full_page:
            print("Full content loaded successfully")
            print(full_page.content)

if __name__ == "__main__":
    asyncio.run(test()) 