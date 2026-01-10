"""Filesystem tools for reading, writing, and searching files.

These tools provide the agent with the ability to interact with the local
filesystem in a controlled manner, respecting the configured project boundaries.
"""

import fnmatch
import os
import re
from pathlib import Path
from typing import Optional

from ..config import get_config


def read_file(path: str) -> str:
    """Read the contents of a file.
    
    Args:
        path: Path to the file to read. Can be relative to project root or absolute.
        
    Returns:
        The contents of the file as a string.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the path is outside allowed boundaries.
    """
    config = get_config()
    resolved_path = config.resolve_path(path)
    
    if not resolved_path.exists():
        raise FileNotFoundError(f"File not found: {path}")
    
    if not resolved_path.is_file():
        raise ValueError(f"Path is not a file: {path}")
    
    return resolved_path.read_text(encoding="utf-8")


def write_file(path: str, content: str) -> str:
    """Write content to a file, creating it if it doesn't exist.
    
    Args:
        path: Path to the file to write. Can be relative to project root or absolute.
        content: The content to write to the file.
        
    Returns:
        A confirmation message indicating success.
        
    Raises:
        ValueError: If the path is outside allowed boundaries.
    """
    config = get_config()
    resolved_path = config.resolve_path(path)
    
    # Create parent directories if they don't exist
    resolved_path.parent.mkdir(parents=True, exist_ok=True)
    
    resolved_path.write_text(content, encoding="utf-8")
    
    return f"Successfully wrote {len(content)} characters to {path}"


def list_directory(path: str = ".", recursive: bool = False) -> str:
    """List contents of a directory.
    
    Args:
        path: Path to the directory to list. Defaults to project root.
        recursive: If True, list contents recursively.
        
    Returns:
        A formatted string listing the directory contents with file/directory indicators.
        
    Raises:
        ValueError: If the path is outside allowed boundaries or not a directory.
    """
    config = get_config()
    resolved_path = config.resolve_path(path)
    
    if not resolved_path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
    
    if not resolved_path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")
    
    entries = []
    
    if recursive:
        for root, dirs, files in os.walk(resolved_path):
            # Skip hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            rel_root = Path(root).relative_to(resolved_path)
            
            for d in sorted(dirs):
                rel_path = rel_root / d if str(rel_root) != '.' else Path(d)
                entries.append(f"[DIR]  {rel_path}/")
            
            for f in sorted(files):
                if f.startswith('.'):
                    continue
                rel_path = rel_root / f if str(rel_root) != '.' else Path(f)
                file_path = Path(root) / f
                size = file_path.stat().st_size
                entries.append(f"[FILE] {rel_path} ({_format_size(size)})")
    else:
        for entry in sorted(resolved_path.iterdir()):
            if entry.name.startswith('.'):
                continue
            
            if entry.is_dir():
                entries.append(f"[DIR]  {entry.name}/")
            else:
                size = entry.stat().st_size
                entries.append(f"[FILE] {entry.name} ({_format_size(size)})")
    
    if not entries:
        return f"Directory '{path}' is empty"
    
    return "\n".join(entries)


def search_files(pattern: str, path: str = ".") -> str:
    """Search for files matching a glob pattern.
    
    Args:
        pattern: Glob pattern to match files (e.g., "*.py", "**/*.txt").
        path: Directory to search in. Defaults to project root.
        
    Returns:
        A newline-separated list of matching file paths.
        
    Raises:
        ValueError: If the path is outside allowed boundaries.
    """
    config = get_config()
    resolved_path = config.resolve_path(path)
    
    if not resolved_path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
    
    if not resolved_path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")
    
    matches = []
    
    # Use rglob for recursive patterns, glob otherwise
    if "**" in pattern:
        for match in resolved_path.rglob(pattern.replace("**/", "")):
            if match.is_file() and not any(p.startswith('.') for p in match.parts):
                rel_path = match.relative_to(resolved_path)
                matches.append(str(rel_path))
    else:
        for match in resolved_path.glob(pattern):
            if match.is_file() and not match.name.startswith('.'):
                rel_path = match.relative_to(resolved_path)
                matches.append(str(rel_path))
    
    if not matches:
        return f"No files matching '{pattern}' found in '{path}'"
    
    return "\n".join(sorted(matches))


def find_in_files(
    pattern: str, 
    path: str = ".", 
    file_pattern: str = "*",
    regex: bool = False,
    context_lines: int = 0
) -> str:
    """Search for a pattern within file contents.
    
    Args:
        pattern: Text or regex pattern to search for.
        path: Directory to search in. Defaults to project root.
        file_pattern: Glob pattern to filter which files to search (e.g., "*.py").
        regex: If True, treat pattern as a regular expression.
        context_lines: Number of lines of context to show around matches.
        
    Returns:
        A formatted string showing matches with file paths and line numbers.
        
    Raises:
        ValueError: If the path is outside allowed boundaries or regex is invalid.
    """
    config = get_config()
    resolved_path = config.resolve_path(path)
    
    if not resolved_path.exists():
        raise FileNotFoundError(f"Directory not found: {path}")
    
    if not resolved_path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")
    
    if regex:
        try:
            compiled_pattern = re.compile(pattern)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}")
    
    results = []
    files_searched = 0
    
    # Find all matching files
    for file_path in resolved_path.rglob(file_pattern):
        if not file_path.is_file():
            continue
        if any(p.startswith('.') for p in file_path.parts):
            continue
        
        files_searched += 1
        
        try:
            content = file_path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue
        
        lines = content.splitlines()
        rel_path = file_path.relative_to(resolved_path)
        file_matches = []
        
        for i, line in enumerate(lines, 1):
            if regex:
                if compiled_pattern.search(line):
                    file_matches.append((i, line))
            else:
                if pattern in line:
                    file_matches.append((i, line))
        
        if file_matches:
            results.append(f"\n{rel_path}:")
            for line_num, line_content in file_matches:
                # Add context lines if requested
                if context_lines > 0:
                    start = max(0, line_num - 1 - context_lines)
                    end = min(len(lines), line_num + context_lines)
                    for ctx_num in range(start, end):
                        prefix = ">" if ctx_num == line_num - 1 else " "
                        results.append(f"  {prefix} {ctx_num + 1}: {lines[ctx_num]}")
                    results.append("")  # Separator
                else:
                    results.append(f"  {line_num}: {line_content.strip()}")
    
    if not results:
        return f"No matches for '{pattern}' found in {files_searched} files"
    
    header = f"Found matches in {len([r for r in results if r.startswith('\\n')])} files:"
    return header + "".join(results)


def _format_size(size: int) -> str:
    """Format a file size in human-readable format."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size < 1024:
            return f"{size:.1f}{unit}" if unit != 'B' else f"{size}{unit}"
        size /= 1024
    return f"{size:.1f}TB"

