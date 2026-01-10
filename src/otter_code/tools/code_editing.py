"""Code editing tools with Aider-style search/replace and fuzzy matching.

These tools provide robust code modification capabilities using the
diff-match-patch library for fuzzy matching, inspired by Aider's
SEARCH/REPLACE block paradigm.
"""

import re
from pathlib import Path
from typing import Optional, Tuple

from diff_match_patch import diff_match_patch

from ..config import get_config


# Fuzzy matching threshold (0.0 = exact match, 1.0 = match anything)
# Lower values require closer matches
DEFAULT_MATCH_THRESHOLD = 0.4

# Maximum distance from expected location to search for a match
DEFAULT_MATCH_DISTANCE = 1000


class FuzzyMatcher:
    """Fuzzy text matcher using diff-match-patch algorithm.
    
    This provides Aider-style fuzzy matching that can find text even
    when there are minor differences in whitespace or formatting.
    """
    
    def __init__(
        self, 
        match_threshold: float = DEFAULT_MATCH_THRESHOLD,
        match_distance: int = DEFAULT_MATCH_DISTANCE
    ):
        """Initialize the fuzzy matcher.
        
        Args:
            match_threshold: Matching threshold (0.0 = exact, 1.0 = loose).
            match_distance: Maximum distance to search from expected location.
        """
        self.dmp = diff_match_patch()
        self.dmp.Match_Threshold = match_threshold
        self.dmp.Match_Distance = match_distance
    
    def find_match(
        self, 
        text: str, 
        pattern: str, 
        expected_location: int = 0
    ) -> Optional[Tuple[int, int]]:
        """Find a fuzzy match for a pattern in text.
        
        Args:
            text: The text to search in.
            pattern: The pattern to find.
            expected_location: Expected position (hint for faster matching).
            
        Returns:
            Tuple of (start, end) positions if found, None otherwise.
        """
        if not pattern:
            return None
        
        # First try exact match
        exact_pos = text.find(pattern)
        if exact_pos != -1:
            return (exact_pos, exact_pos + len(pattern))
        
        # Try fuzzy matching
        match_start = self.dmp.match_main(text, pattern, expected_location)
        
        if match_start == -1:
            return None
        
        # Determine the actual matched length using diff
        # We need to figure out where the match ends
        remaining_text = text[match_start:]
        
        # Use diff to find the best alignment
        diffs = self.dmp.diff_main(pattern, remaining_text[:len(pattern) * 2])
        self.dmp.diff_cleanupSemantic(diffs)
        
        # Calculate matched length in the target text
        match_end = match_start
        pattern_consumed = 0
        
        for op, data in diffs:
            if pattern_consumed >= len(pattern):
                break
            
            if op == 0:  # Equal
                match_end += len(data)
                pattern_consumed += len(data)
            elif op == 1:  # Insert (in target)
                match_end += len(data)
            elif op == -1:  # Delete (from pattern)
                pattern_consumed += len(data)
        
        return (match_start, match_end)
    
    def apply_replacement(
        self, 
        text: str, 
        search: str, 
        replace: str,
        expected_location: int = 0
    ) -> Tuple[str, bool]:
        """Apply a search/replace operation with fuzzy matching.
        
        Args:
            text: The text to modify.
            search: The text to search for.
            replace: The replacement text.
            expected_location: Expected position hint.
            
        Returns:
            Tuple of (modified text, whether a match was found).
        """
        match = self.find_match(text, search, expected_location)
        
        if match is None:
            return (text, False)
        
        start, end = match
        new_text = text[:start] + replace + text[end:]
        return (new_text, True)


