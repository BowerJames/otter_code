"""Tests for code editing tools."""

import pytest
from pathlib import Path

from otter_code.config import ToolConfig, set_config
from otter_code.tools import code_editing


@pytest.fixture
def sample_code_file(temp_dir):
    """Create a sample Python file for testing."""
    file_path = temp_dir / "sample.py"
    file_path.write_text('''"""Sample module."""

def hello(name):
    print(f"Hello, {name}!")

def main():
    hello("World")
    if True:
        print("Done")

if __name__ == "__main__":
    main()
''')
    return file_path


# Test FuzzyMatcher initialization
def test_fuzzy_matcher_init():
    """Test FuzzyMatcher initialization."""
    matcher = code_editing.FuzzyMatcher()
    assert matcher.dmp.Match_Threshold == 0.4
    assert matcher.dmp.Match_Distance == 1000


def test_fuzzy_matcher_custom_threshold():
    """Test FuzzyMatcher with custom threshold."""
    matcher = code_editing.FuzzyMatcher(match_threshold=0.1, match_distance=500)
    assert matcher.dmp.Match_Threshold == 0.1
    assert matcher.dmp.Match_Distance == 500


# Test FuzzyMatcher find_match - exact match
def test_fuzzy_matcher_find_exact():
    """Test find_match with exact string."""
    matcher = code_editing.FuzzyMatcher()
    text = "Hello, World!\nThis is a test."
    
    match = matcher.find_match(text, "Hello, World!")
    assert match == (0, 13)


def test_fuzzy_matcher_find_middle():
    """Test find_match with text in middle."""
    matcher = code_editing.FuzzyMatcher()
    text = "Line 1\nLine 2\nLine 3\nLine 4"
    
    match = matcher.find_match(text, "Line 3")
    assert match == (14, 20)


# Test FuzzyMatcher find_match - fuzzy match
def test_fuzzy_matcher_fuzzy_whitespace():
    """Test fuzzy matching handles whitespace differences."""
    matcher = code_editing.FuzzyMatcher()
    text = "Hello,   World!"  # Extra spaces
    
    # Should still find match despite extra whitespace
    match = matcher.find_match(text, "Hello, World!")
    assert match is not None


# Test FuzzyMatcher find_match - no match
def test_fuzzy_matcher_no_match():
    """Test find_match returns None when no match."""
    matcher = code_editing.FuzzyMatcher()
    text = "Hello, World!"
    
    match = matcher.find_match(text, "Goodbye")
    assert match is None


# Test FuzzyMatcher apply_replacement
def test_fuzzy_matcher_apply_replacement():
    """Test apply_replacement replaces text."""
    matcher = code_editing.FuzzyMatcher()
    text = "Hello, World!\nThis is a test."
    
    new_text, found = matcher.apply_replacement(text, "World", "Universe")
    assert found is True
    assert "Universe" in new_text
    assert "World" not in new_text


# Test FuzzyMatcher apply_replacement no match
def test_fuzzy_matcher_apply_no_match():
    """Test apply_replacement when no match found."""
    matcher = code_editing.FuzzyMatcher()
    text = "Hello, World!"
    
    new_text, found = matcher.apply_replacement(text, "Goodbye", "Hello")
    assert found is False
    assert new_text == text


# Test search_replace successful
def test_search_replace_success(custom_config, sample_code_file):
    """Test search_replace successfully replaces text."""
    set_config(custom_config)
    
    result = code_editing.search_replace(
        str(sample_code_file),
        'print(f"Hello, {name}!")',
        'print(f"Greetings, {name}!")'
    )
    
    assert "Successfully replaced" in result
    
    content = sample_code_file.read_text()
    assert "Greetings" in content
    assert "Hello, {name}" not in content


# Test search_replace with fuzzy match
def test_search_replace_fuzzy(custom_config, sample_code_file):
    """Test search_replace handles minor formatting differences."""
    set_config(custom_config)
    
    # Note: In real fuzzy matching, extra whitespace might be tolerated
    result = code_editing.search_replace(
        str(sample_code_file),
        'def main():\n    hello("World")',
        'def main():\n    hello("Everyone")'
    )
    
    assert "Successfully replaced" in result
    content = sample_code_file.read_text()
    assert 'hello("Everyone")' in content


