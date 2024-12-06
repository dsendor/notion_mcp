from mcp.server import Server
from mcp.types import Resource
from mcp.runner import run_server
import asyncio
from typing import List

class TestServer(Server):
    def __init__(self):
        super().__init__(name="test-server")

    async def get_resources(self, query: str) -> List[Resource]:
        return []

async def main():
    server = TestServer()
    print("Starting test server...")
    await run_server(server, host="localhost", port=8080)

if __name__ == "__main__":
    asyncio.run(main()) 