def search_replace(file_path: str, search: str, replace: str) -> str:
    """Replace text in a file using fuzzy matching.
    
    This function uses Aider-style fuzzy matching to find and replace text,
    which is more robust than exact string matching. It can handle minor
    differences in whitespace and indentation.
    
    Args:
        file_path: Path to the file to modify.
        search: The text to search for. Should be a unique, contiguous block.
        replace: The text to replace it with.
        
    Returns:
        A message describing what was changed.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If no match is found or path is invalid.
    """
    config = get_config()
    resolved_path = config.resolve_path(file_path)
    
    if not resolved_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if not resolved_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    content = resolved_path.read_text(encoding="utf-8")
    
    matcher = FuzzyMatcher()
    new_content, found = matcher.apply_replacement(content, search, replace)
    
    if not found:
        # Provide helpful error message
        search_preview = search[:100] + "..." if len(search) > 100 else search
        raise ValueError(
            f"Could not find matching text in {file_path}. "
            f"Search text begins with: {repr(search_preview)}"
        )
    
    resolved_path.write_text(new_content, encoding="utf-8")
    
    # Calculate change statistics
    lines_removed = search.count('\n') + 1
    lines_added = replace.count('\n') + 1
    
    return (
        f"Successfully replaced text in {file_path}. "
        f"Changed {lines_removed} line(s) to {lines_added} line(s)."
    )


def search_replace_all(file_path: str, search: str, replace: str) -> str:
    """Replace all occurrences of text in a file.
    
    Unlike search_replace which replaces only the first match,
    this replaces all occurrences (using exact matching for safety).
    
    Args:
        file_path: Path to the file to modify.
        search: The exact text to search for.
        replace: The text to replace it with.
        
    Returns:
        A message describing what was changed.
    """
    config = get_config()
    resolved_path = config.resolve_path(file_path)
    
    if not resolved_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    content = resolved_path.read_text(encoding="utf-8")
    
    count = content.count(search)
    if count == 0:
        raise ValueError(f"Text not found in {file_path}")
    
    new_content = content.replace(search, replace)
    resolved_path.write_text(new_content, encoding="utf-8")
    
    return f"Replaced {count} occurrence(s) in {file_path}"


def apply_diff(file_path: str, diff: str) -> str:
    """Apply a unified diff patch to a file.
    
    This accepts patches in unified diff format (as produced by git diff
    or the diff command with -u flag).
    
    Args:
        file_path: Path to the file to patch.
        diff: The unified diff to apply.
        
    Returns:
        A message describing what was changed.
        
    Raises:
        ValueError: If the patch cannot be applied cleanly.
    """
    config = get_config()
    resolved_path = config.resolve_path(file_path)
    
    if not resolved_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    content = resolved_path.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)
    
    # Parse the unified diff
    hunks = _parse_unified_diff(diff)
    
    if not hunks:
        raise ValueError("No valid hunks found in diff")
    
    # Apply hunks in reverse order to preserve line numbers
    new_lines = list(lines)
    applied_count = 0
    
    for hunk in reversed(hunks):
        try:
            new_lines = _apply_hunk(new_lines, hunk)
            applied_count += 1
        except ValueError as e:
            raise ValueError(f"Failed to apply hunk: {e}")
    
    new_content = "".join(new_lines)
    resolved_path.write_text(new_content, encoding="utf-8")
    
    return f"Applied {applied_count} hunk(s) to {file_path}"


def insert_at_line(file_path: str, line_number: int, content: str) -> str:
    """Insert content at a specific line number.
    
    Args:
        file_path: Path to the file to modify.
        line_number: Line number to insert at (1-indexed). Use 0 to prepend.
        content: The content to insert.
        
    Returns:
        A message describing what was changed.
    """
    config = get_config()
    resolved_path = config.resolve_path(file_path)
    
    if not resolved_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    file_content = resolved_path.read_text(encoding="utf-8")
    lines = file_content.splitlines(keepends=True)
    
    # Ensure content ends with newline
    if content and not content.endswith('\n'):
        content += '\n'
    
    content_lines = content.splitlines(keepends=True)
    
    # Handle edge cases
    if line_number <= 0:
        new_lines = content_lines + lines
    elif line_number > len(lines):
        # Append at end
        if lines and not lines[-1].endswith('\n'):
            lines[-1] += '\n'
        new_lines = lines + content_lines
    else:
        # Insert at specified line (1-indexed)
        idx = line_number - 1
        new_lines = lines[:idx] + content_lines + lines[idx:]
    
    new_content = "".join(new_lines)
    resolved_path.write_text(new_content, encoding="utf-8")
    
    return f"Inserted {len(content_lines)} line(s) at line {line_number} in {file_path}"


