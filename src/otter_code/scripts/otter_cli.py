#!/usr/bin/env python3
"""Command Line Interface for the Otter Code Agent.

This script provides a CLI interface to interact with the otter_code agent.
It supports various configuration options and allows users to specify tasks
for the agent to execute.

Usage:
    python otter_cli.py [OPTIONS] TASK
    
Example:
    python otter_cli.py --project-root /path/to/project "Create a new Python module"
"""

import argparse
import sys
import os
from typing import List, Dict, Any
import dspy
from otter_code import configure, get_all_tools, cleanup
from otter_code.modules import Agent
from dotenv import load_dotenv

import mlflow


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Otter Code Agent CLI - Interact with the otter_code agent",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python otter_cli.py "Create a new Python module"
  python otter_cli.py --project-root /path/to/project "Fix the bug in main.py"
  python otter_cli.py --shell-backend docker --max-iterations 10 "Refactor the codebase"
        """
    )
    
    # Required task argument
    parser.add_argument(
        "task",
        type=str,
        help="The task you want the agent to perform"
    )
    
    # Optional configuration arguments
    parser.add_argument(
        "--project-root",
        type=str,
        default=".",
        help="Root directory of the project (default: current directory)"
    )
    
    parser.add_argument(
        "--shell-backend",
        type=str,
        choices=["local", "docker"],
        default="local",
        help="Shell backend to use (local or docker, default: local)"
    )
    
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=15,
        help="Maximum number of iterations for the agent (default: 15)"
    )
    
    parser.add_argument(
        "--temperature",
        type=float,
        default=1.0,
        help="Temperature for the language model (default: 1.0)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug mode with detailed logging"
    )
    
    parser.add_argument(
        "--no-cleanup",
        action="store_true",
        help="Disable automatic cleanup after execution"
    )

    parser.add_argument(
        "--mlflow-tracing",
        action="store_true",
        help="Enable MLflow tracing for the execution"
    )
    
    return parser.parse_args()


def configure_dspy(args: argparse.Namespace) -> None:
    """Configure DSPy with environment variables and settings."""
    load_dotenv()
    
    # Configure DSPy
    dspy.configure(
        lm=dspy.LM(
            os.getenv('LM_MODEL'),
            api_key=os.getenv('LM_API_KEY'),
            temperature=args.temperature
        )
    )
    
    if args.verbose:
        print(f"DSPy configured with model: {os.getenv('LM_MODEL')}")
        print(f"Temperature: {args.temperature}")


def configure_mlflow(args: argparse.Namespace) -> None:
    """Configure MLflow tracing if enabled."""
    if not args.mlflow_tracing:
        return
    
    # Get MLflow URI from environment variable or use default
    mlflow_uri = os.getenv('ML_FLOW_URI', 'http://127.0.0.1:5000')
    
    # Get experiment name from environment variable or use default
    experiment_name = os.getenv('ML_FLOW_EXPERIMENT', 'otter_code')
    
    # Configure MLflow
    mlflow.set_tracking_uri(mlflow_uri)
    mlflow.set_experiment(experiment_name)
    
    # Enable autologging for DSPy
    mlflow.dspy.autolog()
    
    if args.verbose:
        print(f"MLflow tracing enabled")
        print(f"MLflow URI: {mlflow_uri}")
        print(f"Experiment name: {experiment_name}")


def configure_otter_code(args: argparse.Namespace) -> None:
    """Configure the otter_code toolkit."""
    configure(
        project_root=args.project_root,
        shell_backend=args.shell_backend
    )
    
    if args.verbose:
        print(f"Otter Code configured with project root: {args.project_root}")
        print(f"Shell backend: {args.shell_backend}")


def create_agent() -> Agent:
    """Create and return a configured Agent."""
    # Create the agent using the Agent module from otter_code.modules
    agent = Agent()
    
    return agent


def execute_task(agent: Agent, task: str, args: argparse.Namespace) -> str:
    """Execute the given task with the agent and return the result."""
    if args.verbose:
        print(f"\nExecuting task: {task}")
        print("=" * 60)
    
    try:
        # Execute the task using the Agent's forward method
        result = agent.forward(task=task)
        
        if args.verbose:
            print("=" * 60)
            print("Task completed successfully!")
        
        return result
        
    except Exception as e:
        print(f"Error executing task: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI."""
    try:
        # Parse command line arguments
        args = parse_arguments()
        
        if args.debug:
            args.verbose = True
            print("Debug mode enabled")
        
        # Configure DSPy
        configure_dspy(args)
        
        # Configure MLflow if enabled
        configure_mlflow(args)
        
        # Configure otter_code
        configure_otter_code(args)
        
        # Create the agent
        if args.verbose:
            print("Creating agent...")
        
        agent = create_agent()
        
        if args.verbose:
            print("Agent created successfully!")
        
        # Execute the task
        result = execute_task(agent, args.task, args)
        
        # Display results
        print("\n" + "=" * 60)
        print("RESULT:")
        print("=" * 60)
        print(result)
        print("=" * 60)
        
        # Cleanup unless disabled
        if not args.no_cleanup:
            if args.verbose:
                print("Cleaning up resources...")
            cleanup()
            if args.verbose:
                print("Cleanup completed!")
        
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        cleanup()
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        if args.debug:
            import traceback
            traceback.print_exc()
        cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()