"""Shared fixtures and utilities for otter_code tests."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest

from otter_code.config import ToolConfig, ShellBackend


@pytest.fixture
def temp_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary directory for testing.
    
    Returns:
        Path to the temporary directory.
    """
    yield tmp_path


@pytest.fixture
def sample_config() -> ToolConfig:
    """Create a sample ToolConfig instance for testing.
    
    Returns:
        A ToolConfig instance with default values.
    """
    return ToolConfig()


@pytest.fixture
def custom_config(temp_dir: Path) -> ToolConfig:
    """Create a ToolConfig instance with a custom project root.
    
    Args:
        temp_dir: Temporary directory fixture.
        
    Returns:
        A ToolConfig instance with project_root set to temp_dir.
    """
    return ToolConfig(project_root=temp_dir)


@pytest.fixture
def restricted_config(temp_dir: Path) -> ToolConfig:
    """Create a ToolConfig instance with restricted allowed paths.
    
    Args:
        temp_dir: Temporary directory fixture.
        
    Returns:
        A ToolConfig instance with allowed_paths restricted to a subdirectory.
    """
    allowed_path = temp_dir / "allowed"
    allowed_path.mkdir(parents=True, exist_ok=True)
    return ToolConfig(
        project_root=temp_dir,
        allowed_paths=[allowed_path]
    )


@pytest.fixture
def sample_file(temp_dir: Path) -> Path:
    """Create a sample file for testing.
    
    Args:
        temp_dir: Temporary directory fixture.
        
    Returns:
        Path to the created sample file.
    """
    file_path = temp_dir / "sample.txt"
    file_path.write_text("Hello, World!\nThis is a test file.")
    return file_path


@pytest.fixture
def sample_project_structure(temp_dir: Path) -> dict:
    """Create a sample project structure for testing.
    
    Args:
        temp_dir: Temporary directory fixture.
        
    Returns:
        Dictionary with paths to created files and directories.
    """
    # Create directory structure
    src_dir = temp_dir / "src"
    src_dir.mkdir()
    
    tests_dir = temp_dir / "tests"
    tests_dir.mkdir()
    
    nested_dir = src_dir / "nested"
    nested_dir.mkdir()
    
    # Create files
    (temp_dir / "README.md").write_text("# Test Project")
    (temp_dir / "pyproject.toml").write_text("[project]\nname = 'test'")
    (src_dir / "main.py").write_text("def main():\n    print('Hello')")
    (src_dir / "utils.py").write_text("def helper():\n    pass")
    (nested_dir / "module.py").write_text("class Module:\n    pass")
    (tests_dir / "test_main.py").write_text("def test_main():\n    pass")
    
    # Create hidden file (should be filtered out)
    (temp_dir / ".hidden").write_text("secret")
    (src_dir / ".gitignore").write_text("__pycache__")
    
    return {
        "root": temp_dir,
        "src": src_dir,
        "tests": tests_dir,
        "nested": nested_dir,
        "readme": temp_dir / "README.md",
        "main_py": src_dir / "main.py",
        "utils_py": src_dir / "utils.py",
        "nested_module": nested_dir / "module.py",
        "test_py": tests_dir / "test_main.py",
    }


@pytest.fixture(autouse=True)
def reset_global_config() -> Generator[None, None, None]:
    """Reset global configuration before each test.
    
    This ensures tests don't interfere with each other.
    """
    from otter_code.config import _config, set_config
    
    # Save original config
    original_config = _config
    
    # Reset to None
    _config = None
    
    yield
    
    # Restore original config
    set_config(original_config) if original_config is not None else None
