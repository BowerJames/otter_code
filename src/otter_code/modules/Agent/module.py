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
        self.max_iterations = kwargs.get('max_iterations', 5)

    def forward(self, task: str) -> str:
        """
        Execute the task with iterative question-answering loop.
        
        This method orchestrates the Plan and Execute modules in a loop:
        1. Create or update a plan based on the task and any developer questions
        2. Execute the plan
        3. Check if execution produced a question needing clarification
        4. If a question was asked, loop back to update the plan
        5. Otherwise, return the result
        
        The loop continues until either:
        - Execution completes without questions
        - Max iterations is reached (preventing infinite loops)
        """
        current_plan = ""
        developer_question = ""
        
        for iteration in range(self.max_iterations):
            # Step 1: Create or update plan
            plan_response = self.plan(
                task=task, 
                current_plan=current_plan, 
                developer_question=developer_question
            )
            current_plan = plan_response.updated_plan
            
            # Step 2: Execute the plan
            execution_response = self.execute(task=task, plan=current_plan)
            
            # Step 3: Check if execution contains a question
            if self._execution_contains_question(execution_response):
                developer_question = self._extract_question(execution_response)
                # Loop back to update plan with the question
                continue
            else:
                # Task completed successfully
                return execution_response
        
        # Max iterations reached
        return f"Max iterations ({self.max_iterations}) reached. Unable to complete task. Last plan: {current_plan}"
    
    def _execution_contains_question(self, execution_response: str) -> bool:
        """
        Detect if the execution response contains a question.
        
        Args:
            execution_response: The result string from the Execute module
            
        Returns:
            True if the response starts with 'QUESTION:', False otherwise
        """
        if isinstance(execution_response, str):
            return execution_response.strip().startswith("QUESTION:")
        return False
    
    def _extract_question(self, execution_response: str) -> str:
        """
        Extract the question from the execution response.
        
        Args:
            execution_response: The result string from the Execute module
            
        Returns:
            The question content after 'QUESTION:' prefix
        """
        if isinstance(execution_response, str):
            # Remove 'QUESTION:' prefix and return the question
            return execution_response.strip()[9:].strip()
        return "Unknown question format"