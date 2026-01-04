"""Configuration for DSPy Coding Agent tools."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional


class ShellBackend(Enum):
    """Available shell execution backends."""
    LOCAL = "local"
    DOCKER = "docker"


@dataclass
class ToolConfig:
    """Configuration for the coding agent tools.
    
    Attributes:
        project_root: Root directory for file operations. Defaults to current directory.
        shell_backend: Backend for shell execution ('local' or 'docker').
        use_mcp: Whether to use MCP for filesystem operations.
        docker_image: Docker image to use for sandboxed execution.
        docker_work_dir: Working directory inside the Docker container.
        shell_timeout: Default timeout for shell commands in seconds.
        allowed_paths: List of paths the agent is allowed to access. Empty means all paths.
    """
    project_root: Path = field(default_factory=Path.cwd)
    shell_backend: ShellBackend = ShellBackend.LOCAL
    use_mcp: bool = False
    docker_image: str = "python:3.11-slim"
    docker_work_dir: str = "/workspace"
    shell_timeout: int = 30
    allowed_paths: list[Path] = field(default_factory=list)
    
    def __post_init__(self):
        """Normalize paths after initialization."""
        if isinstance(self.project_root, str):
            self.project_root = Path(self.project_root)
        self.project_root = self.project_root.resolve()
        
        if isinstance(self.shell_backend, str):
            self.shell_backend = ShellBackend(self.shell_backend)
        
        self.allowed_paths = [
            Path(p).resolve() if isinstance(p, str) else p.resolve() 
            for p in self.allowed_paths
        ]
    
    def is_path_allowed(self, path: Path) -> bool:
        """Check if a path is within allowed boundaries.
        
        Args:
            path: Path to check.
            
        Returns:
            True if the path is allowed, False otherwise.
        """
        path = path.resolve()
        
        # If no restrictions, check if within project root
        if not self.allowed_paths:
            try:
                path.relative_to(self.project_root)
                return True
            except ValueError:
                return False
        
        # Check against allowed paths
        for allowed in self.allowed_paths:
            try:
                path.relative_to(allowed)
                return True
            except ValueError:
                continue
        return False
    
    def resolve_path(self, path: str | Path) -> Path:
        """Resolve a path relative to project root.
        
        Args:
            path: Path to resolve (can be relative or absolute).
            
        Returns:
            Resolved absolute path.
            
        Raises:
            ValueError: If the path is outside allowed boundaries.
        """
        if isinstance(path, str):
            path = Path(path)
        
        if not path.is_absolute():
            path = self.project_root / path
        
        path = path.resolve()
        
        if not self.is_path_allowed(path):
            raise ValueError(f"Path '{path}' is outside allowed boundaries")
        
        return path


# Global configuration instance
_config: Optional[ToolConfig] = None


def get_config() -> ToolConfig:
    """Get the current tool configuration.
    
    Returns:
        The current ToolConfig instance.
    """
    global _config
    if _config is None:
        _config = ToolConfig()
    return _config


def set_config(config: ToolConfig) -> None:
    """Set the global tool configuration.
    
    Args:
        config: The ToolConfig to use.
    """
    global _config
    _config = config


def configure(**kwargs) -> ToolConfig:
    """Configure tools with the given settings.
    
    Args:
        **kwargs: Configuration options to pass to ToolConfig.
        
    Returns:
        The new ToolConfig instance.
    """
    config = ToolConfig(**kwargs)
    set_config(config)
    return config

