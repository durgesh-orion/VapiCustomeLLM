from flask import Flask, request, jsonify, Response
from dotenv import load_dotenv
import os
import json
import requests
import time
import sys
from urllib3.util.retry import Retry
from requests.adapters import HTTPAdapter

# Load environment variables
load_dotenv()

# Validate required environment variables
required_env_vars = {
    "OLLAMA_API_ENDPOINT": os.getenv("OLLAMA_API_ENDPOINT"),
    "OLLAMA_USERNAME": os.getenv("OLLAMA_USERNAME"),
    "OLLAMA_AI_API_KEY": os.getenv("OLLAMA_AI_API_KEY")
}

# Check for missing environment variables
missing_vars = [var for var, value in required_env_vars.items() if not value]
if missing_vars:
    print(f"Error: Missing required environment variables: {', '.join(missing_vars)}")
    print("Current environment variables:")
    for var, value in required_env_vars.items():
        print(f"{var}: {value if value else 'Not set'}")
    sys.exit(1)

app = Flask(__name__)

# Ollama API configuration
OLLAMA_API_URL = required_env_vars["OLLAMA_API_ENDPOINT"]
OLLAMA_USERNAME = required_env_vars["OLLAMA_USERNAME"]
OLLAMA_API_KEY = required_env_vars["OLLAMA_AI_API_KEY"]

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "running",
        "message": "Server is running. Send POST requests to /chat/completions",
        "endpoints": {
            "chat_completions": "/chat/completions"
        }
    })

