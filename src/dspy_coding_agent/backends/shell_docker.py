"""Docker-based sandboxed shell backend using SWE-ReX.

This module provides a containerized shell execution environment for
secure, isolated command execution using SWE-ReX's DockerDeployment.
The container persists across multiple commands to maintain state.
"""

import asyncio
import os
from pathlib import Path
from typing import Optional, Tuple

from swerex.deployment.docker import DockerDeployment
from swerex.runtime.abstract import BashAction, CreateBashSessionRequest


class DockerShellBackend:
    """Docker-based sandboxed shell execution using SWE-ReX.
    
    This backend runs commands in a Docker container, providing isolation
    from the host system. The container persists to maintain state across
    multiple command executions.
    """
    
    DEFAULT_IMAGE = "python:3.11-slim"
    CONTAINER_WORK_DIR = "/workspace"
    SESSION_NAME = "dspy_docker_shell"
    
    def __init__(
        self,
        project_root: Optional[str] = None,
        image: str = DEFAULT_IMAGE,
        work_dir: str = CONTAINER_WORK_DIR,
    ):
        """Initialize the Docker shell backend.
        
        Args:
            project_root: Local directory to mount as workspace.
            image: Docker image to use.
            work_dir: Working directory inside the container.
        """
        self.project_root = Path(project_root or os.getcwd()).resolve()
        self.image = image
        self.work_dir = work_dir
        
        self._deployment: Optional[DockerDeployment] = None
        self._runtime = None
        self._started = False
        self._loop: Optional[asyncio.AbstractEventLoop] = None
    
    def _get_event_loop(self):
        """Get or create an event loop."""
        if self._loop is None or self._loop.is_closed():
            try:
                self._loop = asyncio.get_running_loop()
            except RuntimeError:
                self._loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self._loop)
        return self._loop
    
    def _run_sync(self, coro):
        """Run an async coroutine synchronously."""
        loop = self._get_event_loop()
        return loop.run_until_complete(coro)
    
    async def _start_async(self) -> None:
        """Start the Docker container asynchronously."""
        if self._started and self._deployment is not None:
            return
        
        # Configure the Docker deployment with volume mount
        self._deployment = DockerDeployment(
            image=self.image,
            docker_args=[
                "-v", f"{self.project_root}:{self.work_dir}",
                "-w", self.work_dir,
            ],
        )
        
        await self._deployment.start()
        self._runtime = self._deployment.runtime
        
        # Create a persistent bash session
        await self._runtime.create_session(
            CreateBashSessionRequest(session=self.SESSION_NAME)
        )
        
        self._started = True
        
        # Set initial working directory
        await self._runtime.run_in_session(
            BashAction(
                command=f'cd "{self.work_dir}"',
                session=self.SESSION_NAME,
            )
        )
    
    def start(self) -> None:
        """Start the Docker container."""
        self._run_sync(self._start_async())
    
    async def _stop_async(self) -> None:
        """Stop the Docker container asynchronously."""
        if self._deployment is not None:
            try:
                await self._deployment.stop()
            except Exception:
                pass
            finally:
                self._deployment = None
                self._runtime = None
                self._started = False
    
    def stop(self) -> None:
        """Stop and remove the Docker container."""
        if self._deployment is not None:
            self._run_sync(self._stop_async())
    
    def is_running(self) -> bool:
        """Check if the container is running."""
        return self._started and self._deployment is not None
    
    async def _execute_async(self, command: str, timeout: int = 30) -> Tuple[str, int]:
        """Execute a command asynchronously.
        
        Args:
            command: The command to execute.
            timeout: Maximum time to wait for command completion.
            
        Returns:
            Tuple of (output, exit_code).
        """
        if not self.is_running():
            await self._start_async()
        
        try:
            result = await self._runtime.run_in_session(
                BashAction(
                    command=command,
                    session=self.SESSION_NAME,
                    timeout=timeout,
                )
            )
            return (result.output.strip(), result.exit_code)
        except asyncio.TimeoutError:
            raise TimeoutError(f"Command timed out after {timeout}s")
        except Exception as e:
            return (str(e), -1)
    
    def run(self, command: str, timeout: int = 30) -> Tuple[str, int]:
        """Execute a command in the Docker container.
        
        Args:
            command: The command to execute.
            timeout: Maximum time to wait for command completion.
            
        Returns:
            Tuple of (output, exit_code).
            
        Raises:
            TimeoutError: If the command times out.
        """
        return self._run_sync(self._execute_async(command, timeout))
    
    def get_working_directory(self) -> str:
        """Get the current working directory in the container.
        
        Returns:
            The current working directory path.
        """
        output, _ = self.run("pwd")
        return output.strip()
    
    def set_working_directory(self, path: str) -> None:
        """Change the working directory for subsequent commands.
        
        Args:
            path: The directory to change to.
            
        Raises:
            ValueError: If the directory doesn't exist.
        """
        output, exit_code = self.run(f'cd "{path}" && pwd')
        if exit_code != 0:
            raise ValueError(f"Directory does not exist: {path}")
        self.work_dir = path
    
    def reset(self) -> None:
        """Reset the container to a clean state."""
        self.stop()
        self.start()
    
    def get_container_info(self) -> dict:
        """Get information about the running container.
        
        Returns:
            Dictionary with container information.
        """
        return {
            "status": "running" if self.is_running() else "stopped",
            "image": self.image,
            "work_dir": self.work_dir,
            "project_root": str(self.project_root),
        }
    
    def __enter__(self) -> "DockerShellBackend":
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.stop()
    
    def __del__(self):
        """Cleanup on deletion."""
        try:
            if self._deployment is not None and self._loop is not None:
                if not self._loop.is_closed():
                    self._loop.run_until_complete(self._stop_async())
        except Exception:
            pass


# Module-level singleton for persistent session
_docker_shell_instance: Optional[DockerShellBackend] = None


def get_docker_shell(
    project_root: Optional[str] = None,
    image: str = DockerShellBackend.DEFAULT_IMAGE,
    reset: bool = False
) -> DockerShellBackend:
    """Get or create the persistent Docker shell instance.
    
    Args:
        project_root: Local directory to mount (only used on first call).
        image: Docker image to use (only used on first call).
        reset: If True, reset the existing container.
        
    Returns:
        The DockerShellBackend instance.
    """
    global _docker_shell_instance
    
    if _docker_shell_instance is None:
        _docker_shell_instance = DockerShellBackend(
            project_root=project_root,
            image=image
        )
        _docker_shell_instance.start()
    elif reset:
        _docker_shell_instance.reset()
    
    return _docker_shell_instance


def close_docker_shell() -> None:
    """Close the persistent Docker shell instance."""
    global _docker_shell_instance
    
    if _docker_shell_instance is not None:
        _docker_shell_instance.stop()
        _docker_shell_instance = None
