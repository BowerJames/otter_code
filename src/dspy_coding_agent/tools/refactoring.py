"""Python refactoring tools using the Rope library.

These tools provide semantic refactoring capabilities for Python code,
including renaming symbols, finding references, and extracting functions.
Rope understands Python's semantics and updates all references correctly.
"""

from pathlib import Path
from typing import Optional, List

from rope.base.project import Project
from rope.base import libutils
from rope.refactor.rename import Rename
from rope.refactor.move import MoveModule, MoveGlobal
from rope.refactor.extract import ExtractMethod, ExtractVariable
from rope.contrib import generate
from rope.contrib.findit import find_occurrences, find_definition

from ..config import get_config


# Cache for Rope project instance
_rope_project: Optional[Project] = None


def _get_rope_project() -> Project:
    """Get or create the Rope project instance."""
    global _rope_project
    
    config = get_config()
    project_root = str(config.project_root)
    
    if _rope_project is None or _rope_project.root.real_path != project_root:
        if _rope_project is not None:
            _rope_project.close()
        
        _rope_project = Project(
            project_root,
            ropefolder=".ropeproject",
            save_history=True
        )
    
    return _rope_project


def _get_resource(file_path: str):
    """Get a Rope resource for a file path."""
    config = get_config()
    resolved_path = config.resolve_path(file_path)
    
    project = _get_rope_project()
    relative_path = resolved_path.relative_to(config.project_root)
    
    return project.get_resource(str(relative_path))


def rename_symbol(file_path: str, offset: int, new_name: str) -> str:
    """Rename a Python symbol (variable, function, class) across the codebase.
    
    This performs a semantic rename, updating all references to the symbol
    throughout the project.
    
    Args:
        file_path: Path to the file containing the symbol.
        offset: Character offset within the file where the symbol is located.
                The offset is the position in the file (0-indexed).
        new_name: The new name for the symbol.
        
    Returns:
        A description of the changes made.
        
    Example:
        # To rename a function 'old_func' to 'new_func':
        # First find the offset of 'old_func' in the file
        >>> rename_symbol("mymodule.py", 42, "new_func")
        'Renamed symbol to new_func. Modified 3 file(s).'
    """
    project = _get_rope_project()
    resource = _get_resource(file_path)
    
    try:
        # Create the rename refactoring
        rename = Rename(project, resource, offset)
        
        # Get the changes
        changes = rename.get_changes(new_name)
        
        # Get description before applying
        description = changes.get_description()
        
        # Apply the changes
        project.do(changes)
        
        # Count modified files
        modified_files = len(changes.get_changed_resources())
        
        return f"Renamed symbol to '{new_name}'. Modified {modified_files} file(s).\n{description}"
        
    except Exception as e:
        return f"Error renaming symbol: {str(e)}"


def rename_symbol_at_line(file_path: str, line_number: int, column: int, new_name: str) -> str:
    """Rename a symbol using line and column position.
    
    A convenience wrapper for rename_symbol that calculates the offset
    from line and column numbers.
    
    Args:
        file_path: Path to the file containing the symbol.
        line_number: Line number (1-indexed).
        column: Column number (0-indexed).
        new_name: The new name for the symbol.
        
    Returns:
        A description of the changes made.
    """
    config = get_config()
    resolved_path = config.resolve_path(file_path)
    
    content = resolved_path.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)
    
    # Calculate offset
    offset = sum(len(line) for line in lines[:line_number - 1]) + column
    
    return rename_symbol(file_path, offset, new_name)


def find_references(file_path: str, offset: int) -> str:
    """Find all references to a symbol in the project.
    
    Args:
        file_path: Path to the file containing the symbol.
        offset: Character offset within the file where the symbol is located.
        
    Returns:
        A formatted list of all locations where the symbol is referenced.
    """
    project = _get_rope_project()
    resource = _get_resource(file_path)
    
    try:
        occurrences = find_occurrences(
            project, 
            resource, 
            offset,
            unsure=False,  # Only definite matches
            in_hierarchy=True
        )
        
        if not occurrences:
            return "No references found."
        
        results = []
        for occ in occurrences:
            rel_path = occ.resource.path
            line_start = occ.lineno
            is_definition = "(definition)" if occ.is_defined() else ""
            results.append(f"  {rel_path}:{line_start} {is_definition}")
        
        return f"Found {len(occurrences)} reference(s):\n" + "\n".join(results)
        
    except Exception as e:
        return f"Error finding references: {str(e)}"


def find_definition(file_path: str, offset: int) -> str:
    """Find the definition of a symbol.
    
    Args:
        file_path: Path to the file containing the symbol reference.
        offset: Character offset within the file.
        
    Returns:
        The location of the symbol's definition.
    """
    project = _get_rope_project()
    resource = _get_resource(file_path)
    
    try:
        definition = find_definition(project, resource, offset)
        
        if definition is None:
            return "Definition not found."
        
        return f"Definition: {definition.resource.path}:{definition.lineno}"
        
    except Exception as e:
        return f"Error finding definition: {str(e)}"


