from mcp.server import Server
from mcp.types import Resource, Tool, TextContent
from pathlib import Path
import json
import asyncio
from typing import List, Dict, Optional

class NotionMCPServer(Server):
    def __init__(self):
        super().__init__(name="notion-mcp")
        self.project_root = Path(__file__).parent.parent.parent
        self.metadata: Dict[str, dict] = {}
        self.page_batch_map: Dict[str, int] = {}  # Maps page IDs to batch numbers
        self.load_metadata()

    def load_metadata(self):
        """Load and index all page metadata"""
        print("Loading Notion page metadata...")
        
        # Load all pages and create metadata index
        all_pages_path = self.project_root / "all_pages.json"
        if all_pages_path.exists():
            with open(all_pages_path, 'r', encoding='utf-8') as f:
                pages = json.load(f)
                for page in pages:
                    self.metadata[page["id"]] = {
                        "title": self.extract_title(page),
                        "last_edited": page["last_edited_time"],
                        "url": page.get("url", ""),
                        "object_type": page.get("object", "unknown")
                    }
        else:
            print(f"Warning: {all_pages_path} not found")

    def extract_title(self, page: dict) -> str:
        """Extract title from page properties"""
        try:
            properties = page.get("properties", {})
            title_prop = properties.get("Name", {}) or properties.get("title", {})
            if title_prop:
                return title_prop.get("title", [{}])[0].get("text", {}).get("content", "Untitled")
            return "Untitled"
        except Exception:
            return "Untitled"

    def find_relevant_pages(self, query: str, limit: int = 5) -> Dict[str, dict]:
        """Find pages relevant to the query"""
        # Simple text matching for now - can be enhanced with better search later
        relevant = {}
        for page_id, meta in self.metadata.items():
            if query.lower() in meta["title"].lower():
                relevant[page_id] = meta
                if len(relevant) >= limit:
                    break
        return relevant

    async def load_full_page(self, page_id: str) -> Optional[Resource]:
        """Load full content of a specific page"""
        try:
            all_pages_path = self.project_root / "all_pages.json"
            with open(all_pages_path, 'r', encoding='utf-8') as f:
                pages = json.load(f)
                page = next((p for p in pages if p["id"] == page_id), None)
                if page:
                    return Resource(
                        id=page_id,
                        content=TextContent(self.format_page_content(page)),
                        metadata=self.metadata[page_id]
                    )
        except Exception as e:
            print(f"Error loading page {page_id}: {e}")
        return None

    def format_page_content(self, page: dict) -> str:
        """Format page content for display"""
        content_parts = [
            f"Title: {self.extract_title(page)}",
            f"Last edited: {page['last_edited_time']}",
            "Properties:"
        ]
        
        for prop_name, prop_data in page.get("properties", {}).items():
            value = self.extract_property_value(prop_data)
            if value:
                content_parts.append(f"  {prop_name}: {value}")
        
        return "\n".join(content_parts)

    def extract_property_value(self, prop_data: dict) -> str:
        """Extract readable value from a property"""
        prop_type = prop_data.get("type", "")
        if prop_type == "title":
            return prop_data.get("title", [{}])[0].get("text", {}).get("content", "")
        elif prop_type == "rich_text":
            texts = prop_data.get("rich_text", [])
            return " ".join(t.get("text", {}).get("content", "") for t in texts)
        elif prop_type == "select":
            select_data = prop_data.get("select", {})
            return select_data.get("name", "") if select_data else ""
        return str(prop_data.get(prop_type, ""))

    async def get_resources(self, query: str) -> List[Resource]:
        """Return resources matching the query"""
        relevant_pages = self.find_relevant_pages(query)
        
        resources = []
        for page_id, meta in relevant_pages.items():
            # Create a resource with basic metadata
            resource = Resource(
                id=page_id,
                content=TextContent(f"Title: {meta['title']}\nLast edited: {meta['last_edited']}"),
                metadata=meta,
                tools=[
                    Tool(
                        name="load_full_content",
                        description="Load the full content of this page",
                        function=self.load_full_page
                    )
                ]
            )
            resources.append(resource)
        
        return resources