@app.route("/chat/completions", methods=["POST"])
def chat_completions():
    try:
        if not request.is_json:
            return jsonify({"error": "Content-Type must be application/json"}), 400
            
        data = request.get_json()
        print("Received request:", json.dumps(data, indent=2))
        
        # Validate required fields
        if not data or 'messages' not in data:
            return jsonify({"error": "Request must include 'messages' field"}), 400
        
        # Extract parameters with defaults
        messages = data.get('messages', [])
        stream = data.get('stream', False)
        model = data.get('model', 'gpt-3.5-turbo')  # Get model from request
        max_tokens = data.get('max_tokens', 250)     # Get max_tokens from request
        temperature = data.get('temperature', 0.7)   # Get temperature from request
        
        # Get the user's message for making a mock response
        user_message = ""
        for msg in messages:
            if msg["role"] == "user":
                user_message = msg["content"]
                break
        
        print(f"Stream mode requested: {stream}")
        
        # Comment out mock implementation
        """
        # Use mock response generator for both streaming and non-streaming responses
        if stream:
            # Handle streaming response
            def generate():
                # Generate mock content based on user message
                response_content = generate_mock_content(user_message)
                
                # Break the response into multiple chunks to simulate streaming
                words = response_content.split()
                chunks = []
                
                # Create a few chunks of varying sizes to simulate realistic streaming
                chunk_size = max(1, len(words) // 4)  # Divide into approximately 4 chunks
                for i in range(0, len(words), chunk_size):
                    chunk = " ".join(words[i:i+chunk_size])
                    chunks.append(chunk)
                
                # Send each chunk as a separate SSE message
                for i, chunk in enumerate(chunks):
                    chunk_data = {
                        "id": "chatcmpl-" + str(os.urandom(3).hex()),
                        "object": "chat.completion.chunk",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "delta": {
                                    "content": chunk + " "
                                },
                                "finish_reason": "stop" if i == len(chunks) - 1 else None
                            }
                        ]
                    }
                    print(f"Sending chunk: {json.dumps(chunk_data)}")
                    yield f"data: {json.dumps(chunk_data)}\n\n"
                    time.sleep(0.3)  # Add a small delay between chunks
                
                # End the stream
                yield "data: [DONE]\n\n"
                
            return Response(generate(), mimetype='text/event-stream')
        else:
            # Non-streaming response
            mock_response = generate_mock_response(user_message, model)
            return jsonify(mock_response)
        """
        
        # Prepare request payload for Ollama
        payload = {
            "messages": messages,
            "stream": stream,
            "username": OLLAMA_USERNAME,
            "model": "huggingface.co/mradermacher/Llama-3.1-8b-Uncensored-Dare-i1-GGUF:i1-Q4_K_M",  # Add specific model
            "temperature": temperature,  # Add temperature
            "max_tokens": max_tokens    # Add max_tokens
        }
        
        # Prepare headers with API key - using the exact format from the working curl command
        headers = {
            "Content-Type": "application/json",
            "api-key": OLLAMA_API_KEY,
            "Accept": "application/json",
            "User-Agent": "Python/Flask Client"
        }
        
        # Validate and sanitize the request
        try:
            # Ensure messages are properly formatted
            for msg in messages:
                if not isinstance(msg, dict) or "role" not in msg or "content" not in msg:
                    raise ValueError("Invalid message format")
                if msg["role"] not in ["system", "user", "assistant"]:
                    raise ValueError(f"Invalid role: {msg['role']}")
                # Sanitize content to remove any problematic characters
                msg["content"] = msg["content"].strip()
            
            # Ensure username is properly formatted
            if not "@" in OLLAMA_USERNAME:
                raise ValueError("Invalid username format")
            
            # Ensure API key is present and properly formatted
            if not OLLAMA_API_KEY or len(OLLAMA_API_KEY) < 10:
                raise ValueError("Invalid API key format")
                
        except ValueError as e:
            print(f"Request validation error: {str(e)}")
            return jsonify({
                "error": "Invalid request format",
                "details": str(e)
            }), 400
        
        print("Sending request to Ollama API:", json.dumps(payload, indent=2))
        print("Using headers:", {
            "Content-Type": "application/json",
            "api-key": f"{'*' * (len(OLLAMA_API_KEY) - 8)}{OLLAMA_API_KEY[-8:]}",
            "Accept": "application/json",
            "User-Agent": "Python/Flask Client"
        })
        print("API URL:", OLLAMA_API_URL)
        
        try:
            # Make request to Ollama API with timeout and retries
            session = requests.Session()
            retries = Retry(
                total=3,  # Reduced retries to avoid long waits
                backoff_factor=0.5,  # Reduced backoff
                status_forcelist=[500, 502, 503, 504]  # Retry on specific status codes
            )
            session.mount('http://', HTTPAdapter(max_retries=retries))
            session.mount('https://', HTTPAdapter(max_retries=retries))
            
            # Try without streaming first if streaming fails
            if stream:
                try:
                    response = session.post(
                        OLLAMA_API_URL,
                        json=payload,
                        headers=headers,
                        stream=True,
                        timeout=30  # Reduced timeout
                    )
                    
                    if response.status_code == 500:
                        print("Streaming request failed, trying without streaming...")
                        # Retry without streaming
                        payload["stream"] = False
                        response = session.post(
                            OLLAMA_API_URL,
                            json=payload,
                            headers=headers,
                            stream=False,
                            timeout=30
                        )
                except Exception as e:
                    print(f"Streaming request failed: {str(e)}")
                    # Retry without streaming
                    payload["stream"] = False
                    response = session.post(
                        OLLAMA_API_URL,
                        json=payload,
                        headers=headers,
                        stream=False,
                        timeout=30
                    )
            else:
                response = session.post(
                    OLLAMA_API_URL,
                    json=payload,
                    headers=headers,
                    stream=False,
                    timeout=30
                )
            
            # Print the full response for debugging
            print(f"Response status code: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response content: {response.text}")
            
            # Check for specific error status codes
            if response.status_code == 402:
                error_msg = "API Credit Error: Not enough credits or invalid subscription"
                print(f"Error 402: {error_msg}")
                print(f"Response content: {response.text}")
                return jsonify({
                    "error": error_msg,
                    "details": "Please check your API subscription and credits",
                    "response": response.json() if response.text else None
                }), 402
            
            # Check response status for other errors
            response.raise_for_status()
            
            # If we get here, the request was successful
            print("Request successful!")
            
            # Handle streaming responses
            if stream:
                def generate():
                    try:
                        for line in response.iter_lines():
                            if line:
                                try:
                                    data = json.loads(line.decode('utf-8'))
                                    print(f"Received streaming data: {json.dumps(data, indent=2)}")
                                    
                                    # Format the response according to Vapi's requirements
                                    formatted_data = {
                                        "id": "chatcmpl-" + str(os.urandom(6).hex()),
                                        "object": "chat.completion.chunk",
                                        "created": int(time.time()),
                                        "model": model,
                                        "choices": [
                                            {
                                                "index": 0,
                                                "delta": {
                                                    "content": data.get("message", {}).get("content", "")
                                                },
                                                "finish_reason": "stop" if data.get("done", False) else None
                                            }
                                        ]
                                    }
                                    yield f"data: {json.dumps(formatted_data)}\n\n"
                                    if data.get("done", False):
                                        break
                                except json.JSONDecodeError as e:
                                    print(f"Error decoding streaming response: {e}")
                                    continue
                    except Exception as e:
                        print(f"Error in stream generation: {e}")
                        # Send a fallback response in case of any error
                        fallback_data = {
                            "id": "chatcmpl-" + str(os.urandom(6).hex()),
                            "object": "chat.completion.chunk",
                            "created": int(time.time()),
                            "model": model,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {
                                        "content": "I apologize, but I encountered a technical issue."
                                    },
                                    "finish_reason": "stop"
                                }
                            ]
                        }
                        yield f"data: {json.dumps(fallback_data)}\n\n"
                    yield "data: [DONE]\n\n"
                
                return Response(generate(), mimetype='text/event-stream')
            else:
                # Format non-streaming response according to Vapi's requirements
                try:
                    ollama_response = response.json()
                    print(f"Received response from Ollama API: {json.dumps(ollama_response, indent=2)}")
                    
                    # Extract the message content from the response
                    message_content = ollama_response.get("message", {}).get("content", "")
                    
                    formatted_response = {
                        "id": "chatcmpl-" + str(os.urandom(6).hex()),
                        "object": "chat.completion",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "message": {
                                    "role": "assistant",
                                    "content": message_content
                                },
                                "finish_reason": "stop"
                            }
                        ],
                        "usage": {
                            "prompt_tokens": ollama_response.get("prompt_eval_count", 0),
                            "completion_tokens": ollama_response.get("eval_count", 0),
                            "total_tokens": (
                                ollama_response.get("prompt_eval_count", 0) + 
                                ollama_response.get("eval_count", 0)
                            )
                        }
                    }
                    return jsonify(formatted_response)
                except (json.JSONDecodeError, KeyError) as e:
                    print(f"Error processing response: {e}")
                    print(f"Raw response content: {response.text}")
                    
                    # Return a fallback response in OpenAI format
                    fallback_response = {
                        "id": "chatcmpl-" + str(os.urandom(6).hex()),
                        "object": "chat.completion",
                        "created": int(time.time()),
                        "model": model,
                        "choices": [
                            {
                                "index": 0,
                                "message": {
                                    "role": "assistant",
                                    "content": "I apologize, but I encountered a technical issue while processing your request."
                                },
                                "finish_reason": "stop"
                            }
                        ],
                        "usage": {
                            "prompt_tokens": 0,
                            "completion_tokens": 0,
                            "total_tokens": 0
                        }
                    }
                    return jsonify(fallback_response)
                
        except Exception as e:
            print(f"Unexpected error during API request: {str(e)}")
            # Return a fallback response in OpenAI format for any other exception
            fallback_response = {
                "id": "chatcmpl-" + str(os.urandom(6).hex()),
                "object": "chat.completion",
                "created": int(time.time()),
                "model": model,
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "I'm sorry, I encountered an unexpected technical issue. Please try again later."
                        },
                        "finish_reason": "stop"
                    }
                ],
                "usage": {
                    "prompt_tokens": 0,
                    "completion_tokens": 0,
                    "total_tokens": 0
                }
            }
            return jsonify(fallback_response)
    
    except Exception as e:
        print(f"Error in chat completions: {str(e)}")
        # Return a fallback response in OpenAI format for any unhandled exception
        fallback_response = {
            "id": "chatcmpl-" + str(os.urandom(6).hex()),
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "gpt-3.5-turbo",
            "choices": [
                {
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": "I apologize, but something went wrong on our end. Please try again later."
                    },
                    "finish_reason": "stop"
                }
            ],
            "usage": {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0
            }
        }
        return jsonify(fallback_response), 200  # Return 200 OK with fallback

