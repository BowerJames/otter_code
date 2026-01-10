import dspy
from otter_code import configure, get_all_tools, cleanup
from dotenv import load_dotenv
import os
import json

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

# OPTION 1: Enable MLflow for comprehensive tracing (Recommended)
# This provides the most detailed execution traces with a web UI
# First install: pip install mlflow
# Then uncomment the following lines:
# import mlflow
# mlflow.dspy.autolog()
# mlflow.set_tracking_uri("http://localhost:5000")  # Optional: if running MLflow server
# After running, start MLflow UI: mlflow ui
# Then view traces at: http://localhost:5000

# OPTION 2: Enable verbose tracing in DSPy settings
# This will print execution details to console
try:
    # Enable trace collection
    if hasattr(dspy.settings, 'trace'):
        dspy.settings.trace = []
except:
    pass

# Create a coding agent
coding_agent = dspy.CodeAct(
    signature="task: str -> result: str",
    tools=get_all_tools(),
    max_iters=20
)

# Example tasks the agent can handle:
tasks = [
    "What is the layout of the src folder? Use the functions provided to get your answer."
]

for task in tasks:
    print(f"\n{'='*50}")
    print(f"Task: {task}")
    result = coding_agent(task=task)
    print(f"Result: {result.result}")
    
    # OPTION 3: Print execution history if available on result
    if hasattr(result, 'history'):
        print(f"\n{'='*50}")
        print("Execution History:")
        print(json.dumps(result.history, indent=2, default=str))
    
    # OPTION 4: Print trace from dspy.settings if collected
    if hasattr(dspy.settings, 'trace') and dspy.settings.trace:
        print(f"\n{'='*50}")
        print("Execution Trace:")
        for trace_entry in dspy.settings.trace:
            print(json.dumps(trace_entry, indent=2, default=str))
    
    # OPTION 5: Check for execution logs on the agent module
    if hasattr(coding_agent, 'history'):
        print(f"\n{'='*50}")
        print("Agent History:")
        print(json.dumps(coding_agent.history, indent=2, default=str))
    
    # OPTION 6: Inspect the result object for any trace information
    # Uncomment to see all available attributes on the result object:
    # print(f"\n{'='*50}")
    # print("Result object attributes:")
    # print([attr for attr in dir(result) if not attr.startswith('_')])

cleanup()