# Test search_replace file not found
def test_search_replace_not_found(custom_config):
    """Test search_replace raises FileNotFoundError."""
    set_config(custom_config)
    
    with pytest.raises(FileNotFoundError, match="File not found"):
        code_editing.search_replace("nonexistent.py", "text", "replacement")


# Test search_replace no match
def test_search_replace_no_match(custom_config, sample_code_file):
    """Test search_replace raises ValueError when no match."""
    set_config(custom_config)
    
    with pytest.raises(ValueError, match="Could not find matching text"):
        code_editing.search_replace(
            str(sample_code_file),
            "nonexistent text that won't be found",
            "replacement"
        )


# Test search_replace disallowed path
def test_search_replace_disallowed(temp_dir):
    """Test search_replace raises ValueError for disallowed path."""
    config = ToolConfig(project_root=temp_dir)
    set_config(config)
    
    with pytest.raises(ValueError, match="outside allowed boundaries"):
        code_editing.search_replace("/etc/hosts", "text", "replacement")


# Test search_replace_all successful
def test_search_replace_all_success(custom_config, temp_dir):
    """Test search_replace_all replaces all occurrences."""
    set_config(custom_config)
    
    file_path = temp_dir / "replace_test.txt"
    file_path.write_text("cat dog cat dog cat")
    
    result = code_editing.search_replace_all(str(file_path), "cat", "dog")
    
    assert "Replaced 3 occurrence(s)" in result
    assert file_path.read_text() == "dog dog dog dog dog"


# Test search_replace_all no occurrences
def test_search_replace_all_no_match(custom_config, temp_dir):
    """Test search_replace_all raises ValueError when no matches."""
    set_config(custom_config)
    
    file_path = temp_dir / "test.txt"
    file_path.write_text("Hello World")
    
    with pytest.raises(ValueError, match="Text not found"):
        code_editing.search_replace_all(str(file_path), "Goodbye", "Hello")


# Test search_replace_all file not found
def test_search_replace_all_not_found(custom_config):
    """Test search_replace_all raises FileNotFoundError."""
    set_config(custom_config)
    
    with pytest.raises(FileNotFoundError):
        code_editing.search_replace_all("nonexistent.txt", "text", "replace")


# Test apply_diff simple hunk
def test_apply_diff_simple(custom_config, temp_dir):
    """Test apply_diff with a simple diff."""
    set_config(custom_config)
    
    file_path = temp_dir / "diff_test.py"
    file_path.write_text("line 1\nline 2\nline 3\nline 4\n")
    
    diff = '''--- a/diff_test.py
+++ b/diff_test.py
@@ -1,4 +1,4 @@
 line 1
-line 2
+modified line 2
 line 3
 line 4
'''
    
    result = code_editing.apply_diff(str(file_path), diff)
    
    assert "Applied 1 hunk" in result
    content = file_path.read_text()
    assert "modified line 2" in content
    # Check that the original line was replaced (not just modified)
    assert content == "line 1\nmodified line 2\nline 3\nline 4\n"


# Test apply_diff multiple hunks
def test_apply_diff_multiple_hunks(custom_config, temp_dir):
    """Test apply_diff with multiple hunks."""
    set_config(custom_config)
    
    file_path = temp_dir / "multi_hunk.py"
    file_path.write_text("a\nb\nc\nd\ne\nf\ng\n")
    
    diff = '''@@ -1,7 +1,7 @@
 a
-b
+B
 c
-d
+D
 e
-f
+F
 g
'''
    
    result = code_editing.apply_diff(str(file_path), diff)
    
    assert "Applied 1 hunk" in result  # This is a single hunk with multiple changes
    content = file_path.read_text()
    assert content == "a\nB\nc\nD\ne\nF\ng\n"


# Test apply_diff file not found
def test_apply_diff_not_found(custom_config):
    """Test apply_diff raises FileNotFoundError."""
    set_config(custom_config)
    
    with pytest.raises(FileNotFoundError):
        code_editing.apply_diff("nonexistent.txt", "diff content")


# Test apply_diff invalid diff
def test_apply_diff_invalid(custom_config, temp_dir):
    """Test apply_diff with invalid diff."""
    set_config(custom_config)
    
    file_path = temp_dir / "test.txt"
    file_path.write_text("content")
    
    invalid_diff = "This is not a valid diff"
    
    with pytest.raises(ValueError, match="No valid hunks"):
        code_editing.apply_diff(str(file_path), invalid_diff)


