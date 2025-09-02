from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv
from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from helper import State, route_tools, BasicToolNode

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize components
gemini_llm = init_chat_model(model="gemini-2.5-flash", model_provider="google_genai")
memory = InMemorySaver()

# Initialize Tavily tool
tavily_tool = TavilySearch(
    max_result=3,
    include_answer=True
)

# Setup tools
tools = [tavily_tool]
llm_with_tools = gemini_llm.bind_tools(tools)

def chatbot(state: State):
    system_prompt = """You are a helpful stock market assistant. When users ask about stocks, 
    use the Tavily search tool to find current information about stock prices, market news, and company information.
    Be concise and informative in your responses. Format numbers nicely and use emojis where appropriate."""
    
    messages = state["messages"]
    if len(messages) == 1:
        messages = [{"role": "system", "content": system_prompt}] + messages
    
    return {"messages": [llm_with_tools.invoke(messages)]}

# Build graph
graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)
tool_node = BasicToolNode(tools=[tavily_tool])
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    route_tools,
    {
        "tools": "tools",
        END: END
    }
)
graph_builder.add_edge(START, "chatbot")
graph_builder.add_edge("tools", "chatbot")

graph = graph_builder.compile(checkpointer=memory)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '')
        thread_id = data.get('thread_id', 'default')
        if not message:
            return jsonify({'error': 'No message provided'}), 400
        
        config = {"configurable": {"thread_id": str(thread_id)}}
        
        # Stream the graph
        events = graph.stream(
            {"messages": [{"role": "user", "content": message}]},
            config=config,
            stream_mode="values"
        )
        
        # Get the response
        response_text = ""
        for event in events:
            if event["messages"]:
                last_message = event["messages"][-1]
                if hasattr(last_message, 'content'):
                    response_text = last_message.content
        
        return jsonify({'response': response_text})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("Starting Flask Stock Chatbot Server...")
    app.run(debug=True, port=5000)