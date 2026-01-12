"""Tests for filesystem tools."""

from pathlib import Path
import pytest

from otter_code.config import ToolConfig, set_config
from otter_code.tools import filesystem


# Test read_file successfully reads existing file
def test_read_file_success(custom_config, sample_file):
    """Test read_file successfully reads an existing file."""
    set_config(custom_config)
    
    content = filesystem.read_file("sample.txt")
    assert "Hello, World!" in content
    assert "This is a test file." in content


# Test read_file with absolute path
def test_read_file_absolute_path(custom_config, sample_file):
    """Test read_file with absolute path."""
    set_config(custom_config)
    
    content = filesystem.read_file(str(sample_file))
    assert "Hello, World!" in content


# Test read_file raises FileNotFoundError for non-existent file
def test_read_file_not_found(custom_config):
    """Test read_file raises FileNotFoundError for non-existent file."""
    set_config(custom_config)
    
    with pytest.raises(FileNotFoundError, match="File not found"):
        filesystem.read_file("nonexistent.txt")


# Test read_file raises ValueError for disallowed path
def test_read_file_disallowed_path(temp_dir):
    """Test read_file raises ValueError for disallowed paths."""
    config = ToolConfig(project_root=temp_dir)
    set_config(config)
    
    with pytest.raises(ValueError, match="outside allowed boundaries"):
        filesystem.read_file("/etc/hosts")


# Test read_file raises ValueError for directory path
def test_read_file_directory_path(custom_config, temp_dir):
    """Test read_file raises ValueError when path is a directory."""
    set_config(custom_config)
    
    # Create a subdirectory
    subdir = temp_dir / "subdir"
    subdir.mkdir()
    
    with pytest.raises(ValueError, match="Path is not a file"):
        filesystem.read_file("subdir")


# Test write_file creates new file
def test_write_file_new_file(custom_config):
    """Test write_file creates a new file."""
    set_config(custom_config)
    
    result = filesystem.write_file("new_file.txt", "Test content")
    assert "Successfully wrote" in result
    assert "new_file.txt" in result
    
    # Verify file was created
    assert (custom_config.project_root / "new_file.txt").exists()
    content = (custom_config.project_root / "new_file.txt").read_text()
    assert content == "Test content"


# Test write_file creates parent directories
def test_write_file_creates_dirs(custom_config):
    """Test write_file creates parent directories if they don't exist."""
    set_config(custom_config)
    
    result = filesystem.write_file("nested/deep/file.txt", "Content")
    assert "Successfully wrote" in result
    
    # Verify path was created
    file_path = custom_config.project_root / "nested" / "deep" / "file.txt"
    assert file_path.exists()
    assert file_path.read_text() == "Content"


# Test write_file overwrites existing file
def test_write_file_overwrite(custom_config, sample_file):
    """Test write_file overwrites existing file."""
    set_config(custom_config)
    
    original_content = sample_file.read_text()
    assert "Hello" in original_content
    
    result = filesystem.write_file("sample.txt", "New content")
    assert "Successfully wrote" in result
    
    # Verify content was overwritten
    new_content = sample_file.read_text()
    assert new_content == "New content"


# Test write_file with absolute path
def test_write_file_absolute_path(custom_config, temp_dir):
    """Test write_file with absolute path."""
    set_config(custom_config)
    
    file_path = temp_dir / "absolute.txt"
    result = filesystem.write_file(str(file_path), "Absolute content")
    assert "Successfully wrote" in result
    
    assert file_path.read_text() == "Absolute content"


# Test write_file raises ValueError for disallowed path
def test_write_file_disallowed_path(temp_dir):
    """Test write_file raises ValueError for disallowed paths."""
    config = ToolConfig(project_root=temp_dir)
    set_config(config)
    
    with pytest.raises(ValueError, match="outside allowed boundaries"):
        filesystem.write_file("/tmp/file.txt", "content")


