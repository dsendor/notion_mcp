from mcp.server import Server
from mcp.types import (
    Resource, 
    Tool,
    TextContent,
    EmbeddedResource
)
import os
import json
import httpx
from dotenv import load_dotenv
from pathlib import Path

# Find and load .env file from project root
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'
if not env_path.exists():
    raise FileNotFoundError(f"No .env file found at {env_path}")
load_dotenv(env_path)

# Configuration with validation
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

if not NOTION_API_KEY:
    raise ValueError("NOTION_API_KEY not found in .env file")
#if not DATABASE_ID:
#    raise ValueError("NOTION_DATABASE_ID not found in .env file")

NOTION_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"

# Notion API headers
headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": NOTION_VERSION
}

async def main():
    """Fetch and display todos in a tree structure"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{NOTION_BASE_URL}/databases/{DATABASE_ID}/query",
            headers=headers,
            json={
                "sorts": [
                    {
                        "timestamp": "created_time",
                        "direction": "descending"
                    }
                ]
            }
        )
        response.raise_for_status()
        todos = response.json()

        print("📋 Todo List")
        print("├── Today")
        today_items = [todo for todo in todos["results"] 
                      if todo["properties"]["When"]["select"] and 
                      todo["properties"]["When"]["select"]["name"] == "today"]
        for todo in today_items:
            status = "✅" if todo["properties"]["Checkbox"]["checkbox"] else "⬜️"
            task = todo["properties"]["Task"]["title"][0]["text"]["content"]
            print(f"│   └── {status} {task}")

        print("└── Later")
        later_items = [todo for todo in todos["results"]
                      if todo["properties"]["When"]["select"] and 
                      todo["properties"]["When"]["select"]["name"] == "later"]
        for todo in later_items:
            status = "✅" if todo["properties"]["Checkbox"]["checkbox"] else "⬜️"
            task = todo["properties"]["Task"]["title"][0]["text"]["content"]
            print(f"    └── {status} {task}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
