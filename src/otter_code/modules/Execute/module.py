from __future__ import annotations

import dspy

from otter_code.tools import (
    read_file,
    write_file,
    list_directory,
    search_files,
    find_in_files,
    search_replace,
    search_replace_all,
    apply_diff,
    insert_at_line,
    delete_lines,
    execute_bash,
    execute_bash_with_status,
    get_working_directory,
    change_directory,
    reset_shell_session,
    get_shell_info,
    wrap_as_dspy_tool
)
from otter_code.tools.communication import ask_question

EXECUTE_TOOLS = [
    wrap_as_dspy_tool(read_file),
    wrap_as_dspy_tool(write_file),
    wrap_as_dspy_tool(list_directory),
    wrap_as_dspy_tool(search_files),
    wrap_as_dspy_tool(find_in_files),
    wrap_as_dspy_tool(search_replace),
    wrap_as_dspy_tool(search_replace_all),
    wrap_as_dspy_tool(apply_diff),
    wrap_as_dspy_tool(insert_at_line),
    wrap_as_dspy_tool(delete_lines),
    wrap_as_dspy_tool(execute_bash),
    wrap_as_dspy_tool(execute_bash_with_status),
    wrap_as_dspy_tool(get_working_directory),
    wrap_as_dspy_tool(change_directory),
    wrap_as_dspy_tool(reset_shell_session),
    wrap_as_dspy_tool(get_shell_info),
    wrap_as_dspy_tool(ask_question),
]

class ExecuteSignature(dspy.Signature):
    """
    Execute the plan to complete the task.
    """
    task: str = dspy.InputField(desc="The task to execute")
    plan: str = dspy.InputField(desc="The plan to execute")
    result: str = dspy.OutputField(desc="The result of the execution")

class Execute(dspy.Module):
    def __init__(
        self,
        **kwargs
    ):
        super().__init__()
        self.react = dspy.ReAct(ExecuteSignature, EXECUTE_TOOLS, kwargs.get('max_iters', 100))

    def forward(self, task: str, plan: str) -> str:
        return self.react(task=task, plan=plan)