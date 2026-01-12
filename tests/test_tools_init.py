"""Tests for tools initialization and organization."""

import pytest
import dspy

from otter_code.tools import (
    wrap_as_dspy_tool,
    get_filesystem_tools,
    get_code_editing_tools,
    get_shell_tools,
    get_refactoring_tools,
    get_core_tools,
    get_all_tools,
    get_tools_by_category,
    cleanup,
)
from otter_code.config import ToolConfig, set_config


# Test wrap_as_dspy_tool returns a dspy.Tool instance
def test_wrap_as_dspy_tool():
    """Test that wrap_as_dspy_tool returns a dspy.Tool instance."""
    def sample_func(x: int) -> int:
        return x * 2
    
    tool = wrap_as_dspy_tool(sample_func)
    
    assert isinstance(tool, dspy.Tool)
    assert hasattr(tool, 'name')
    assert hasattr(tool, 'func')
    assert callable(tool.func)


# Test wrap_as_dspy_tool preserves function signature
def test_wrap_as_dspy_tool_preserves_signature():
    """Test that wrapped tool preserves the original function."""
    def sample_func(x: int) -> int:
        return x * 2
    
    tool = wrap_as_dspy_tool(sample_func)
    
    # The wrapped function should still work
    result = tool.func(5)
    assert result == 10


# Test get_filesystem_tools returns list of tools
def test_get_filesystem_tools():
    """Test that get_filesystem_tools returns a list of dspy.Tool objects."""
    tools = get_filesystem_tools()
    
    assert isinstance(tools, list)
    assert len(tools) > 0
    assert all(isinstance(tool, dspy.Tool) for tool in tools)


# Test get_filesystem_tools contains expected tools
def test_get_filesystem_tools_content():
    """Test that get_filesystem_tools contains expected filesystem tools."""
    tools = get_filesystem_tools()
    
    tool_names = [tool.name for tool in tools]
    expected_tools = [
        'read_file',
        'write_file',
        'list_directory',
        'search_files',
        'find_in_files',
    ]
    
    for expected in expected_tools:
        assert expected in tool_names, f"Expected tool '{expected}' not found"


# Test get_code_editing_tools returns list of tools
def test_get_code_editing_tools():
    """Test that get_code_editing_tools returns a list of dspy.Tool objects."""
    tools = get_code_editing_tools()
    
    assert isinstance(tools, list)
    assert len(tools) > 0
    assert all(isinstance(tool, dspy.Tool) for tool in tools)


# Test get_code_editing_tools contains expected tools
def test_get_code_editing_tools_content():
    """Test that get_code_editing_tools contains expected code editing tools."""
    tools = get_code_editing_tools()
    
    tool_names = [tool.name for tool in tools]
    expected_tools = [
        'search_replace',
        'search_replace_all',
        'apply_diff',
        'insert_at_line',
        'delete_lines',
    ]
    
    for expected in expected_tools:
        assert expected in tool_names, f"Expected tool '{expected}' not found"


# Test get_shell_tools returns list of tools
def test_get_shell_tools():
    """Test that get_shell_tools returns a list of dspy.Tool objects."""
    tools = get_shell_tools()
    
    assert isinstance(tools, list)
    assert len(tools) > 0
    assert all(isinstance(tool, dspy.Tool) for tool in tools)


# Test get_shell_tools contains expected tools
def test_get_shell_tools_content():
    """Test that get_shell_tools contains expected shell tools."""
    tools = get_shell_tools()
    
    tool_names = [tool.name for tool in tools]
    expected_tools = [
        'execute_bash',
        'get_working_directory',
        'change_directory',
        'reset_shell_session',
        'run_python',
        'run_script',
    ]
    
    for expected in expected_tools:
        assert expected in tool_names, f"Expected tool '{expected}' not found"


# Test get_refactoring_tools returns list of tools
def test_get_refactoring_tools():
    """Test that get_refactoring_tools returns a list of dspy.Tool objects."""
    tools = get_refactoring_tools()
    
    assert isinstance(tools, list)
    assert len(tools) > 0
    assert all(isinstance(tool, dspy.Tool) for tool in tools)


# Test get_refactoring_tools contains expected tools
def test_get_refactoring_tools_content():
    """Test that get_refactoring_tools contains expected refactoring tools."""
    tools = get_refactoring_tools()
    
    tool_names = [tool.name for tool in tools]
    expected_tools = [
        'rename_symbol',
        'rename_symbol_at_line',
        'find_references',
        'extract_function',
        'extract_variable',
        'move_symbol',
        'validate_python_syntax',
    ]
    
    for expected in expected_tools:
        assert expected in tool_names, f"Expected tool '{expected}' not found"


