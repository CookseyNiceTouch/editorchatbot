import anthropic
import json
import logging
from davinciapi.davinciapi import get_resolve_connection

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger('ToolUse')

# Define tools for DaVinci Resolve API with better descriptions
DAVINCI_TOOLS = [
    {
        "name": "check_resolve_status",
        "description": "Check if DaVinci Resolve is running and get its version. Returns status (true/false) and version information if running.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_project_info",
        "description": "Get information about the current DaVinci Resolve project including project name, framerate, and timeline count.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_timeline_info",
        "description": "Get details about the current timeline in DaVinci Resolve, including name, frame range, timecode, and track counts.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_media_pool_info",
        "description": "Get information about the media pool in the current DaVinci Resolve project, including folders and clip counts.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_render_jobs",
        "description": "Get information about render jobs in the current DaVinci Resolve project, including job count and individual job details.",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    }
]

def execute_tool(tool_name, tool_input):
    """Execute the specified DaVinci Resolve tool and return the result."""
    logger.info(f"Executing tool: {tool_name}")
    
    try:
        # For check_resolve_status
        if tool_name == "check_resolve_status":
            api = get_resolve_connection()
            if api:
                result = api.is_resolve_running()
                logger.info(f"Resolve status: {result}")
                return result
            return {
                "status": False,
                "error": "Could not connect to DaVinci Resolve"
            }
        
        # For all other tools, check connection first
        api = get_resolve_connection()
        if not api:
            return {
                "error": "Could not connect to DaVinci Resolve"
            }
        
        # Execute the requested tool
        if tool_name == "get_project_info":
            result = api.get_basic_project_info()
            logger.info(f"Project info: {result}")
            return result
            
        elif tool_name == "get_timeline_info":
            result = api.get_timeline_info()
            logger.info(f"Timeline info: {result}")
            return result
            
        elif tool_name == "get_media_pool_info":
            result = api.get_media_pool_info()
            logger.info(f"Media pool info: {result}")
            return result
            
        elif tool_name == "get_render_jobs":
            result = api.get_render_jobs()
            logger.info(f"Render jobs: {result}")
            return result
            
        else:
            return {
                "error": f"Unknown tool: {tool_name}"
            }
            
    except Exception as e:
        logger.error(f"Error executing tool {tool_name}: {str(e)}")
        return {
            "error": f"Error executing tool {tool_name}: {str(e)}"
        }

def create_tool_chat(client, conversation_id, conversations, user_message):
    """Create a chat with tool use capability."""
    try:
        # Prepare messages for Claude
        messages = []
        
        # Add previous messages from conversation (excluding system messages)
        if conversation_id in conversations:
            for msg in conversations[conversation_id]:
                if isinstance(msg["content"], str) and msg["role"] != "system":
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
        
        # Add the current user message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        # Define system prompt separately
        system_prompt = "You can access DaVinci Resolve information. When the user asks about DaVinci Resolve, use the appropriate tool to get the information they need."
        
        logger.info(f"Sending request to Claude with {len(messages)} messages and a system prompt")
        
        # Call Claude API with tools - NOTE: system is a separate parameter, not in messages
        try:
            response = client.messages.create(
                model="claude-3-5-sonnet-latest",
                max_tokens=1000,
                system=system_prompt,  # Pass system prompt as a separate parameter
                tools=DAVINCI_TOOLS,
                tool_choice={"type": "auto"},
                messages=messages
            )
            
            logger.info(f"Claude response received, stop_reason: {response.stop_reason}")
            
            # Handle tool use if Claude decided to use a tool
            if response.stop_reason == "tool_use":
                logger.info("Claude is using a tool")
                
                # Find the tool use content block
                tool_use = None
                for content in response.content:
                    if content.type == "tool_use":
                        tool_use = content
                        break
                
                if tool_use:
                    tool_name = tool_use.name
                    tool_input = tool_use.input
                    tool_use_id = tool_use.id
                    
                    logger.info(f"Tool use - Name: {tool_name}, ID: {tool_use_id}")
                    
                    # Execute the tool
                    tool_result = execute_tool(tool_name, tool_input)
                    
                    # Store messages in conversation history
                    if conversation_id not in conversations:
                        conversations[conversation_id] = []
                    
                    # Add user message
                    conversations[conversation_id].append({
                        "role": "user",
                        "content": user_message
                    })
                    
                    # Add a message indicating tool use
                    conversations[conversation_id].append({
                        "role": "assistant",
                        "content": f"I'll use the {tool_name} tool to get that information."
                    })
                    
                    # Continue conversation with tool result
                    try:
                        # Create new messages array with the tool result
                        new_messages = messages.copy()  # Copy previous messages
                        
                        # Add the assistant's tool use (we'll display this differently in UI)
                        new_messages.append({
                            "role": "assistant",
                            "content": [
                                {
                                    "type": "tool_use",
                                    "name": tool_name,
                                    "input": tool_input,
                                    "id": tool_use_id
                                }
                            ]
                        })
                        
                        # Add the tool result
                        new_messages.append({
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": tool_use_id,
                                    "content": json.dumps(tool_result)
                                }
                            ]
                        })
                        
                        logger.info("Sending tool result back to Claude")
                        
                        # Get final response with the tool result
                        final_response = client.messages.create(
                            model="claude-3-5-sonnet-latest",
                            max_tokens=1000,
                            messages=new_messages
                        )
                        
                        # Add the final response to history
                        final_answer = final_response.content[0].text
                        
                        conversations[conversation_id].append({
                            "role": "assistant",
                            "content": final_answer
                        })
                        
                        return {
                            "conversation_id": conversation_id,
                            "message": final_answer,
                            "history": conversations[conversation_id],
                            "tool_used": True,
                            "tool_name": tool_name
                        }
                        
                    except Exception as e:
                        logger.error(f"Error in second Claude call: {str(e)}")
                        return {"error": f"Error after tool use: {str(e)}"}
            
            # Handle regular text response (no tool use)
            logger.info("Claude provided a text response (no tool use)")
            assistant_message = response.content[0].text
            
            # Store messages in conversation history
            if conversation_id not in conversations:
                conversations[conversation_id] = []
            
            # Add user message
            conversations[conversation_id].append({
                "role": "user",
                "content": user_message
            })
            
            # Add assistant response
            conversations[conversation_id].append({
                "role": "assistant",
                "content": assistant_message
            })
            
            return {
                "conversation_id": conversation_id,
                "message": assistant_message,
                "history": conversations[conversation_id],
                "tool_used": False
            }
            
        except Exception as e:
            logger.error(f"Claude API error: {str(e)}")
            raise e
            
    except Exception as e:
        logger.error(f"Error in tool chat: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return {"error": str(e)}
