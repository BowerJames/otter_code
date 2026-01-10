"""Shell execution tools with configurable backends.

These tools provide the agent with the ability to execute shell commands
in a persistent session, supporting both local and Docker-based execution.

The backends use SWE-ReX (SWE-agent Remote Execution) for robust persistent
shell sessions with proper command completion detection.
"""

from typing import Optional, Tuple, Protocol, runtime_checkable

from ..config import get_config, ShellBackend
from ..backends.shell_local import LocalShellBackend, get_local_shell, close_local_shell
from ..backends.shell_docker import DockerShellBackend, get_docker_shell, close_docker_shell


@runtime_checkable
class ShellBackendProtocol(Protocol):
    """Protocol defining the shell backend interface."""
    
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def is_running(self) -> bool: ...
    def run(self, command: str, timeout: int = 30) -> Tuple[str, int]: ...
    def get_working_directory(self) -> str: ...
    def reset(self) -> None: ...


# Current active shell backend
_current_backend: Optional[ShellBackendProtocol] = None


def _get_shell_backend() -> ShellBackendProtocol:
    """Get the appropriate shell backend based on configuration."""
    global _current_backend
    
    config = get_config()
    
    if _current_backend is not None:
        return _current_backend
    
    if config.shell_backend == ShellBackend.DOCKER:
        _current_backend = get_docker_shell(
            project_root=str(config.project_root),
            image=config.docker_image
        )
    else:
        _current_backend = get_local_shell(
            working_directory=str(config.project_root)
        )
    
    return _current_backend


def execute_bash(command: str, timeout: int = 30) -> str:
    """Execute a bash command in a persistent shell session.
    
    The shell session persists across multiple calls, maintaining:
    - Environment variables set by previous commands
    - Current working directory changes
    - Shell aliases and functions
    
    Args:
        command: The bash command to execute.
        timeout: Maximum time in seconds to wait for the command.
                 Defaults to 30 seconds.
        
    Returns:
        The command output (stdout and stderr combined).
        If the command fails, returns the error message with exit code.
        
    Example:
        >>> execute_bash("echo 'Hello, World!'")
        'Hello, World!'
        
        >>> execute_bash("export MY_VAR=test")
        ''
        
        >>> execute_bash("echo $MY_VAR")
        'test'
    """
    config = get_config()
    backend = _get_shell_backend()
    
    try:
        output, exit_code = backend.run(command, timeout=timeout)
        
        if exit_code == 0:
            return output
        else:
            return f"{output}\n[Exit code: {exit_code}]" if output else f"[Exit code: {exit_code}]"
            
    except TimeoutError as e:
        return f"Command timed out after {timeout} seconds: {str(e)}"
    except Exception as e:
        return f"Error executing command: {str(e)}"


def execute_bash_with_status(command: str, timeout: int = 30) -> dict:
    """Execute a bash command and return structured result.
    
    Similar to execute_bash but returns a dictionary with separate
    output and exit code fields.
    
    Args:
        command: The bash command to execute.
        timeout: Maximum time in seconds to wait for the command.
        
    Returns:
        Dictionary with 'output', 'exit_code', and 'success' fields.
    """
    backend = _get_shell_backend()
    
    try:
        output, exit_code = backend.run(command, timeout=timeout)
        return {
            "output": output,
            "exit_code": exit_code,
            "success": exit_code == 0
        }
    except TimeoutError:
        return {
            "output": f"Command timed out after {timeout} seconds",
            "exit_code": -1,
            "success": False
        }
    except Exception as e:
        return {
            "output": f"Error executing command: {str(e)}",
            "exit_code": -1,
            "success": False
        }


def get_working_directory() -> str:
    """Get the current working directory of the shell session.
    
    Returns:
        The absolute path of the current working directory.
    """
    backend = _get_shell_backend()
    
    try:
        return backend.get_working_directory()
    except Exception as e:
        return f"Error getting working directory: {str(e)}"


def change_directory(path: str) -> str:
    """Change the shell's current working directory.
    
    Args:
        path: The directory to change to. Can be relative or absolute.
        
    Returns:
        The new working directory path, or an error message.
    """
    backend = _get_shell_backend()
    
    try:
        output, exit_code = backend.run(f'cd "{path}" && pwd')
        
        if exit_code == 0:
            return f"Changed directory to: {output.strip()}"
        else:
            return f"Failed to change directory: {output}"
            
    except Exception as e:
        return f"Error changing directory: {str(e)}"


def reset_shell_session() -> str:
    """Reset the shell session to a clean state.
    
    This clears all environment variables, aliases, and returns
    to the initial working directory.
    
    Returns:
        A confirmation message.
    """
    backend = _get_shell_backend()
    
    try:
        backend.reset()
        return "Shell session reset successfully"
    except Exception as e:
        return f"Error resetting shell session: {str(e)}"


def get_shell_info() -> str:
    """Get information about the current shell session.
    
    Returns:
        A formatted string with shell session details.
    """
    config = get_config()
    backend = _get_shell_backend()
    
    info_lines = [
        f"Backend: {config.shell_backend.value}",
        f"Running: {backend.is_running()}",
    ]
    
    if backend.is_running():
        try:
            cwd = backend.get_working_directory()
            info_lines.append(f"Working Directory: {cwd}")
        except Exception:
            info_lines.append("Working Directory: (unable to determine)")
    
    if config.shell_backend == ShellBackend.DOCKER:
        info_lines.append(f"Docker Image: {config.docker_image}")
    
    return "\n".join(info_lines)


def run_python(code: str, timeout: int = 60) -> str:
    """Execute Python code in the shell session.
    
    This is a convenience wrapper that runs Python code using
    the python3 interpreter in the shell.
    
    Args:
        code: Python code to execute.
        timeout: Maximum time in seconds to wait.
        
    Returns:
        The output from running the Python code.
    """
    # Escape quotes and format for shell
    escaped_code = code.replace("'", "'\"'\"'")
    command = f"python3 -c '{escaped_code}'"
    
    return execute_bash(command, timeout=timeout)


def run_script(script_path: str, args: str = "", timeout: int = 60) -> str:
    """Execute a script file in the shell session.
    
    Args:
        script_path: Path to the script to execute.
        args: Additional arguments to pass to the script.
        timeout: Maximum time in seconds to wait.
        
    Returns:
        The output from running the script.
    """
    command = f'"{script_path}"'
    if args:
        command += f" {args}"
    
    return execute_bash(command, timeout=timeout)


def install_package(package: str, use_pip: bool = True) -> str:
    """Install a package using pip or the system package manager.
    
    Args:
        package: Name of the package to install.
        use_pip: If True, use pip. Otherwise, try apt-get.
        
    Returns:
        The output from the installation command.
    """
    if use_pip:
        command = f"pip install {package}"
    else:
        command = f"apt-get update && apt-get install -y {package}"
    
    return execute_bash(command, timeout=120)


def close_shell() -> None:
    """Close the current shell session.
    
    This should be called when done using shell tools to clean up
    resources (especially for Docker backend).
    """
    global _current_backend
    
    config = get_config()
    
    if config.shell_backend == ShellBackend.DOCKER:
        close_docker_shell()
    else:
        close_local_shell()
    
    _current_backend = None

