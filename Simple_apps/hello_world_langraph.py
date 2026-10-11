"""Module 1 · Lesson 2 — Same idea in LangGraph, WITH a tool.

Strands isn't the only framework. This uses LangGraph and adds a small tool,
so you can watch the agentic loop actually loop.

WHAT TO LOOK FOR in the output:
    human: Please greet Alice and Bob.
    ai:                                  <-- EMPTY! the model chose to use a tool
    tool: Hello, Alice! ...              <-- the tool ran
    tool: Hello, Bob! ...                <-- and ran again
    ai: Done! I've greeted both...       <-- now it answers

That empty `ai:` line is the model deciding to act instead of replying.
That IS the agentic loop.

    python shivank1/02_hello_world_langgraph.py
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain.chat_models import init_chat_model
from langchain.tools import tool
from langchain.agents import create_agent
from config import MODEL_ID

# Define a Simple Tool
@tool
def greet(name: str):
    """
    Green someone by name
    """
    return f"Hello , {name}! welcome to the world of AI Agents."


# initialize the LLM via backend
llm = init_chat_model(
    MODEL_ID,
    model_provider="bedrock_converse"
)

# create a React agent with the tools
agent = create_agent(
    model=llm,
    tools=[greet]
)

# RUN agent

reponse = agent.invoke(
    {"messages": [
        {
            "role": "user",
            "content": "Please greet Alice and Bob."
        }
    ]}
)

# print every steps so we can see loop
for message in reponse['messages']:
    print(f"{message.type}: {message.text}")