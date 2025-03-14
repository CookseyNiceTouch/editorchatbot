from flask import Flask, request, jsonify
import os
from dotenv import load_dotenv
import anthropic
from flask_cors import CORS
import uuid

# Import DaVinci Resolve API
from davinciapi.davinciapi import get_resolve_connection
# Import tool use functionality
from anthropicstuff.tooluse import create_tool_chat, DAVINCI_TOOLS

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Initialize the Anthropic client
client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

# In-memory storage for conversations
# In a production app, you'd use a database instead
conversations = {}

# DaVinci Resolve API endpoints
@app.route("/api/resolve/status", methods=["GET"])
def resolve_status():
    """Check if DaVinci Resolve is running and return status."""
    try:
        api = get_resolve_connection()
        if api:
            status = api.is_resolve_running()
            return jsonify(status)
        return jsonify({"status": False, "error": "Could not connect to DaVinci Resolve"})
    except Exception as e:
        return jsonify({"status": False, "error": str(e)}), 500

@app.route("/api/resolve/project", methods=["GET"])
def get_project_info():
    """Get basic project information from DaVinci Resolve."""
    try:
        api = get_resolve_connection()
        if not api:
            return jsonify({"error": "Could not connect to DaVinci Resolve"}), 503
        
        project_info = api.get_basic_project_info()
        return jsonify(project_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/resolve/timeline", methods=["GET"])
def get_timeline_info():
    """Get current timeline information from DaVinci Resolve."""
    try:
        api = get_resolve_connection()
        if not api:
            return jsonify({"error": "Could not connect to DaVinci Resolve"}), 503
        
        timeline_info = api.get_timeline_info()
        return jsonify(timeline_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/resolve/mediapool", methods=["GET"])
def get_media_pool_info():
    """Get media pool information from DaVinci Resolve."""
    try:
        api = get_resolve_connection()
        if not api:
            return jsonify({"error": "Could not connect to DaVinci Resolve"}), 503
        
        media_pool_info = api.get_media_pool_info()
        return jsonify(media_pool_info)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/resolve/renderjobs", methods=["GET"])
def get_render_jobs():
    """Get render jobs information from DaVinci Resolve."""
    try:
        api = get_resolve_connection()
        if not api:
            return jsonify({"error": "Could not connect to DaVinci Resolve"}), 503
        
        render_jobs = api.get_render_jobs()
        return jsonify(render_jobs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/chat", methods=["POST"])
def chat():
    data = request.json
    conversation_id = data.get("conversation_id")
    user_message = data.get("message")
    use_tools = data.get("use_tools", False)
    
    if not user_message:
        return jsonify({"error": "Message is required"}), 400
    
    # Create a new conversation if none exists
    if not conversation_id or conversation_id not in conversations:
        conversation_id = str(uuid.uuid4())
        conversations[conversation_id] = []
    
    try:
        if use_tools:
            # Simplified tool chat function
            from anthropicstuff.tooluse import create_tool_chat
            result = create_tool_chat(client, conversation_id, conversations, user_message)
            
            if "error" in result:
                return jsonify({"error": result["error"]}), 500
                
            return jsonify(result)
        else:
            # Regular chat without tools
            # Add the user message to history
            conversations[conversation_id].append({
                "role": "user",
                "content": user_message
            })
            
            # Prepare messages for Claude (don't include system messages)
            messages = []
            for msg in conversations[conversation_id]:
                if isinstance(msg["content"], str) and msg["role"] != "system":
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
            
            # Add system prompt as a separate parameter
            system_prompt = "You are Claude, a helpful AI assistant."
            
            response = client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=1000,
                system=system_prompt,
                messages=messages
            )
            
            # Extract assistant's message
            assistant_message = response.content[0].text
            
            # Add the assistant's response to history
            conversations[conversation_id].append({
                "role": "assistant",
                "content": assistant_message
            })
            
            return jsonify({
                "conversation_id": conversation_id,
                "message": assistant_message,
                "history": conversations[conversation_id]
            })
            
    except Exception as e:
        import traceback
        print(f"Error in chat: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": str(e), "status": "error"}), 500

@app.route("/api/conversations/<conversation_id>", methods=["GET"])
def get_conversation(conversation_id):
    if conversation_id not in conversations:
        return jsonify({"error": "Conversation not found"}), 404
    
    return jsonify({
        "conversation_id": conversation_id,
        "history": conversations[conversation_id]
    })

@app.route("/api/conversations", methods=["GET"])
def list_conversations():
    conversation_list = [
        {"id": conv_id, "message_count": len(messages)}
        for conv_id, messages in conversations.items()
    ]
    return jsonify(conversation_list)

if __name__ == "__main__":
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Warning: ANTHROPIC_API_KEY environment variable not set")
    app.run(debug=True)
