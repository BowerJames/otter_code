"""DSPy Coding Agent - A comprehensive toolkit for AI coding agents.

This package provides DSPy-compatible tools for building autonomous coding
agents, including:

- Filesystem operations (read, write, list, search)
- Code editing with Aider-style fuzzy matching
- Persistent shell execution (local or Docker)
- Python refactoring via Rope

Example:
    import dspy
    from otter_code import configure, get_all_tools
    
    # Configure the toolkit
    configure(
        project_root="/path/to/project",
        shell_backend="local"
    )
    
    # Create a ReAct agent with tools
    agent = dspy.ReAct(
        signature="task: str -> result: str",
        tools=get_all_tools(),
        max_iters=15
    )
    
    # Run the agent
    result = agent("Fix the bug in main.py")
"""

from .config import (
    ToolConfig,
    ShellBackend,
    get_config,
    set_config,
    configure,
)

from .tools import (
    get_all_tools,
    get_core_tools,
    get_filesystem_tools,
    get_code_editing_tools,
    get_shell_tools,
    get_refactoring_tools,
    get_tools_by_category,
    cleanup,
)

__version__ = "0.1.0"

__all__ = [
    # Configuration
    "ToolConfig",
    "ShellBackend",
    "get_config",
    "set_config",
    "configure",
    
    # Tool getters
    "get_all_tools",
    "get_core_tools",
    "get_filesystem_tools",
    "get_code_editing_tools",
    "get_shell_tools",
    "get_refactoring_tools",
    "get_tools_by_category",
    
    # Cleanup
    "cleanup",
]

