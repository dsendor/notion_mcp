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
from dotenv import dotenv_values
from pathlib import Path

# Find and load .env file from project root
project_root = Path(__file__).parent
print(project_root)
env_path = project_root / '.env'
if not env_path.exists():
    raise FileNotFoundError(f"No .env file found at {env_path}")

# Load environment variables explicitly
config = dotenv_values(env_path)
NOTION_API_KEY = config.get("NOTION_API_KEY")
DATABASE_ID = config.get("NOTION_DATABASE_ID")

# Debug the loaded values
print("\nLoaded values directly from .env:")
print(f"API Key present: {'Yes' if NOTION_API_KEY else 'No'}")
print(f"Database ID: {DATABASE_ID}")

if not NOTION_API_KEY:
    raise ValueError("NOTION_API_KEY not found in .env file")
if not DATABASE_ID:
    raise ValueError("NOTION_DATABASE_ID not found in .env file")

NOTION_VERSION = "2022-02-22"
NOTION_BASE_URL = "https://api.notion.com/v1"


# After loading .env file, add these debug lines
print("Debug Environment Variables:")
print(f"Current working directory: {os.getcwd()}")
print(f"Env file path: {env_path}")
print(f"Env file exists: {env_path.exists()}")
print(f"DATABASE_ID loaded as: {DATABASE_ID}")
print(f"API URL being called: {NOTION_BASE_URL}/databases/{DATABASE_ID}/query")

# Add instructions to help find correct ID
print("\nTo find your correct database ID:")
print("1. Open your Notion database in full page view")
print("2. Look at the URL in your browser")
print("3. Copy the last 32 characters (with hyphens)")
print("Example URL format: https://www.notion.so/workspace/71e28ad4-7a44-4c83-bfd2-2aacf044970d")

# Read and print .env file contents (excluding sensitive data)
try:
    with open(env_path, 'r') as f:
        env_contents = f.read()
        print("\nEnv file contents (API key hidden):")
        for line in env_contents.splitlines():
            if line.startswith('NOTION_API_KEY'):
                print('NOTION_API_KEY=***')
            else:
                print(line)
except Exception as e:
    print(f"Error reading .env file: {e}")

if DATABASE_ID == "your-database-id-here":
    raise ValueError("Database ID is still set to placeholder value. Check .env file loading")



# Notion API headers
headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Notion-Version": NOTION_VERSION,
    "Content-Type": "application/json"
}

async def get_database_structure():
    """Fetch and print database structure"""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{NOTION_BASE_URL}/databases/{DATABASE_ID}",
                headers=headers
            )
            print("\nDatabase Structure:")
            data = response.json()
            print("Available properties:", list(data.get("properties", {}).keys()))
            
            # Save to JSON file with nice formatting
            output_file = project_root / "database_structure.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"\nDatabase structure saved to: {output_file}")
            
            return data
        except Exception as e:
            print(f"Error fetching database structure: {e}")
            return None

async def get_all_pages():
    """Fetch all pages from the workspace"""
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            all_pages = []
            has_more = True
            start_cursor = None
            page_count = 0
            
            print("\nFetching all pages...")
            while has_more:
                try:
                    params = {
                        "filter": {"value": "page", "property": "object"},
                        "page_size": 100
                    }
                    if start_cursor:
                        params["start_cursor"] = start_cursor
                    
                    print(f"Fetching batch {page_count + 1}...")
                    response = await client.post(
                        f"{NOTION_BASE_URL}/search",
                        headers=headers,
                        json=params
                    )
                    response.raise_for_status()
                    data = response.json()
                    
                    batch_results = data["results"]
                    all_pages.extend(batch_results)
                    has_more = data["has_more"]
                    start_cursor = data.get("next_cursor")
                    page_count += 1
                    
                    print(f"Batch {page_count}: Got {len(batch_results)} pages")
                    print(f"Total pages so far: {len(all_pages)}")
                    
                    # Save progress after each batch
                    temp_output_file = project_root / f"pages_batch_{page_count}.json"
                    with open(temp_output_file, 'w', encoding='utf-8') as f:
                        json.dump(batch_results, f, indent=2, ensure_ascii=False)
                    
                except httpx.TimeoutException:
                    print(f"Timeout on batch {page_count + 1}, retrying...")
                    continue
                except Exception as e:
                    print(f"Error on batch {page_count + 1}: {type(e).__name__}: {str(e)}")
                    continue
            
            # Combine all batches into final file
            output_file = project_root / "all_pages.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_pages, f, indent=2, ensure_ascii=False)
            print(f"\nAll pages saved to: {output_file}")
            print(f"Total batches: {page_count}")
            print(f"Total pages: {len(all_pages)}")
            
            return all_pages
            
        except Exception as e:
            print(f"Error in get_all_pages: {type(e).__name__}: {str(e)}")
            return None

