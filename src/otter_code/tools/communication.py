"""Communication tools for agent interaction."""

def ask_question(question: str) -> str:
    """
    Ask a question to the planner when clarification is needed.
    
    Use this when:
    - The plan isn't clear or is ambiguous
    - Multiple valid approaches exist and you need guidance on which to take
    - The plan lacks necessary details
    - You encounter an issue that prevents completing the plan as written
    
    Args:
        question: The question to ask the planner, including context and what clarification is needed.
            The question should include:
            - ISSUE: What's unclear or blocking progress
            - CONTEXT: Relevant information about the current state
            - CLARIFICATION NEEDED: What specific information you need
            
        Returns:
            A marker indicating the question was asked. This will be intercepted
            by the Agent module to trigger a re-planning cycle.
    """
    return f"QUESTION: {question}"
