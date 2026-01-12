"""Tests for shell tools."""

from unittest.mock import Mock, patch, MagicMock
import pytest

from otter_code.config import ToolConfig, ShellBackend, set_config
from otter_code.tools import shell
from otter_code.backends.shell_local import LocalShellBackend
from otter_code.backends.shell_docker import DockerShellBackend


@pytest.fixture
def mock_backend():
    """Create a mock shell backend."""
    backend = Mock(spec=LocalShellBackend)
    backend.is_running.return_value = True
    backend.get_working_directory.return_value = "/workspace"
    backend.run.return_value = ("output", 0)
    return backend


@pytest.fixture
def reset_shell_backend():
    """Reset the shell backend between tests."""
    shell._current_backend = None
    yield
    shell._current_backend = None


# Test execute_bash successful execution
def test_execute_bash_success(mock_backend, reset_shell_backend):
    """Test execute_bash executes command successfully."""
    mock_backend.run.return_value = ("Hello, World!", 0)
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        result = shell.execute_bash("echo 'Hello, World!'")
        
        mock_backend.run.assert_called_once_with("echo 'Hello, World!'", timeout=30)
        assert result == "Hello, World!"


# Test execute_bash with custom timeout
def test_execute_bash_custom_timeout(mock_backend, reset_shell_backend):
    """Test execute_bash with custom timeout."""
    mock_backend.run.return_value = ("output", 0)
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        shell.execute_bash("sleep 1", timeout=60)
        
        mock_backend.run.assert_called_once_with("sleep 1", timeout=60)


# Test execute_bash with non-zero exit code
def test_execute_bash_nonzero_exit(mock_backend, reset_shell_backend):
    """Test execute_bash handles non-zero exit code."""
    mock_backend.run.return_value = ("Error occurred", 1)
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        result = shell.execute_bash("false")
        
        assert "Error occurred" in result
        assert "[Exit code: 1]" in result


# Test execute_bash with empty output and non-zero exit
def test_execute_bash_empty_output_error(mock_backend, reset_shell_backend):
    """Test execute_bash with empty output and non-zero exit."""
    mock_backend.run.return_value = ("", 127)
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        result = shell.execute_bash("nonexistent_command")
        
        assert "[Exit code: 127]" in result


# Test execute_bash timeout handling
def test_execute_bash_timeout(mock_backend, reset_shell_backend):
    """Test execute_bash handles timeout errors."""
    mock_backend.run.side_effect = TimeoutError("Command timed out")
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        result = shell.execute_bash("sleep 100")
        
        assert "timed out" in result.lower()
        assert "30 seconds" in result


# Test execute_bash general exception handling
def test_execute_bash_exception(mock_backend, reset_shell_backend):
    """Test execute_bash handles general exceptions."""
    mock_backend.run.side_effect = RuntimeError("Backend error")
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        result = shell.execute_bash("command")
        
        assert "Error executing command" in result
        assert "Backend error" in result


# Test execute_bash_with_status success
def test_execute_bash_with_status_success(mock_backend, reset_shell_backend):
    """Test execute_bash_with_status returns structured result."""
    mock_backend.run.return_value = ("output", 0)
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        result = shell.execute_bash_with_status("command")
        
        assert isinstance(result, dict)
        assert result["output"] == "output"
        assert result["exit_code"] == 0
        assert result["success"] is True


# Test execute_bash_with_status failure
def test_execute_bash_with_status_failure(mock_backend, reset_shell_backend):
    """Test execute_bash_with_status with non-zero exit code."""
    mock_backend.run.return_value = ("error output", 1)
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        result = shell.execute_bash_with_status("command")
        
        assert result["output"] == "error output"
        assert result["exit_code"] == 1
        assert result["success"] is False


# Test execute_bash_with_status timeout
def test_execute_bash_with_status_timeout(mock_backend, reset_shell_backend):
    """Test execute_bash_with_status handles timeout."""
    mock_backend.run.side_effect = TimeoutError()
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        result = shell.execute_bash_with_status("command")
        
        assert result["exit_code"] == -1
        assert result["success"] is False
        assert "timed out" in result["output"].lower()


