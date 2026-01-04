"""Local persistent shell backend using SWE-ReX.

This module provides a persistent bash shell session that maintains state
(environment variables, working directory) across multiple command executions
using SWE-ReX's LocalDeployment.
"""

import asyncio
import os
from pathlib import Path
from typing import Optional, Tuple

from swerex.deployment.local import LocalDeployment
from swerex.runtime.abstract import BashAction, CreateBashSessionRequest


class LocalShellBackend:
    """Persistent local shell session using SWE-ReX.
    
    This backend maintains a bash session that persists across multiple
    command executions, preserving environment variables, aliases, and
    the current working directory.
    """
    
    SESSION_NAME = "dspy_shell"
    
    def __init__(
        self, 
        working_directory: Optional[str] = None,
        env: Optional[dict[str, str]] = None,
    ):
        """Initialize the local shell backend.
        
        Args:
            working_directory: Initial working directory. Defaults to cwd.
            env: Additional environment variables to set.
        """
        self.working_directory = Path(working_directory or os.getcwd()).resolve()
        self.env = env or {}
        self._deployment: Optional[LocalDeployment] = None
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
        """Start the shell session asynchronously."""
        if self._started and self._deployment is not None:
            return
        
        self._deployment = LocalDeployment()
        await self._deployment.start()
        self._runtime = self._deployment.runtime
        
        # Create a persistent bash session
        await self._runtime.create_session(
            CreateBashSessionRequest(session=self.SESSION_NAME)
        )
        
        self._started = True
        
        # Set initial working directory
        if self.working_directory:
            await self._runtime.run_in_session(
                BashAction(
                    command=f'cd "{self.working_directory}"',
                    session=self.SESSION_NAME,
                )
            )
        
        # Set environment variables
        for name, value in self.env.items():
            await self._runtime.run_in_session(
                BashAction(
                    command=f'export {name}="{value}"',
                    session=self.SESSION_NAME,
                )
            )
    
    def start(self) -> None:
        """Start the shell session."""
        self._run_sync(self._start_async())
    
    async def _stop_async(self) -> None:
        """Stop the shell session asynchronously."""
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
        """Stop the shell session."""
        if self._deployment is not None:
            self._run_sync(self._stop_async())
    
    def is_running(self) -> bool:
        """Check if the shell session is running."""
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
        """Execute a command in the persistent shell.
        
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
        """Get the current working directory of the shell.
        
        Returns:
            The current working directory path.
        """
        output, _ = self.run("pwd")
        return output.strip()
    
    def set_working_directory(self, path: str) -> None:
        """Change the shell's working directory.
        
        Args:
            path: The directory to change to.
            
        Raises:
            ValueError: If the directory doesn't exist.
        """
        output, exit_code = self.run(f'cd "{path}" && pwd')
        if exit_code != 0:
            raise ValueError(f"Failed to change directory to {path}: {output}")
    
    def get_environment_variable(self, name: str) -> Optional[str]:
        """Get an environment variable value.
        
        Args:
            name: The environment variable name.
            
        Returns:
            The value, or None if not set.
        """
        output, exit_code = self.run(f'echo "${name}"')
        value = output.strip()
        return value if value else None
    
    def set_environment_variable(self, name: str, value: str) -> None:
        """Set an environment variable.
        
        Args:
            name: The environment variable name.
            value: The value to set.
        """
        self.run(f'export {name}="{value}"')
    
    def reset(self) -> None:
        """Reset the shell session to a clean state."""
        self.stop()
        self.start()
    
    def __enter__(self) -> "LocalShellBackend":
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
_shell_instance: Optional[LocalShellBackend] = None


def get_local_shell(
    working_directory: Optional[str] = None,
    reset: bool = False
) -> LocalShellBackend:
    """Get or create the persistent local shell instance.
    
    Args:
        working_directory: Initial working directory (only used on first call).
        reset: If True, reset the existing shell session.
        
    Returns:
        The LocalShellBackend instance.
    """
    global _shell_instance
    
    if _shell_instance is None:
        _shell_instance = LocalShellBackend(working_directory=working_directory)
        _shell_instance.start()
    elif reset:
        _shell_instance.reset()
    
    return _shell_instance


def close_local_shell() -> None:
    """Close the persistent local shell instance."""
    global _shell_instance
    
    if _shell_instance is not None:
        _shell_instance.stop()
        _shell_instance = None
