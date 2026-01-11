from __future__ import annotations

import dspy

from otter_code.tools import (
    read_file,
    list_directory,
    search_files,
    find_in_files,
    execute_bash,
    reset_shell_session,
    wrap_as_dspy_tool
)

PLAN_TOOLS = [
    wrap_as_dspy_tool(read_file),
    wrap_as_dspy_tool(list_directory),
    wrap_as_dspy_tool(search_files),
    wrap_as_dspy_tool(find_in_files),
    wrap_as_dspy_tool(execute_bash),
    wrap_as_dspy_tool(reset_shell_session)
]

class PlanSignature(dspy.Signature):
    """
    Create an implementation plan for the task.

    Do not complete the task yourself.

    Do any exploration required to create the plan.


    """
    task: str = dspy.InputField(desc="The task to plan for")
    plan: str = dspy.OutputField(desc="The plan for the task")

class Plan(dspy.Module):
    def __init__(
        self,
        **kwargs
    ):
        super().__init__()
        self.react = dspy.ReAct(PlanSignature, PLAN_TOOLS, kwargs.get('max_iters', 100))

    def forward(self, task: str) -> str:
        return self.react(task=task)