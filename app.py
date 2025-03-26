from flask import Flask, request, jsonify, Response
from openai import OpenAI
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Configure OpenAI client to use Groq
client = OpenAI(
    api_key=os.getenv("GROQ_API_KEY"),  # Store key in .env file
    base_url="https://api.groq.com/openai/v1"
)

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "running",
        "message": "Server is running. Send POST requests to /chat/completions",
        "supported_models": ["gpt-3.5-turbo", "gpt-4", "llama-3.3-70b-versatile"]
    })

@app.route("/chat/completions", methods=["POST"])
def chat_completions():
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
            
        data = request.get_json()
        print("Received request:", data)  # Debug log
        
        if not data or 'messages' not in data:
            return jsonify({"error": "Request must include 'messages' field"}), 400
        
        # Model mapping from OpenAI to Groq
        model_mapping = {
            "gpt-3.5-turbo": "llama-3.3-70b-versatile",
            "gpt-4": "llama-3.3-70b-versatile",
            "llama-3.3-70b-versatile": "llama-3.3-70b-versatile"
        }
        
        # Extract requested model and map to Groq model
        requested_model = data.get('model', 'gpt-3.5-turbo')
        groq_model = model_mapping.get(requested_model)
        
        if not groq_model:
            return jsonify({"error": f"Unsupported model: {requested_model}"}), 400
        
        # Extract messages from the request
        messages = data.get('messages', [])
        
        # Add system message if not present
        if not messages or messages[0].get('role') != 'system':
            messages.insert(0, {"role": "system", "content": "You are a helpful assistant."})
        
        # Check if streaming is requested
        stream = data.get('stream', False)
        
        print("Sending messages to Groq:", messages)  # Debug log
        print(f"Using Groq model: {groq_model} (mapped from {requested_model})")
        print(f"Stream mode: {stream}")
        
        response = client.chat.completions.create(
            model=groq_model,
            messages=messages,
            temperature=data.get('temperature', 0.7),
            max_tokens=data.get('max_tokens', 1000),
            stream=stream
        )
        
        # Handle streaming responses differently
        if stream:
            def generate():
                for chunk in response:
                    if chunk.choices:
                        content = chunk.choices[0].delta.content
                        if content:
                            data = {
                                "id": chunk.id,
                                "object": "chat.completion.chunk",
                                "created": chunk.created,
                                "model": groq_model,
                                "choices": [
                                    {
                                        "index": 0,
                                        "delta": {
                                            "content": content
                                        },
                                        "finish_reason": chunk.choices[0].finish_reason
                                    }
                                ]
                            }
                            yield f"data: {json.dumps(data)}\n\n"
                yield "data: [DONE]\n\n"
            
            return Response(generate(), mimetype='text/event-stream')
        else:
            # Format response according to OpenAI's structure for non-streaming
            formatted_response = {
                "id": response.id,
                "object": "chat.completion",
                "created": response.created,
                "model": response.model,
                "choices": [
                    {
                        "index": choice.index,
                        "message": {
                            "role": choice.message.role,
                            "content": choice.message.content
                        },
                        "finish_reason": choice.finish_reason
                    }
                    for choice in response.choices
                ],
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens
                }
            }
            
            return jsonify(formatted_response)
    
    except Exception as e:
        print(f"Error: {str(e)}")  # Debug log
        return jsonify({"error": str(e)}), 500

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route not found"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5000) 