def extract_function(
    file_path: str, 
    start_offset: int, 
    end_offset: int, 
    new_name: str,
    make_global: bool = False
) -> str:
    """Extract a code block into a new function.
    
    This refactoring extracts the selected code into a new function,
    automatically determining the necessary parameters and return values.
    
    Args:
        file_path: Path to the file containing the code to extract.
        start_offset: Start of the code region to extract.
        end_offset: End of the code region to extract.
        new_name: Name for the new function.
        make_global: If True, create a module-level function instead of a method.
        
    Returns:
        A description of the changes made.
    """
    project = _get_rope_project()
    resource = _get_resource(file_path)
    
    try:
        extractor = ExtractMethod(project, resource, start_offset, end_offset)
        
        changes = extractor.get_changes(new_name, global_=make_global)
        
        description = changes.get_description()
        project.do(changes)
        
        return f"Extracted function '{new_name}'.\n{description}"
        
    except Exception as e:
        return f"Error extracting function: {str(e)}"


def extract_variable(
    file_path: str,
    start_offset: int,
    end_offset: int,
    new_name: str
) -> str:
    """Extract an expression into a new variable.
    
    This refactoring extracts the selected expression into a variable,
    optionally replacing all similar occurrences.
    
    Args:
        file_path: Path to the file containing the expression.
        start_offset: Start of the expression to extract.
        end_offset: End of the expression to extract.
        new_name: Name for the new variable.
        
    Returns:
        A description of the changes made.
    """
    project = _get_rope_project()
    resource = _get_resource(file_path)
    
    try:
        extractor = ExtractVariable(project, resource, start_offset, end_offset)
        
        changes = extractor.get_changes(new_name)
        
        description = changes.get_description()
        project.do(changes)
        
        return f"Extracted variable '{new_name}'.\n{description}"
        
    except Exception as e:
        return f"Error extracting variable: {str(e)}"


def move_symbol(
    source_file: str,
    offset: int,
    destination_file: str
) -> str:
    """Move a global symbol to another module.
    
    Args:
        source_file: Path to the file containing the symbol.
        offset: Character offset of the symbol to move.
        destination_file: Path to the destination module.
        
    Returns:
        A description of the changes made.
    """
    project = _get_rope_project()
    source_resource = _get_resource(source_file)
    dest_resource = _get_resource(destination_file)
    
    try:
        mover = MoveGlobal(project, source_resource, offset)
        
        changes = mover.get_changes(dest_resource)
        
        description = changes.get_description()
        project.do(changes)
        
        modified_files = len(changes.get_changed_resources())
        return f"Moved symbol to '{destination_file}'. Modified {modified_files} file(s).\n{description}"
        
    except Exception as e:
        return f"Error moving symbol: {str(e)}"


def get_symbol_at_offset(file_path: str, offset: int) -> str:
    """Get information about the symbol at a given offset.
    
    This is a helper function to identify what symbol is at a particular
    location in the code.
    
    Args:
        file_path: Path to the file.
        offset: Character offset in the file.
        
    Returns:
        Information about the symbol at that position.
    """
    config = get_config()
    resolved_path = config.resolve_path(file_path)
    
    content = resolved_path.read_text(encoding="utf-8")
    
    # Find the word at the offset
    if offset < 0 or offset >= len(content):
        return "Offset out of range"
    
    # Find word boundaries
    start = offset
    while start > 0 and (content[start - 1].isalnum() or content[start - 1] == '_'):
        start -= 1
    
    end = offset
    while end < len(content) and (content[end].isalnum() or content[end] == '_'):
        end += 1
    
    symbol = content[start:end]
    
    # Find line number
    line_num = content[:offset].count('\n') + 1
    line_start = content.rfind('\n', 0, offset) + 1
    column = offset - line_start
    
    return f"Symbol: '{symbol}' at line {line_num}, column {column} (offset {offset})"


def undo_last_refactoring() -> str:
    """Undo the last refactoring operation.
    
    Returns:
        A confirmation message.
    """
    project = _get_rope_project()
    
    try:
        if project.history.undo_list:
            project.history.undo()
            return "Last refactoring undone."
        else:
            return "No refactoring to undo."
            
    except Exception as e:
        return f"Error undoing refactoring: {str(e)}"


def redo_refactoring() -> str:
    """Redo the last undone refactoring.
    
    Returns:
        A confirmation message.
    """
    project = _get_rope_project()
    
    try:
        if project.history.redo_list:
            project.history.redo()
            return "Refactoring redone."
        else:
            return "No refactoring to redo."
            
    except Exception as e:
        return f"Error redoing refactoring: {str(e)}"


def close_rope_project() -> None:
    """Close the Rope project and release resources.
    
    Should be called when done with refactoring operations.
    """
    global _rope_project
    
    if _rope_project is not None:
        try:
            _rope_project.close()
        except Exception:
            pass
        _rope_project = None


def validate_python_syntax(file_path: str) -> str:
    """Validate Python syntax of a file.
    
    Args:
        file_path: Path to the Python file to validate.
        
    Returns:
        "Syntax OK" or an error message describing the syntax error.
    """
    config = get_config()
    resolved_path = config.resolve_path(file_path)
    
    try:
        content = resolved_path.read_text(encoding="utf-8")
        compile(content, file_path, "exec")
        return "Syntax OK"
    except SyntaxError as e:
        return f"Syntax error at line {e.lineno}: {e.msg}"
    except Exception as e:
        return f"Error validating syntax: {str(e)}"