# Test get_working_directory
def test_get_working_directory(mock_backend, reset_shell_backend):
    """Test get_working_directory returns current directory."""
    mock_backend.get_working_directory.return_value = "/workspace"
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        result = shell.get_working_directory()
        
        assert result == "/workspace"
        mock_backend.get_working_directory.assert_called_once()


# Test get_working_directory error handling
def test_get_working_directory_error(mock_backend, reset_shell_backend):
    """Test get_working_directory handles errors."""
    mock_backend.get_working_directory.side_effect = RuntimeError("Not running")
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        result = shell.get_working_directory()
        
        assert "Error getting working directory" in result


# Test change_directory success
def test_change_directory_success(mock_backend, reset_shell_backend):
    """Test change_directory successfully changes directory."""
    mock_backend.run.return_value = ("/new/path\n", 0)
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        result = shell.change_directory("/new/path")
        
        assert "Changed directory to:" in result
        assert "/new/path" in result
        mock_backend.run.assert_called_once()


# Test change_directory failure
def test_change_directory_failure(mock_backend, reset_shell_backend):
    """Test change_directory handles failure."""
    mock_backend.run.return_value = ("No such directory", 1)
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        result = shell.change_directory("/nonexistent")
        
        assert "Failed to change directory" in result
        assert "No such directory" in result


# Test change_directory error handling
def test_change_directory_error(mock_backend, reset_shell_backend):
    """Test change_directory handles exceptions."""
    mock_backend.run.side_effect = RuntimeError("Backend error")
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        result = shell.change_directory("/path")
        
        assert "Error changing directory" in result


# Test reset_shell_session
def test_reset_shell_session(mock_backend, reset_shell_backend):
    """Test reset_shell_session resets the backend."""
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        result = shell.reset_shell_session()
        
        assert "reset successfully" in result.lower()
        mock_backend.reset.assert_called_once()


# Test reset_shell_session error handling
def test_reset_shell_session_error(mock_backend, reset_shell_backend):
    """Test reset_shell_session handles errors."""
    mock_backend.reset.side_effect = RuntimeError("Cannot reset")
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        result = shell.reset_shell_session()
        
        assert "error resetting" in result.lower()


# Test get_shell_info local backend
def test_get_shell_info_local(mock_backend, reset_shell_backend):
    """Test get_shell_info with local backend."""
    set_config(ToolConfig(shell_backend=ShellBackend.LOCAL))
    mock_backend.is_running.return_value = True
    mock_backend.get_working_directory.return_value = "/workspace"
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        result = shell.get_shell_info()
        
        assert "Backend: local" in result
        assert "Running: True" in result
        assert "Working Directory: /workspace" in result


# Test get_shell_info docker backend
def test_get_shell_info_docker(mock_backend, reset_shell_backend):
    """Test get_shell_info with docker backend."""
    set_config(ToolConfig(
        shell_backend=ShellBackend.DOCKER,
        docker_image="python:3.11-slim"
    ))
    mock_backend.is_running.return_value = True
    mock_backend.get_working_directory.return_value = "/workspace"
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        result = shell.get_shell_info()
        
        assert "Backend: docker" in result
        assert "Docker Image: python:3.11-slim" in result


# Test get_shell_info not running
def test_get_shell_info_not_running(mock_backend, reset_shell_backend):
    """Test get_shell_info when backend is not running."""
    mock_backend.is_running.return_value = False
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        result = shell.get_shell_info()
        
        assert "Running: False" in result


# Test run_python
def test_run_python(mock_backend, reset_shell_backend):
    """Test run_python executes Python code."""
    mock_backend.run.return_value = ("42", 0)
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        result = shell.run_python("print(42)")
        
        mock_backend.run.assert_called_once()
        call_args = mock_backend.run.call_args[0]
        assert "python3" in call_args[0]
        assert "print(42)" in call_args[0]
        assert result == "42"


# Test run_python with timeout
def test_run_python_timeout(mock_backend, reset_shell_backend):
    """Test run_python with custom timeout."""
    mock_backend.run.return_value = ("", 0)
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        shell.run_python("print('test')", timeout=120)
        
        call_args = mock_backend.run.call_args
        assert call_args[1]["timeout"] == 120


