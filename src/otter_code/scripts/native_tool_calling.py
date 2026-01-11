"""Toy example demonstrating ChatAdapter with native tool calling.

This script shows how to use DSPy's ChatAdapter with native function calling
to enable a language model to make tool calls. The history can be inspected
to see how tool calls are structured and executed. The script also executes
the tool calls and gives the model a chance to respond to the results.
"""
import dspy
from dspy.adapters import ChatAdapter
from dotenv import load_dotenv
import os
import json

dspy.ReAct

# Import tools from otter_code
from otter_code import configure, get_filesystem_tools, cleanup

load_dotenv()

# Configure ChatAdapter with native function calling enabled
# This allows the language model to use native function calling APIs
chat_adapter = ChatAdapter(use_native_function_calling=True)

# Configure DSPy with the language model and adapter
dspy.configure(
    lm=dspy.LM(
        os.getenv('LM_MODEL'),
        api_key=os.getenv('LM_API_KEY')
    ),
    adapter=chat_adapter
)

# Configure otter_code tools (for filesystem operations)
configure(project_root=".", shell_backend="local")


class MySignature(dspy.Signature):
    user_message: str = dspy.InputField(desc="A message from the user")
    


# Get some simple filesystem tools
# Using filesystem tools as they don't require complex setup
tools = get_filesystem_tools()[:3]  # Get first 3 tools: read_file, write_file, list_directory

# Create a dictionary mapping tool names to tool objects for execution
tools_dict = {tool.name: tool for tool in tools}

# Create Predict instances
tool_calling_predictor = dspy.Predict(ToolCallingSignature)
response_predictor = dspy.Predict(ToolResponseSignature)

# Make a prediction that should trigger tool calls
# The model should see the available tools and decide to call one
task = "List the contents of the current directory (use the list_directory tool)"

print("=" * 60)
print("MAKING PREDICTION WITH NATIVE TOOL CALLING")
print("=" * 60)
print(f"\nTask: {task}")
print(f"\nAvailable tools: {[tool.name for tool in tools]}")

try:
    # Step 1: Get tool calls from the model
    print("\n" + "-" * 60)
    print("Step 1: Model making tool calls...")
    print("-" * 60)
    
    tool_result = tool_calling_predictor(task=task, tools=tools)
    
    print(f"\nTool Calls Received: {tool_result.tool_calls}")
    
    # Execute the tool calls if any were made
    tool_results = []
    if tool_result.tool_calls and tool_result.tool_calls.tool_calls:
        print(f"\nExecuting {len(tool_result.tool_calls.tool_calls)} tool call(s)...")
        
        for i, tool_call in enumerate(tool_result.tool_calls.tool_calls):
            print(f"\n  Tool Call {i+1}:")
            print(f"    Name: {tool_call.name}")
            print(f"    Args: {tool_call.args}")
            
            try:
                # Execute the tool call
                result = tool_call.execute(functions=tools)
                tool_results.append(f"Tool '{tool_call.name}' result: {result}")
                print(f"    Result: {result[:100]}..." if len(str(result)) > 100 else f"    Result: {result}")
            except Exception as e:
                error_msg = f"Tool '{tool_call.name}' error: {str(e)}"
                tool_results.append(error_msg)
                print(f"    Error: {e}")
    else:
        print("\nNo tool calls were made.")
        tool_results.append("No tool calls were made by the model.")
    
    # Combine all tool results into a single string
    tool_results_str = "\n\n".join(tool_results)
    
    # Step 2: Give the model a chance to respond to the tool results
    print("\n" + "-" * 60)
    print("Step 2: Getting model's response to tool results...")
    print("-" * 60)
    
    response_result = response_predictor(
        task=task,
        tool_results=tool_results_str
    )
    
    print(f"\nModel's Response:")
    print(response_result.response)
    
    # Inspect the history to see the full conversation
    print("\n" + "=" * 60)
    print("CONVERSATION HISTORY")
    print("=" * 60)
    history = dspy.inspect_history(n=2)  # Get last 2 calls (tool calling + response)
    print(json.dumps(history, indent=2, default=str))
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
finally:
    # Cleanup resources
    cleanup()
