import asyncio
from mcp_manager import MCPHostManager
import os

async def main():
    # Caminho para o servidor do DesktopCommander
    # Assumindo que você construiu o projeto, o script principal está em dist/index.js
    server_path = os.path.abspath("desktop-commander-ext/dist/index.js")
    
    manager = MCPHostManager(server_path)
    
    try:
        await manager.connect()
        
        # Testar listagem de ferramentas
        tools = await manager.list_tools()
        print("Available tools:")
        for tool in tools.tools:
            print(f"- {tool.name}: {tool.description}")
            
    finally:
        await manager.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