def delete_lines(file_path: str, start_line: int, end_line: int) -> str:
    """Delete lines from a file.
    
    Args:
        file_path: Path to the file to modify.
        start_line: First line to delete (1-indexed, inclusive).
        end_line: Last line to delete (1-indexed, inclusive).
        
    Returns:
        A message describing what was changed.
    """
    config = get_config()
    resolved_path = config.resolve_path(file_path)
    
    if not resolved_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    if start_line < 1 or end_line < start_line:
        raise ValueError(f"Invalid line range: {start_line}-{end_line}")
    
    content = resolved_path.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)
    
    if start_line > len(lines):
        raise ValueError(f"Start line {start_line} is beyond end of file ({len(lines)} lines)")
    
    # Adjust end_line to not exceed file length
    end_line = min(end_line, len(lines))
    
    # Delete lines (convert to 0-indexed)
    del lines[start_line - 1:end_line]
    
    new_content = "".join(lines)
    resolved_path.write_text(new_content, encoding="utf-8")
    
    deleted_count = end_line - start_line + 1
    return f"Deleted {deleted_count} line(s) from {file_path}"


def _parse_unified_diff(diff: str) -> list[dict]:
    """Parse a unified diff into hunks.
    
    Returns a list of hunk dictionaries with:
    - old_start: Starting line in original file
    - old_count: Number of lines in original
    - new_start: Starting line in new file
    - new_count: Number of lines in new version
    - lines: List of (operation, content) tuples
    """
    hunks = []
    current_hunk = None
    
    hunk_header_pattern = re.compile(
        r'^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@'
    )
    
    for line in diff.splitlines(keepends=True):
        # Check for hunk header
        match = hunk_header_pattern.match(line)
        if match:
            if current_hunk:
                hunks.append(current_hunk)
            
            old_start = int(match.group(1))
            old_count = int(match.group(2)) if match.group(2) else 1
            new_start = int(match.group(3))
            new_count = int(match.group(4)) if match.group(4) else 1
            
            current_hunk = {
                'old_start': old_start,
                'old_count': old_count,
                'new_start': new_start,
                'new_count': new_count,
                'lines': []
            }
            continue
        
        # Skip diff header lines
        if line.startswith('---') or line.startswith('+++'):
            continue
        if line.startswith('diff ') or line.startswith('index '):
            continue
        
        # Process hunk content
        if current_hunk is not None:
            if line.startswith('-'):
                current_hunk['lines'].append(('delete', line[1:]))
            elif line.startswith('+'):
                current_hunk['lines'].append(('add', line[1:]))
            elif line.startswith(' ') or line == '\n':
                content = line[1:] if line.startswith(' ') else line
                current_hunk['lines'].append(('context', content))
    
    if current_hunk:
        hunks.append(current_hunk)
    
    return hunks


def _apply_hunk(lines: list[str], hunk: dict) -> list[str]:
    """Apply a single hunk to a list of lines."""
    result = []
    line_idx = 0
    hunk_start = hunk['old_start'] - 1  # Convert to 0-indexed
    
    # Copy lines before the hunk
    result.extend(lines[:hunk_start])
    line_idx = hunk_start
    
    # Apply the hunk
    for op, content in hunk['lines']:
        if op == 'context':
            # Verify context matches (fuzzy)
            if line_idx < len(lines):
                result.append(lines[line_idx])
                line_idx += 1
            else:
                result.append(content)
        elif op == 'delete':
            # Skip the deleted line
            line_idx += 1
        elif op == 'add':
            # Add the new line
            if not content.endswith('\n'):
                content += '\n'
            result.append(content)
    
    # Copy remaining lines
    result.extend(lines[line_idx:])
    
    return result

