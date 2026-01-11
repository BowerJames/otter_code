import dspy
from otter_code import configure, get_all_tools, cleanup
from dotenv import load_dotenv
import os
import json
import mlflow
mlflow.set_tracking_uri("http://127.0.0.1:5000")
mlflow.set_experiment("otter_code")
mlflow.dspy.autolog()

load_dotenv()

from otter_code.modules import Agent

# Setup
dspy.configure(
    lm=dspy.LM(
        os.getenv('LM_MODEL'),
        api_key=os.getenv('LM_API_KEY'),
        temperature=1.0
    )
)
configure(project_root=".", shell_backend="local")

agent = Agent()

response = agent(task="In the otter_cli.py script it shoudl be using the Agent module defined in the otter_code modules. Instead it seems to be creating its own react agent. Can you fix this?")

print("--------------------------------")
print("RESPONSE:")
print(response)
print("--------------------------------")

cleanup()