# Function to generate a mock response for testing
def generate_mock_response(user_message, model):
    # Generate content based on user message
    response_content = generate_mock_content(user_message)
    
    # Create a proper OpenAI format response
    mock_response = {
        "id": "chatcmpl-" + str(os.urandom(6).hex()),
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response_content
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 50,
            "completion_tokens": len(response_content.split()),
            "total_tokens": 50 + len(response_content.split())
        }
    }
    
    print(f"Generated mock response: {json.dumps(mock_response, indent=2)}")
    return mock_response

# Function to generate content based on user message
def generate_mock_content(user_message):
    # Default response for any message
    response_content = "Hey there! I heard you say: \"" + user_message + "\". How can I help you further?"
    
    # Special cases for common greetings
    if "hello" in user_message.lower() or "hi" in user_message.lower():
        response_content = "Well hello there! It's lovely to meet you. How's your day going so far?"
    elif "how are you" in user_message.lower():
        response_content = "I'm doing wonderfully today, thank you for asking! How about yourself?"
    elif "joke" in user_message.lower():
        response_content = "Why don't scientists trust atoms? Because they make up everything! 😄"
    elif user_message.strip() == "":
        response_content = "I noticed you're quiet. Is there something specific you'd like to talk about today?"
    
    return response_content

@app.errorhandler(404)
def not_found(e):
    return jsonify({"error": "Route not found"}), 404

@app.errorhandler(405)
def method_not_allowed(e):
    return jsonify({"error": "Method not allowed"}), 405

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=5000) 