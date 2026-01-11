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
    Create an implementation plan for the task or update an existing plan.

    When no current_plan is provided:
    - Create a comprehensive implementation plan for the task from scratch
    - Do any exploration required to create the plan

    When a current_plan is provided:
    - Review the existing plan and update it to address the developer_question
    - The developer_question may ask for clarification, modification, or expansion of the existing plan
    - Return an updated plan that incorporates the requested changes

    Do not complete the task yourself.
    """
    task: str = dspy.InputField(desc="The task to plan for")
    current_plan: str = dspy.InputField(desc="Current plan to update, or empty string if creating from scratch", default="")
    developer_question: str = dspy.InputField(desc="Developer question to address when updating a plan, or empty string if not applicable", default="")
    updated_plan: str = dspy.OutputField(desc="The updated plan for the task")

class Plan(dspy.Module):
    def __init__(
        self,
        **kwargs
    ):
        super().__init__()
        self.react = dspy.ReAct(PlanSignature, PLAN_TOOLS, kwargs.get('max_iters', 100))

    def forward(self, task: str, current_plan: str = "", developer_question: str = "") -> dspy.Prediction:
        return self.react(task=task, current_plan=current_plan, developer_question=developer_question)