async def search_notion(
    query: str = None,
    filter_type: str = None,
    sort: dict = None,
    start_cursor: str = None,
    page_size: int = 100
) -> dict:
    """
    Search Notion pages and databases.
    
    Args:
        query (str, optional): Search query string
        filter_type (str, optional): Filter results by 'page' or 'database'
        sort (dict, optional): Sort parameters
        start_cursor (str, optional): Pagination cursor
        page_size (int, optional): Number of results per page (default: 100)
    
    Returns:
        dict: Search results from Notion API
    """
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Build search parameters
            params = {"page_size": page_size}
            
            if query:
                params["query"] = query
            
            if filter_type:
                params["filter"] = {"property": "object", "value": filter_type}
            
            if sort:
                params["sort"] = sort
                
            if start_cursor:
                params["start_cursor"] = start_cursor
            
            response = await client.post(
                f"{NOTION_BASE_URL}/search",
                headers=headers,
                json=params
            )
            response.raise_for_status()
            return response.json()
            
        except Exception as e:
            print(f"Error in search_notion: {type(e).__name__}: {str(e)}")
            return None

async def search_all_results(
    query: str = None,
    filter_type: str = None,
    sort: dict = None
) -> list:
    """
    Search all matching results, handling pagination automatically.
    
    Args:
        query (str, optional): Search query string
        filter_type (str, optional): Filter results by 'page' or 'database'
        sort (dict, optional): Sort parameters
    
    Returns:
        list: All matching results
    """
    all_results = []
    start_cursor = None
    has_more = True
    batch_count = 0
    
    while has_more:
        batch_count += 1
        print(f"Fetching search results batch {batch_count}...")
        
        response = await search_notion(
            query=query,
            filter_type=filter_type,
            sort=sort,
            start_cursor=start_cursor
        )
        
        if not response:
            break
            
        batch_results = response["results"]
        all_results.extend(batch_results)
        
        has_more = response["has_more"]
        start_cursor = response.get("next_cursor")
        
        print(f"Batch {batch_count}: Got {len(batch_results)} results")
        print(f"Total results so far: {len(all_results)}")
    
    return all_results

async def main():
    """Fetch and display workspace structure"""
    # Get database structure
    db_structure = await get_database_structure()
    if not db_structure:
        return
        
    # Get all pages
    pages = await get_all_pages()
    if pages:
        print(f"\nTotal pages found: {len(pages)}")
        # Print first page structure as example
        if pages:
            print("\nExample page structure:")
            print(json.dumps(pages[0], indent=2))

    # Example search usage
    print("\nTesting search functionality:")
    
    # Search all pages containing "meeting"
    meeting_pages = await search_all_results(
        query="meeting",
        filter_type="page"
    )
    if meeting_pages:
        print(f"\nFound {len(meeting_pages)} pages containing 'meeting'")
        
    # Search all databases
    databases = await search_all_results(filter_type="database")
    if databases:
        print(f"\nFound {len(databases)} databases")

async def test_connection():
    """Test the basic API connection"""
    async with httpx.AsyncClient() as client:
        try:
            print("\nTesting API connection...")
            response = await client.get(
                f"{NOTION_BASE_URL}/users/me",
                headers=headers,
                timeout=30.0
            )
            print(f"Test Response Status: {response.status_code}")
            print(f"Test Response: {response.text}")
            return response.status_code == 200
        except Exception as e:
            print(f"Connection test failed: {type(e).__name__}: {str(e)}")
            return False

if __name__ == "__main__":
    import asyncio
    # Test connection before trying the main functionality
    if asyncio.run(test_connection()):
        asyncio.run(main())
    else:
        print("Failed to establish connection to Notion API")
