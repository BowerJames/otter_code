"""Backend implementations for shell execution and MCP integration."""

from .shell_local import LocalShellBackend, get_local_shell, close_local_shell
from .shell_docker import DockerShellBackend, get_docker_shell, close_docker_shell

__all__ = [
    "LocalShellBackend",
    "DockerShellBackend",
    "get_local_shell",
    "close_local_shell",
    "get_docker_shell",
    "close_docker_shell",
]