# Test list_directory non-recursive
def test_list_directory_non_recursive(sample_project_structure, custom_config):
    """Test list_directory lists non-recursive directory contents."""
    set_config(custom_config)
    
    result = filesystem.list_directory(".")
    
    assert "[DIR]  src/" in result
    assert "[DIR]  tests/" in result
    assert "[FILE] README.md" in result
    assert "[FILE] pyproject.toml" in result
    
    # Nested items should not appear
    assert "nested/" not in result
    assert "main.py" not in result


# Test list_directory filters hidden files
def test_list_directory_filters_hidden(sample_project_structure, custom_config):
    """Test list_directory filters out hidden files and directories."""
    set_config(custom_config)
    
    result = filesystem.list_directory(".")
    
    # Hidden files should not appear
    assert ".hidden" not in result
    assert ".gitignore" not in result


# Test list_directory recursive
def test_list_directory_recursive(sample_project_structure, custom_config):
    """Test list_directory lists contents recursively."""
    set_config(custom_config)
    
    result = filesystem.list_directory(".", recursive=True)
    
    # Top-level items
    assert "[DIR]  src/" in result
    assert "[DIR]  tests/" in result
    
    # Nested items should appear
    assert "src/nested/" in result
    assert "src/main.py" in result
    assert "src/utils.py" in result
    assert "src/nested/module.py" in result
    assert "tests/test_main.py" in result


# Test list_directory recursive filters hidden files
def test_list_directory_recursive_filters_hidden(sample_project_structure, custom_config):
    """Test list_directory recursive filters hidden files."""
    set_config(custom_config)
    
    result = filesystem.list_directory(".", recursive=True)
    
    # Hidden files should not appear even in recursive listing
    assert ".hidden" not in result
    assert ".gitignore" not in result


# Test list_directory empty directory
def test_list_directory_empty(custom_config):
    """Test list_directory handles empty directory."""
    set_config(custom_config)
    
    empty_dir = custom_config.project_root / "empty"
    empty_dir.mkdir()
    
    result = filesystem.list_directory("empty")
    assert "empty" in result.lower()
    assert "is empty" in result.lower()


# Test list_directory with non-existent path
def test_list_directory_not_found(custom_config):
    """Test list_directory raises FileNotFoundError for non-existent directory."""
    set_config(custom_config)
    
    with pytest.raises(FileNotFoundError, match="Directory not found"):
        filesystem.list_directory("nonexistent")


# Test list_directory with file path
def test_list_directory_file_path(custom_config, sample_file):
    """Test list_directory raises ValueError when path is not a directory."""
    set_config(custom_config)
    
    with pytest.raises(ValueError, match="Path is not a directory"):
        filesystem.list_directory("sample.txt")


# Test search_files with simple pattern
def test_search_files_simple_pattern(sample_project_structure, custom_config):
    """Test search_files finds files matching glob pattern."""
    set_config(custom_config)
    
    result = filesystem.search_files("*.py")
    
    assert "main.py" in result
    assert "utils.py" in result
    assert "test_main.py" in result
    
    # Non-Python files should not appear
    assert "README.md" not in result


# Test search_files with recursive pattern
def test_search_files_recursive_pattern(sample_project_structure, custom_config):
    """Test search_files with recursive pattern (**/)."""
    set_config(custom_config)
    
    result = filesystem.search_files("**/*.py")
    
    assert "main.py" in result
    assert "utils.py" in result
    assert "nested/module.py" in result
    assert "test_main.py" in result


# Test search_files filters hidden files
def test_search_files_filters_hidden(sample_project_structure, custom_config):
    """Test search_files filters hidden files."""
    set_config(custom_config)
    
    result = filesystem.search_files("*")
    
    # Hidden files should not appear
    assert ".hidden" not in result
    assert ".gitignore" not in result


# Test search_files in subdirectory
def test_search_files_subdirectory(sample_project_structure, custom_config):
    """Test search_files in a specific subdirectory."""
    set_config(custom_config)
    
    result = filesystem.search_files("*.py", "src")
    
    assert "main.py" in result
    assert "utils.py" in result
    assert "nested/module.py" in result
    
    # Files outside src should not appear
    assert "test_main.py" not in result


# Test search_files no matches
def test_search_files_no_matches(custom_config):
    """Test search_files handles no matches found."""
    set_config(custom_config)
    
    result = filesystem.search_files("*.xyz")
    assert "No files matching" in result
    assert "*.xyz" in result


