from __future__ import annotations

import dspy

from otter_code.modules import Plan, Execute

class Agent(dspy.Module):
    def __init__(
        self,
        **kwargs
    ):
        super().__init__()
        self.plan = Plan(**kwargs)
        self.execute = Execute(**kwargs)

    def forward(self, task: str) -> str:
        plan = self.plan(task=task, current_plan="", developer_question="")
        result = self.execute(task=task, plan=plan.updated_plan)
        return result