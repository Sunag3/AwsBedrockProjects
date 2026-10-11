"""Module 2 · Lesson 1 — From a plain function to a tool.

THE CORE IDEA OF MODULE 2.

A normal Python function is invisible to an agent. To expose it, add 3 things:
    1. the @tool decorator   -> makes it available to agents
    2. type hints            -> tells the agent what data types to expect
    3. a proper docstring    -> tells the agent WHEN to use it

    python shivank2/01_function_to_tool.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from strands import Agent, tool
from strands.models.bedrock import BedrockModel
from config import MODEL_ID


@tool
def check_server_status(server_url: str):
    """
    Check if server is responding by makng http request.

    Args:
      server_url: The URL of the server to check
    
    Return:
      A message indicating whether the server is up or down
    """

    try:
        response = requests.get(server_url, timeout=5)
        return f"Server is up. Status code: {response.status_code}"
    except requests.exceptions.RequestException:
        return f"Server is down or unreachable"


model = BedrockModel(model_id=MODEL_ID)
agent = Agent(model=model, tools=[check_server_status])

response = agent("Is the staging server running? check https://httpbin.org/")

print(response)