# Test get_core_tools returns list of tools
def test_get_core_tools():
    """Test that get_core_tools returns a list of dspy.Tool objects."""
    tools = get_core_tools()
    
    assert isinstance(tools, list)
    assert len(tools) > 0
    assert all(isinstance(tool, dspy.Tool) for tool in tools)


# Test get_core_tools contains essential tools
def test_get_core_tools_content():
    """Test that get_core_tools contains essential tools for basic tasks."""
    tools = get_core_tools()
    
    tool_names = [tool.name for tool in tools]
    # Core tools should include at least basic operations
    assert 'read_file' in tool_names
    assert 'write_file' in tool_names
    assert 'execute_bash' in tool_names
    assert 'search_replace' in tool_names


# Test get_all_tools returns all tools
def test_get_all_tools():
    """Test that get_all_tools returns a comprehensive list of tools."""
    tools = get_all_tools()
    
    assert isinstance(tools, list)
    assert len(tools) > 0
    assert all(isinstance(tool, dspy.Tool) for tool in tools)


# Test get_all_tools includes all categories
def test_get_all_tools_comprehensive():
    """Test that get_all_tools includes tools from all categories."""
    filesystem_tools = get_filesystem_tools()
    code_editing_tools = get_code_editing_tools()
    shell_tools = get_shell_tools()
    refactoring_tools = get_refactoring_tools()
    all_tools = get_all_tools()
    
    # All_tools should have at least as many tools as individual categories
    total_from_categories = (
        len(filesystem_tools) +
        len(code_editing_tools) +
        len(shell_tools) +
        len(refactoring_tools)
    )
    
    # Note: there might be duplicates, so we use >=
    assert len(all_tools) >= total_from_categories


# Test get_tools_by_category with all True
def test_get_tools_by_category_all():
    """Test get_tools_by_category with all categories enabled."""
    tools = get_tools_by_category(
        filesystem=True,
        code_editing=True,
        shell=True,
        refactoring=True
    )
    
    assert isinstance(tools, list)
    assert len(tools) > 0
    assert all(isinstance(tool, dspy.Tool) for tool in tools)


# Test get_tools_by_category selective
def test_get_tools_by_category_selective():
    """Test get_tools_by_category with selective categories."""
    # Only filesystem and shell
    tools = get_tools_by_category(
        filesystem=True,
        code_editing=False,
        shell=True,
        refactoring=False
    )
    
    tool_names = [tool.name for tool in tools]
    
    # Should have filesystem tools
    assert 'read_file' in tool_names
    assert 'write_file' in tool_names
    
    # Should have shell tools
    assert 'execute_bash' in tool_names
    
    # Should NOT have code editing tools
    assert 'search_replace' not in tool_names
    
    # Should NOT have refactoring tools
    assert 'rename_symbol' not in tool_names


# Test get_tools_by_category empty selection
def test_get_tools_by_category_empty():
    """Test get_tools_by_category with no categories selected."""
    tools = get_tools_by_category(
        filesystem=False,
        code_editing=False,
        shell=False,
        refactoring=False
    )
    
    assert tools == []


# Test get_tools_by_category with config
def test_get_tools_by_category_with_config(temp_dir):
    """Test get_tools_by_category with custom config."""
    config = ToolConfig(project_root=temp_dir)
    
    tools = get_tools_by_category(filesystem=True, config=config)
    
    assert isinstance(tools, list)
    assert len(tools) > 0


# Test cleanup function
def test_cleanup():
    """Test that cleanup function exists and can be called without error."""
    # Just ensure it doesn't raise an exception
    cleanup()


# Test tool names are unique in category
def test_tool_names_unique_in_category():
    """Test that tool names are unique within each category."""
    for getter in [get_filesystem_tools, get_code_editing_tools, 
                   get_shell_tools, get_refactoring_tools]:
        tools = getter()
        tool_names = [tool.name for tool in tools]
        
        # Check for duplicates
        assert len(tool_names) == len(set(tool_names)), \
            f"Duplicate tool names found in {getter.__name__}"


# Test all tools have required attributes
def test_all_tools_have_required_attributes():
    """Test that all tools have name and func attributes."""
    tools = get_all_tools()
    
    for tool in tools:
        assert hasattr(tool, 'name'), f"Tool missing 'name' attribute"
        assert hasattr(tool, 'func'), f"Tool missing 'func' attribute"
        assert tool.name, f"Tool name is empty"
        assert callable(tool.func), f"Tool func is not callable"