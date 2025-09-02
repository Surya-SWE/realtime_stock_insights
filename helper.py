## Conditional Edges

# Edge -> route the control flow from one to the next.
# Conditional Edge -> start froma a single node and usually contain if statement to route to different nodes depedending on the current graph state.

# Now we need to define the route_tools that checks for tool_calls in the chatbot's output/
# Provide this fun to graph by calling add_conditional_edges which tells the graph that whenever the chat node completed to check this fun to see where to go next..
from langgraph.graph import END
from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph.message import add_messages
from langchain_core.messages import ToolMessage
import json

class State(TypedDict):
    messages: Annotated[list, add_messages]

class BasicToolNode:
    """ This node that runs the tools requested in the last AIMessage.."""

    def __init__(self, tools: list) -> None:
        self.tools_by_name = {tool.name: tool for tool in tools}


    def __call__(self, inputs: dict):
        # := is the walrus operator it's an assignment expression that assigns a value to a var and return that value.
        if messages := inputs.get("messages", []):
            message = messages[-1]
        else:
            raise ValueError("No message found in input")
        outputs = []

        for tool_call in message.tool_calls:
            tool_result = self.tools_by_name[tool_call["name"]].invoke(tool_call["args"])
            outputs.append(
                ToolMessage(
                    content = json.dumps(tool_result),
                    name = tool_call["name"],
                    tool_call_id = tool_call["id"]
                )
            )
        return {"messages" : outputs}

def route_tools(state: State):
    if isinstance(state, list):
        ai_message = state[-1]

    elif messages := state.get("messages", []):
        ai_message = messages[-1]
    
    else:
        raise ValueError(f"No messages found in input state to tool_edge: {state}")
    
    if hasattr(ai_message, "tool_calls") and len(ai_message.tool_calls) > 0:
        return "tools"
    return END