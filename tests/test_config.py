"""Tests for otter_code configuration."""

from pathlib import Path
import pytest

from otter_code.config import (
    ToolConfig,
    ShellBackend,
    get_config,
    set_config,
    configure,
)


# Test ToolConfig initialization with defaults
def test_toolconfig_defaults():
    """Test ToolConfig initialization with default values."""
    config = ToolConfig()
    
    assert isinstance(config.project_root, Path)
    assert config.shell_backend == ShellBackend.LOCAL
    assert config.use_mcp is False
    assert config.docker_image == "python:3.11-slim"
    assert config.docker_work_dir == "/workspace"
    assert config.shell_timeout == 30
    assert config.allowed_paths == []


# Test ToolConfig initialization with custom values
def test_toolconfig_custom_values(temp_dir):
    """Test ToolConfig initialization with custom values."""
    config = ToolConfig(
        project_root=str(temp_dir),
        shell_backend=ShellBackend.DOCKER,
        use_mcp=True,
        docker_image="python:3.12-slim",
        docker_work_dir="/app",
        shell_timeout=60,
        allowed_paths=[temp_dir / "src"],
    )
    
    assert config.project_root == temp_dir
    assert config.shell_backend == ShellBackend.DOCKER
    assert config.use_mcp is True
    assert config.docker_image == "python:3.12-slim"
    assert config.docker_work_dir == "/app"
    assert config.shell_timeout == 60
    assert len(config.allowed_paths) == 1
    assert temp_dir / "src" in config.allowed_paths


# Test __post_init__ path normalization
def test_toolconfig_post_init_path_normalization(temp_dir):
    """Test __post_init__ normalizes paths correctly."""
    # Test with string path
    config = ToolConfig(project_root=str(temp_dir))
    assert isinstance(config.project_root, Path)
    assert config.project_root.is_absolute()
    
    # Test with relative path
    config = ToolConfig(project_root="../test")
    assert config.project_root.is_absolute()
    
    # Test allowed_paths normalization
    allowed = [temp_dir / "src", str(temp_dir / "tests")]
    config = ToolConfig(allowed_paths=allowed)
    assert all(isinstance(p, Path) for p in config.allowed_paths)
    assert all(p.is_absolute() for p in config.allowed_paths)


# Test __post_init__ shell_backend conversion
def test_toolconfig_post_init_shell_backend():
    """Test __post_init__ converts string shell_backend to enum."""
    config = ToolConfig(shell_backend="docker")
    assert isinstance(config.shell_backend, ShellBackend)
    assert config.shell_backend == ShellBackend.DOCKER


# Test is_path_allowed with no restrictions
def test_is_path_allowed_no_restrictions(sample_config):
    """Test is_path_allowed allows all paths under project root."""
    project_root = sample_config.project_root
    
    # Paths within project root should be allowed
    assert sample_config.is_path_allowed(project_root)
    assert sample_config.is_path_allowed(project_root / "src")
    assert sample_config.is_path_allowed(project_root / "src" / "file.py")
    assert sample_config.is_path_allowed(project_root / "nested" / "deep" / "file.txt")


# Test is_path_allowed with no restrictions - outside project root
def test_is_path_allowed_no_restrictions_outside(sample_config):
    """Test is_path_allowed rejects paths outside project root when no restrictions."""
    project_root = sample_config.project_root
    
    # Paths outside project root should be rejected
    assert not sample_config.is_path_allowed(Path("/tmp"))
    assert not sample_config.is_path_allowed(Path("/etc") / "hosts")
    assert not sample_config.is_path_allowed(project_root.parent / "other")


# Test is_path_allowed with specific allowed paths
def test_is_path_allowed_with_restrictions(restricted_config):
    """Test is_path_allowed with specific allowed paths list."""
    temp_dir = restricted_config.project_root
    allowed_dir = temp_dir / "allowed"
    
    # Paths within allowed directory should be allowed
    assert restricted_config.is_path_allowed(allowed_dir)
    assert restricted_config.is_path_allowed(allowed_dir / "file.py")
    assert restricted_config.is_path_allowed(allowed_dir / "nested" / "deep")
    
    # Paths outside allowed directory should be rejected
    assert not restricted_config.is_path_allowed(temp_dir)
    assert not restricted_config.is_path_allowed(temp_dir / "other")
    assert not restricted_config.is_path_allowed(Path("/tmp"))


