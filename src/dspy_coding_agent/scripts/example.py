import dspy
from dspy_coding_agent import configure, get_all_tools, cleanup
from dotenv import load_dotenv
import os

load_dotenv()

# Setup
dspy.configure(
    lm=dspy.LM(
        'openrouter/mistralai/devstral-2512:free',
        api_key=os.getenv('OPENROUTER_API_KEY'),
        temperature=0.8
    )
)
configure(project_root=".", shell_backend="local")

# Create a coding agent
coding_agent = dspy.ReAct(
    signature="task: str -> result: str",
    tools=get_all_tools(),
    max_iters=20
)

# Example tasks the agent can handle:
tasks = [
    "Explain to me how this repository manages shell execution for the agent then run the tests suite and give me a report. Use uv to run the test suite.",
]

for task in tasks:
    print(f"\n{'='*50}")
    print(f"Task: {task}")
    result = coding_agent(task=task)
    print(f"Result: {result.result}")

cleanup()