# Test insert_at_line prepend
def test_insert_at_line_prepend(custom_config, temp_dir):
    """Test insert_at_line with line_number=0 prepends content."""
    set_config(custom_config)
    
    file_path = temp_dir / "insert_test.txt"
    file_path.write_text("line 1\nline 2\n")
    
    result = code_editing.insert_at_line(str(file_path), 0, "PREPENDED\n")
    
    assert "Inserted" in result
    assert "line 0" in result
    content = file_path.read_text()
    assert content.startswith("PREPENDED")


# Test insert_at_line middle
def test_insert_at_line_middle(custom_config, temp_dir):
    """Test insert_at_line inserts at specified line."""
    set_config(custom_config)
    
    file_path = temp_dir / "insert_test.txt"
    file_path.write_text("line 1\nline 2\nline 3\n")
    
    result = code_editing.insert_at_line(str(file_path), 2, "INSERTED\n")
    
    assert "Inserted" in result
    assert "line 2" in result
    content = file_path.read_text()
    assert "line 1\nINSERTED\nline 2" in content


# Test insert_at_line append
def test_insert_at_line_append(custom_config, temp_dir):
    """Test insert_at_line appends when line > file length."""
    set_config(custom_config)
    
    file_path = temp_dir / "insert_test.txt"
    file_path.write_text("line 1\nline 2")
    
    result = code_editing.insert_at_line(str(file_path), 10, "APPENDED\n")
    
    assert "Inserted" in result
    content = file_path.read_text()
    assert content.endswith("APPENDED\n")


# Test insert_at_line adds newline
def test_insert_at_line_adds_newline(custom_config, temp_dir):
    """Test insert_at_line adds newline if missing."""
    set_config(custom_config)
    
    file_path = temp_dir / "insert_test.txt"
    file_path.write_text("line 1\nline 2\n")
    
    code_editing.insert_at_line(str(file_path), 2, "no newline")
    
    content = file_path.read_text()
    assert "line 1\nno newline\nline 2" in content


# Test insert_at_line file not found
def test_insert_at_line_not_found(custom_config):
    """Test insert_at_line raises FileNotFoundError."""
    set_config(custom_config)
    
    with pytest.raises(FileNotFoundError):
        code_editing.insert_at_line("nonexistent.txt", 1, "content")


# Test delete_lines simple
def test_delete_lines_simple(custom_config, temp_dir):
    """Test delete_lines removes specified lines."""
    set_config(custom_config)
    
    file_path = temp_dir / "delete_test.txt"
    file_path.write_text("line 1\nline 2\nline 3\nline 4\n")
    
    result = code_editing.delete_lines(str(file_path), 2, 3)
    
    assert "Deleted 2 line" in result
    content = file_path.read_text()
    assert content == "line 1\nline 4\n"


# Test delete_lines single line
def test_delete_lines_single(custom_config, temp_dir):
    """Test delete_lines removes single line."""
    set_config(custom_config)
    
    file_path = temp_dir / "delete_test.txt"
    file_path.write_text("a\nb\nc\n")
    
    code_editing.delete_lines(str(file_path), 2, 2)
    
    content = file_path.read_text()
    assert content == "a\nc\n"


# Test delete_lines all
def test_delete_lines_all(custom_config, temp_dir):
    """Test delete_lines removes all lines."""
    set_config(custom_config)
    
    file_path = temp_dir / "delete_test.txt"
    file_path.write_text("line 1\nline 2\nline 3\n")
    
    result = code_editing.delete_lines(str(file_path), 1, 3)
    
    assert "Deleted 3 line" in result
    assert file_path.read_text() == ""


# Test delete_lines invalid range
def test_delete_lines_invalid_range(custom_config, temp_dir):
    """Test delete_lines raises ValueError for invalid range."""
    set_config(custom_config)
    
    file_path = temp_dir / "test.txt"
    file_path.write_text("content")
    
    with pytest.raises(ValueError, match="Invalid line range"):
        code_editing.delete_lines(str(file_path), 3, 1)
    
    with pytest.raises(ValueError, match="Invalid line range"):
        code_editing.delete_lines(str(file_path), 0, 1)


# Test delete_lines beyond file
def test_delete_lines_beyond_file(custom_config, temp_dir):
    """Test delete_lines when start line is beyond file."""
    set_config(custom_config)
    
    file_path = temp_dir / "test.txt"
    file_path.write_text("line 1\nline 2")
    
    with pytest.raises(ValueError, match="beyond end of file"):
        code_editing.delete_lines(str(file_path), 10, 15)