# Test run_script
def test_run_script(mock_backend, reset_shell_backend):
    """Test run_script executes a script."""
    mock_backend.run.return_value = ("Script output", 0)
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        result = shell.run_script("/path/to/script.sh")
        
        mock_backend.run.assert_called_once()
        call_args = mock_backend.run.call_args[0]
        assert '/path/to/script.sh' in call_args[0]
        assert result == "Script output"


# Test run_script with args
def test_run_script_with_args(mock_backend, reset_shell_backend):
    """Test run_script with arguments."""
    mock_backend.run.return_value = ("", 0)
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        shell.run_script("/path/to/script.sh", args="--verbose --output result.txt")
        
        call_args = mock_backend.run.call_args[0]
        assert "--verbose" in call_args[0]
        assert "--output" in call_args[0]


# Test install_package with pip
def test_install_package_pip(mock_backend, reset_shell_backend):
    """Test install_package using pip."""
    mock_backend.run.return_value = ("Successfully installed", 0)
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        result = shell.install_package("requests")
        
        call_args = mock_backend.run.call_args
        assert "pip install" in call_args[0][0]
        assert "requests" in call_args[0][0]
        assert call_args[1]["timeout"] == 120


# Test install_package with apt
def test_install_package_apt(mock_backend, reset_shell_backend):
    """Test install_package using apt-get."""
    mock_backend.run.return_value = ("", 0)
    
    with patch.object(shell, '_get_shell_backend', return_value=mock_backend):
        shell.install_package("curl", use_pip=False)
        
        call_args = mock_backend.run.call_args[0]
        assert "apt-get update" in call_args[0]
        assert "apt-get install" in call_args[0]
        assert "curl" in call_args[0]


# Test close_shell local backend
def test_close_shell_local(reset_shell_backend):
    """Test close_shell with local backend."""
    set_config(ToolConfig(shell_backend=ShellBackend.LOCAL))
    shell._current_backend = Mock()
    
    with patch('otter_code.tools.shell.close_local_shell') as mock_close:
        shell.close_shell()
        
        mock_close.assert_called_once()
        assert shell._current_backend is None


# Test close_shell docker backend
def test_close_shell_docker(reset_shell_backend):
    """Test close_shell with docker backend."""
    set_config(ToolConfig(shell_backend=ShellBackend.DOCKER))
    shell._current_backend = Mock()
    
    with patch('otter_code.tools.shell.close_docker_shell') as mock_close:
        shell.close_shell()
        
        mock_close.assert_called_once()
        assert shell._current_backend is None


# Test _get_shell_backend returns cached
def test_get_shell_backend_cached(mock_backend, reset_shell_backend):
    """Test _get_shell_backend returns cached backend."""
    shell._current_backend = mock_backend
    
    result = shell._get_shell_backend()
    
    assert result is mock_backend


# Test _get_shell_backend creates new for local
def test_get_shell_backend_creates_local(reset_shell_backend):
    """Test _get_shell_backend creates new local backend."""
    set_config(ToolConfig(shell_backend=ShellBackend.LOCAL, project_root="/workspace"))
    shell._current_backend = None
    
    with patch('otter_code.tools.shell.get_local_shell') as mock_get:
        mock_get.return_value = mock_backend
        
        result = shell._get_shell_backend()
        
        mock_get.assert_called_once_with(working_directory="/workspace")
        assert result is mock_backend


# Test _get_shell_backend creates new for docker
def test_get_shell_backend_creates_docker(reset_shell_backend):
    """Test _get_shell_backend creates new docker backend."""
    set_config(ToolConfig(
        shell_backend=ShellBackend.DOCKER,
        project_root="/workspace",
        docker_image="python:3.12-slim"
    ))
    shell._current_backend = None
    
    with patch('otter_code.tools.shell.get_docker_shell') as mock_get:
        mock_get.return_value = mock_backend
        
        result = shell._get_shell_backend()
        
        mock_get.assert_called_once_with(project_root="/workspace", image="python:3.12-slim")
        assert result is mock_backend