# Test search_files non-existent directory
def test_search_files_not_found(custom_config):
    """Test search_files raises FileNotFoundError for non-existent directory."""
    set_config(custom_config)
    
    with pytest.raises(FileNotFoundError, match="Directory not found"):
        filesystem.search_files("*.py", "nonexistent")


# Test find_in_files text pattern
def test_find_in_files_text_pattern(sample_project_structure, custom_config):
    """Test find_in_files searches for text pattern in files."""
    set_config(custom_config)
    
    # Search for "def" in Python files
    result = filesystem.find_in_files("def", file_pattern="*.py")
    
    assert "Found matches" in result
    assert "main.py:" in result
    assert "1: def main():" in result
    assert "utils.py:" in result
    assert "1: def helper():" in result


# Test find_in_files with regex
def test_find_in_files_regex(sample_project_structure, custom_config):
    """Test find_in_files with regex pattern."""
    set_config(custom_config)
    
    # Search for function definitions
    result = filesystem.find_in_files(r"^def \w+", file_pattern="*.py", regex=True)
    
    assert "Found matches" in result
    assert "main.py:" in result
    assert "utils.py:" in result


# Test find_in_files with context lines
def test_find_in_files_with_context(sample_project_structure, custom_config):
    """Test find_in_files includes context lines."""
    set_config(custom_config)
    
    # Create a file with more content
    test_file = custom_config.project_root / "context_test.py"
    test_file.write_text("""# Line 1
# Line 2
def test_func():
    # Line 5
    pass
# Line 7
""")
    
    result = filesystem.find_in_files(
        "def test_func",
        file_pattern="*.py",
        context_lines=1
    )
    
    assert "context_test.py:" in result
    assert "> 3: def test_func():" in result
    # Should include context lines
    assert "  2: # Line 2" in result or "  4:     # Line 5" in result


# Test find_in_files filters by file pattern
def test_find_in_files_file_pattern(sample_project_structure, custom_config):
    """Test find_in_files filters by file pattern."""
    set_config(custom_config)
    
    result = filesystem.find_in_files("Project", file_pattern="*.md")
    
    assert "README.md:" in result
    assert "# Test Project" in result
    
    # Python files should not be searched
    assert "main.py" not in result


# Test find_in_files no matches
def test_find_in_files_no_matches(sample_project_structure, custom_config):
    """Test find_in_files handles no matches found."""
    set_config(custom_config)
    
    result = filesystem.find_in_files("NONEXISTENT_PATTERN")
    assert "No matches for" in result


# Test find_in_files invalid regex
def test_find_in_files_invalid_regex(custom_config):
    """Test find_in_files raises ValueError for invalid regex."""
    set_config(custom_config)
    
    with pytest.raises(ValueError, match="Invalid regex pattern"):
        filesystem.find_in_files("[invalid(Regex", regex=True)


# Test find_in_files non-existent directory
def test_find_in_files_not_found(custom_config):
    """Test find_in_files raises FileNotFoundError for non-existent directory."""
    set_config(custom_config)
    
    with pytest.raises(FileNotFoundError, match="Directory not found"):
        filesystem.find_in_files("pattern", path="nonexistent")


# Test find_in_files not a directory
def test_find_in_files_not_directory(custom_config, sample_file):
    """Test find_in_files raises ValueError when path is not a directory."""
    set_config(custom_config)
    
    with pytest.raises(ValueError, match="Path is not a directory"):
        filesystem.find_in_files("pattern", path="sample.txt")


# Test _format_size helper function
def test_format_size():
    """Test _format_size formats file sizes correctly."""
    from otter_code.tools.filesystem import _format_size
    
    assert _format_size(0) == "0B"
    assert _format_size(500) == "500B"
    assert _format_size(1024) == "1.0KB"
    assert _format_size(1536) == "1.5KB"
    assert _format_size(1024 * 1024) == "1.0MB"
    assert _format_size(1024 * 1024 * 1024) == "1.0GB"
    assert _format_size(1024 * 1024 * 1024 * 1024) == "1.0TB"