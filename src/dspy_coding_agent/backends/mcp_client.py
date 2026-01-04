"""MCP (Model Context Protocol) client adapter for filesystem operations.

This module provides an optional MCP-based backend for filesystem operations,
allowing integration with MCP-compliant servers for standardized tool access.

Note: Requires the optional 'mcp' dependency:
    pip install dspy-coding-agent[mcp]
"""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, AsyncGenerator, Optional

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    ClientSession = None
    StdioServerParameters = None
    stdio_client = None


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server connection.
    
    Attributes:
        command: The command to run the MCP server (e.g., "npx").
        args: Arguments to pass to the command.
        env: Optional environment variables for the server process.
    """
    command: str
    args: list[str]
    env: Optional[dict[str, str]] = None


class MCPFilesystemClient:
    """Client for interacting with MCP filesystem servers.
    
    This client wraps the MCP protocol to provide filesystem operations
    through a standardized interface.
    """
    
    # Default MCP filesystem server configuration
    DEFAULT_SERVER = MCPServerConfig(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-filesystem"]
    )
    
    def __init__(
        self, 
        project_root: str,
        server_config: Optional[MCPServerConfig] = None
    ):
        """Initialize the MCP filesystem client.
        
        Args:
            project_root: Root directory to expose to the MCP server.
            server_config: Optional custom server configuration.
            
        Raises:
            ImportError: If the MCP package is not installed.
        """
        if not MCP_AVAILABLE:
            raise ImportError(
                "MCP package not installed. Install with: "
                "pip install dspy-coding-agent[mcp]"
            )
        
        self.project_root = project_root
        self.server_config = server_config or self.DEFAULT_SERVER
        self._session: Optional[ClientSession] = None
        self._tools: dict[str, Any] = {}
    
    @asynccontextmanager
    async def connect(self) -> AsyncGenerator["MCPFilesystemClient", None]:
        """Connect to the MCP server.
        
        Yields:
            The connected client instance.
        """
        # Add project root to server args
        server_args = self.server_config.args + [self.project_root]
        
        server_params = StdioServerParameters(
            command=self.server_config.command,
            args=server_args,
            env=self.server_config.env
        )
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                self._session = session
                
                # Cache available tools
                tools_response = await session.list_tools()
                self._tools = {
                    tool.name: tool 
                    for tool in tools_response.tools
                }
                
                try:
                    yield self
                finally:
                    self._session = None
                    self._tools = {}
    
    async def call_tool(self, name: str, arguments: dict[str, Any]) -> Any:
        """Call an MCP tool.
        
        Args:
            name: Name of the tool to call.
            arguments: Arguments to pass to the tool.
            
        Returns:
            The result from the tool.
            
        Raises:
            RuntimeError: If not connected to a server.
            ValueError: If the tool is not available.
        """
        if self._session is None:
            raise RuntimeError("Not connected to MCP server. Use 'async with client.connect():'")
        
        if name not in self._tools:
            available = ", ".join(self._tools.keys())
            raise ValueError(f"Tool '{name}' not available. Available tools: {available}")
        
        result = await self._session.call_tool(name, arguments)
        return result.content
    
    async def read_file(self, path: str) -> str:
        """Read a file through MCP.
        
        Args:
            path: Path to the file to read.
            
        Returns:
            The file contents.
        """
        result = await self.call_tool("read_file", {"path": path})
        # MCP returns a list of content blocks
        if isinstance(result, list) and result:
            return result[0].text if hasattr(result[0], 'text') else str(result[0])
        return str(result)
    
    async def write_file(self, path: str, content: str) -> str:
        """Write content to a file through MCP.
        
        Args:
            path: Path to the file to write.
            content: Content to write.
            
        Returns:
            Confirmation message.
        """
        await self.call_tool("write_file", {"path": path, "content": content})
        return f"Successfully wrote to {path}"
    
    async def list_directory(self, path: str = ".") -> str:
        """List directory contents through MCP.
        
        Args:
            path: Path to the directory.
            
        Returns:
            Directory listing.
        """
        result = await self.call_tool("list_directory", {"path": path})
        if isinstance(result, list) and result:
            return result[0].text if hasattr(result[0], 'text') else str(result[0])
        return str(result)
    
    def list_available_tools(self) -> list[str]:
        """List available MCP tools.
        
        Returns:
            List of tool names.
        """
        return list(self._tools.keys())


def create_mcp_filesystem_tools(project_root: str) -> dict[str, callable]:
    """Create synchronous wrapper functions for MCP filesystem operations.
    
    These wrappers run the async MCP operations in a synchronous context,
    making them compatible with DSPy's synchronous tool interface.
    
    Args:
        project_root: Root directory to expose to the MCP server.
        
    Returns:
        Dictionary of tool name to function mappings.
    """
    if not MCP_AVAILABLE:
        raise ImportError(
            "MCP package not installed. Install with: "
            "pip install dspy-coding-agent[mcp]"
        )
    
    client = MCPFilesystemClient(project_root)
    
    def _run_async(coro):
        """Run an async coroutine synchronously."""
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    
    async def _read_file_async(path: str) -> str:
        async with client.connect():
            return await client.read_file(path)
    
    async def _write_file_async(path: str, content: str) -> str:
        async with client.connect():
            return await client.write_file(path, content)
    
    async def _list_directory_async(path: str = ".") -> str:
        async with client.connect():
            return await client.list_directory(path)
    
    def mcp_read_file(path: str) -> str:
        """Read file contents using MCP filesystem server.
        
        Args:
            path: Path to the file to read.
            
        Returns:
            The file contents as a string.
        """
        return _run_async(_read_file_async(path))
    
    def mcp_write_file(path: str, content: str) -> str:
        """Write content to a file using MCP filesystem server.
        
        Args:
            path: Path to the file to write.
            content: Content to write to the file.
            
        Returns:
            Confirmation message.
        """
        return _run_async(_write_file_async(path, content))
    
    def mcp_list_directory(path: str = ".") -> str:
        """List directory contents using MCP filesystem server.
        
        Args:
            path: Path to the directory to list.
            
        Returns:
            Directory listing as a formatted string.
        """
        return _run_async(_list_directory_async(path))
    
    return {
        "read_file": mcp_read_file,
        "write_file": mcp_write_file,
        "list_directory": mcp_list_directory,
    }

