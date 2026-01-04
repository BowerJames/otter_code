"""DSPy-compatible tools for coding agents.

This module provides a comprehensive toolkit for AI coding agents,
including filesystem operations, code editing, shell execution, and
Python refactoring capabilities.

All tools are wrapped with dspy.Tool for seamless integration with
DSPy modules like dspy.ReAct.

Example usage:
    import dspy
    from dspy_coding_agent.tools import get_all_tools
    from dspy_coding_agent.config import ToolConfig, configure
    
    # Configure tools
    configure(
        project_root="/path/to/project",
        shell_backend="local"  # or "docker"
    )
    
    # Get all tools as DSPy Tool objects
    tools = get_all_tools()
    
    # Create a ReAct agent with the tools
    agent = dspy.ReAct(
        signature="task: str -> result: str",
        tools=tools,
        max_iters=15
    )
"""

from typing import List, Optional

import dspy

from ..config import ToolConfig, get_config, set_config, configure

# Import all tool functions
from .filesystem import (
    read_file,
    write_file,
    list_directory,
    search_files,
    find_in_files,
)

from .code_editing import (
    search_replace,
    search_replace_all,
    apply_diff,
    insert_at_line,
    delete_lines,
)

from .shell import (
    execute_bash,
    execute_bash_with_status,
    get_working_directory,
    change_directory,
    reset_shell_session,
    get_shell_info,
    run_python,
    run_script,
    install_package,
    close_shell,
)

from .refactoring import (
    rename_symbol,
    rename_symbol_at_line,
    find_references,
    extract_function,
    extract_variable,
    move_symbol,
    get_symbol_at_offset,
    undo_last_refactoring,
    redo_refactoring,
    validate_python_syntax,
    close_rope_project,
)


# Categories for organizing tools
FILESYSTEM_TOOLS = [
    read_file,
    write_file,
    list_directory,
    search_files,
    find_in_files,
]

CODE_EDITING_TOOLS = [
    search_replace,
    search_replace_all,
    apply_diff,
    insert_at_line,
    delete_lines,
]

SHELL_TOOLS = [
    execute_bash,
    get_working_directory,
    change_directory,
    reset_shell_session,
    run_python,
    run_script,
]

REFACTORING_TOOLS = [
    rename_symbol,
    rename_symbol_at_line,
    find_references,
    extract_function,
    extract_variable,
    move_symbol,
    validate_python_syntax,
]

# Core tools recommended for most agents
CORE_TOOLS = [
    read_file,
    write_file,
    list_directory,
    search_files,
    find_in_files,
    search_replace,
    execute_bash,
    get_working_directory,
]


def wrap_as_dspy_tool(func) -> dspy.Tool:
    """Wrap a function as a DSPy Tool.
    
    Args:
        func: The function to wrap.
        
    Returns:
        A dspy.Tool wrapping the function.
    """
    return dspy.Tool(func)


def get_filesystem_tools() -> List[dspy.Tool]:
    """Get all filesystem-related tools.
    
    Returns:
        List of DSPy Tool objects for filesystem operations.
    """
    return [wrap_as_dspy_tool(f) for f in FILESYSTEM_TOOLS]


def get_code_editing_tools() -> List[dspy.Tool]:
    """Get all code editing tools.
    
    Returns:
        List of DSPy Tool objects for code editing.
    """
    return [wrap_as_dspy_tool(f) for f in CODE_EDITING_TOOLS]


def get_shell_tools() -> List[dspy.Tool]:
    """Get all shell execution tools.
    
    Returns:
        List of DSPy Tool objects for shell execution.
    """
    return [wrap_as_dspy_tool(f) for f in SHELL_TOOLS]


def get_refactoring_tools() -> List[dspy.Tool]:
    """Get all Python refactoring tools.
    
    Returns:
        List of DSPy Tool objects for refactoring.
    """
    return [wrap_as_dspy_tool(f) for f in REFACTORING_TOOLS]


def get_core_tools() -> List[dspy.Tool]:
    """Get a curated set of essential tools for most coding tasks.
    
    This includes basic file operations, code editing, and shell access.
    
    Returns:
        List of essential DSPy Tool objects.
    """
    return [wrap_as_dspy_tool(f) for f in CORE_TOOLS]


def get_all_tools(config: Optional[ToolConfig] = None) -> List[dspy.Tool]:
    """Get all available tools.
    
    Args:
        config: Optional ToolConfig to use. If provided, updates global config.
        
    Returns:
        List of all DSPy Tool objects.
    """
    if config is not None:
        set_config(config)
    
    all_functions = (
        FILESYSTEM_TOOLS +
        CODE_EDITING_TOOLS +
        SHELL_TOOLS +
        REFACTORING_TOOLS
    )
    
    return [wrap_as_dspy_tool(f) for f in all_functions]


def get_tools_by_category(
    filesystem: bool = True,
    code_editing: bool = True,
    shell: bool = True,
    refactoring: bool = True,
    config: Optional[ToolConfig] = None
) -> List[dspy.Tool]:
    """Get tools from selected categories.
    
    Args:
        filesystem: Include filesystem tools.
        code_editing: Include code editing tools.
        shell: Include shell execution tools.
        refactoring: Include Python refactoring tools.
        config: Optional ToolConfig to use.
        
    Returns:
        List of DSPy Tool objects from selected categories.
    """
    if config is not None:
        set_config(config)
    
    tools = []
    
    if filesystem:
        tools.extend(get_filesystem_tools())
    if code_editing:
        tools.extend(get_code_editing_tools())
    if shell:
        tools.extend(get_shell_tools())
    if refactoring:
        tools.extend(get_refactoring_tools())
    
    return tools


def cleanup() -> None:
    """Clean up all tool resources.
    
    Call this when done using the tools to release resources
    like shell sessions and Rope projects.
    """
    close_shell()
    close_rope_project()


# Export all public functions and tools
__all__ = [
    # Configuration
    "configure",
    "ToolConfig",
    
    # Tool getters
    "get_all_tools",
    "get_core_tools",
    "get_filesystem_tools",
    "get_code_editing_tools",
    "get_shell_tools",
    "get_refactoring_tools",
    "get_tools_by_category",
    "wrap_as_dspy_tool",
    
    # Cleanup
    "cleanup",
    
    # Filesystem tools
    "read_file",
    "write_file",
    "list_directory",
    "search_files",
    "find_in_files",
    
    # Code editing tools
    "search_replace",
    "search_replace_all",
    "apply_diff",
    "insert_at_line",
    "delete_lines",
    
    # Shell tools
    "execute_bash",
    "execute_bash_with_status",
    "get_working_directory",
    "change_directory",
    "reset_shell_session",
    "get_shell_info",
    "run_python",
    "run_script",
    "install_package",
    "close_shell",
    
    # Refactoring tools
    "rename_symbol",
    "rename_symbol_at_line",
    "find_references",
    "extract_function",
    "extract_variable",
    "move_symbol",
    "get_symbol_at_offset",
    "undo_last_refactoring",
    "redo_refactoring",
    "validate_python_syntax",
    "close_rope_project",
]