# Test is_path_allowed with multiple allowed paths
def test_is_path_allowed_multiple_allowed(temp_dir):
    """Test is_path_allowed with multiple allowed paths."""
    src_dir = temp_dir / "src"
    tests_dir = temp_dir / "tests"
    
    config = ToolConfig(
        project_root=temp_dir,
        allowed_paths=[src_dir, tests_dir]
    )
    
    # Both allowed directories should be accessible
    assert config.is_path_allowed(src_dir)
    assert config.is_path_allowed(tests_dir)
    assert config.is_path_allowed(src_dir / "file.py")
    assert config.is_path_allowed(tests_dir / "test.py")
    
    # Other paths should be rejected
    assert not config.is_path_allowed(temp_dir)
    assert not config.is_path_allowed(temp_dir / "docs")


# Test resolve_path with relative paths
def test_resolve_path_relative(temp_dir):
    """Test resolve_path with relative paths."""
    config = ToolConfig(project_root=temp_dir)
    
    resolved = config.resolve_path("file.txt")
    assert resolved == temp_dir / "file.txt"
    
    resolved = config.resolve_path("src/module.py")
    assert resolved == temp_dir / "src" / "module.py"
    
    resolved = config.resolve_path("../other")
    assert resolved == temp_dir.parent / "other"


# Test resolve_path with absolute paths
def test_resolve_path_absolute(temp_dir):
    """Test resolve_path with absolute paths."""
    config = ToolConfig(project_root=temp_dir)
    
    abs_path = Path("/tmp") / "file.txt"
    resolved = config.resolve_path(abs_path)
    assert resolved == abs_path
    
    resolved = config.resolve_path("/etc/hosts")
    assert resolved == Path("/etc/hosts")


# Test resolve_path raises ValueError for disallowed paths
def test_resolve_path_disallowed(temp_dir):
    """Test resolve_path raises ValueError for disallowed paths."""
    config = ToolConfig(project_root=temp_dir)
    
    # Path outside project root
    with pytest.raises(ValueError, match="outside allowed boundaries"):
        config.resolve_path("/etc/hosts")
    
    # Path outside project root (parent directory)
    with pytest.raises(ValueError, match="outside allowed boundaries"):
        config.resolve_path("../sibling")


# Test resolve_path raises ValueError with restrictions
def test_resolve_path_restricted(restricted_config):
    """Test resolve_path with restricted allowed paths."""
    temp_dir = restricted_config.project_root
    
    # Path outside allowed directory
    with pytest.raises(ValueError, match="outside allowed boundaries"):
        restricted_config.resolve_path("file.txt")
    
    with pytest.raises(ValueError, match="outside allowed boundaries"):
        restricted_config.resolve_path(str(temp_dir / "other"))
    
    # Path within allowed directory should work
    resolved = restricted_config.resolve_path("allowed/file.txt")
    assert resolved == temp_dir / "allowed" / "file.txt"


# Test get_config returns singleton
def test_get_config_singleton():
    """Test get_config returns the same instance across calls."""
    config1 = get_config()
    config2 = get_config()
    
    assert config1 is config2
    assert id(config1) == id(config2)


# Test get_config creates default config
def test_get_config_creates_default():
    """Test get_config creates default config when none exists."""
    from otter_code.config import _config
    
    # Ensure config is None
    _config = None
    
    config = get_config()
    assert isinstance(config, ToolConfig)
    assert config.shell_backend == ShellBackend.LOCAL


# Test set_config changes global config
def test_set_config():
    """Test set_config changes the global configuration."""
    from otter_code.config import _config
    
    # Reset to None
    _config = None
    
    config1 = get_config()
    assert config1.shell_timeout == 30
    
    config2 = ToolConfig(shell_timeout=60)
    set_config(config2)
    
    config3 = get_config()
    assert config3 is config2
    assert config3.shell_timeout == 60


# Test configure creates and sets config
def test_configure():
    """Test configure creates and sets a new config."""
    from otter_code.config import _config
    
    _config = None
    
    config = configure(
        shell_timeout=45,
        use_mcp=True,
        shell_backend="docker"
    )
    
    assert isinstance(config, ToolConfig)
    assert config.shell_timeout == 45
    assert config.use_mcp is True
    assert config.shell_backend == ShellBackend.DOCKER
    
    # Verify it's the global config
    assert get_config() is config


# Test configure with existing config
def test_configure_overrides_existing():
    """Test configure overrides existing config."""
    config1 = configure(shell_timeout=30)
    assert config1.shell_timeout == 30
    
    config2 = configure(shell_timeout=90)
    assert config2.shell_timeout == 90
    
    # Global config should be updated
    assert get_config().shell_timeout == 90