# Test delete_lines end beyond file
def test_delete_lines_end_beyond_file(custom_config, temp_dir):
    """Test delete_lines handles end line beyond file length."""
    set_config(custom_config)
    
    file_path = temp_dir / "test.txt"
    file_path.write_text("line 1\nline 2\nline 3")
    
    # Should delete to end of file
    code_editing.delete_lines(str(file_path), 2, 100)
    
    content = file_path.read_text()
    assert content == "line 1\n"


# Test delete_lines file not found
def test_delete_lines_not_found(custom_config):
    """Test delete_lines raises FileNotFoundError."""
    set_config(custom_config)
    
    with pytest.raises(FileNotFoundError):
        code_editing.delete_lines("nonexistent.txt", 1, 3)


# Test _parse_unified_diff simple
def test_parse_unified_diff_simple():
    """Test _parse_unified_diff parses simple diff."""
    diff = '''@@ -1,2 +1,2 @@
-old line
+new line
 context
'''
    
    hunks = code_editing._parse_unified_diff(diff)
    
    assert len(hunks) == 1
    assert hunks[0]['old_start'] == 1
    assert hunks[0]['old_count'] == 2
    assert hunks[0]['new_start'] == 1
    assert hunks[0]['new_count'] == 2
    
    lines = hunks[0]['lines']
    assert len(lines) == 3
    assert lines[0] == ('delete', 'old line\n')
    assert lines[1] == ('add', 'new line\n')
    assert lines[2] == ('context', ' context\n')


# Test _parse_unified_diff empty
def test_parse_unified_diff_empty():
    """Test _parse_unified_diff with empty diff."""
    hunks = code_editing._parse_unified_diff("")
    assert hunks == []


# Test _parse_unified_diff with headers
def test_parse_unified_diff_with_headers():
    """Test _parse_unified_diff skips diff headers."""
    diff = '''diff --git a/file.py b/file.py
index 123..456 100644
--- a/file.py
+++ b/file.py
@@ -1,1 +1,1 @@
-old
+new
'''
    
    hunks = code_editing._parse_unified_diff(diff)
    
    assert len(hunks) == 1
    assert hunks[0]['lines'][0] == ('delete', 'old\n')


# Test _apply_hunk simple
def test_apply_hunk_simple():
    """Test _apply_hunk applies simple change."""
    lines = ["line 1\n", "line 2\n", "line 3\n"]
    hunk = {
        'old_start': 2,
        'old_count': 1,
        'new_start': 2,
        'new_count': 1,
        'lines': [('delete', 'line 2\n'), ('add', 'MODIFIED\n')]
    }
    
    result = code_editing._apply_hunk(lines, hunk)
    
    assert result == ["line 1\n", "MODIFIED\n", "line 3\n"]


# Test _apply_hunk with context
def test_apply_hunk_with_context():
    """Test _apply_hunk with context lines."""
    lines = ["a\n", "b\n", "c\n", "d\n", "e\n"]
    hunk = {
        'old_start': 2,
        'old_count': 3,
        'new_start': 2,
        'new_count': 3,
        'lines': [
            ('context', 'b\n'),
            ('delete', 'c\n'),
            ('add', 'C\n'),
            ('context', 'd\n'),
        ]
    }
    
    result = code_editing._apply_hunk(lines, hunk)
    
    assert result == ["a\n", "b\n", "C\n", "d\n", "e\n"]


# Test _apply_hunk pure addition
def test_apply_hunk_addition():
    """Test _apply_hunk adds new line."""
    lines = ["line 1\n", "line 2\n"]
    hunk = {
        'old_start': 1,
        'old_count': 0,
        'new_start': 1,
        'new_count': 1,
        'lines': [('add', 'new line\n')]
    }
    
    result = code_editing._apply_hunk(lines, hunk)
    
    assert result == ["new line\n", "line 1\n", "line 2\n"]


# Test _apply_hunk pure deletion
def test_apply_hunk_deletion():
    """Test _apply_hunk deletes line."""
    lines = ["line 1\n", "line 2\n", "line 3\n"]
    hunk = {
        'old_start': 2,
        'old_count': 1,
        'new_start': 2,
        'new_count': 0,
        'lines': [('delete', 'line 2\n')]
    }
    
    result = code_editing._apply_hunk(lines, hunk)
    
    assert result == ["line 1\n", "line 3\n"]