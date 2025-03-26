from fastapi import FastAPI, HTTPException, Request, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import os
from dotenv import load_dotenv
import aiohttp
import json

# Load environment variables
load_dotenv()

# Initialize API keys and endpoints
VAPI_API_KEY = os.getenv("VAPI_API_KEY")
OLLAMA_API_ENDPOINT = os.getenv("OLLAMA_API_ENDPOINT")
OLLAMA_USERNAME = os.getenv("OLLAMA_USERNAME")

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

class Message(BaseModel):
    role: str
    content: str

class VapiRequest(BaseModel):
    messages: List[Dict[str, Any]]
    config: Optional[Dict[str, Any]]
    context: Optional[Dict[str, Any]]

async def verify_vapi_key(api_key: str = Header(None, alias="X-API-Key")):
    if not api_key or api_key != VAPI_API_KEY:
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing API key"
        )
    return api_key

async def custom_llm_response(messages: List[Dict[str, Any]]) -> str:
    """
    Calls the Ollama API endpoint for chat completion
    """
    try:
        # Prepare the request payload
        payload = {
            "messages": [
                {"role": "system", "content": "You are a helpful voice assistant. Keep responses concise and natural for voice conversation."}
            ] + messages,
            "stream": False,
            "username": OLLAMA_USERNAME
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                OLLAMA_API_ENDPOINT,
                json=payload,
                headers={"Content-Type": "application/json"}
            ) as response:
                if response.status != 200:
                    error_text = await response.text()
                    raise HTTPException(
                        status_code=response.status,
                        detail=f"Ollama API error: {error_text}"
                    )
                
                result = await response.json()
                # Extract the assistant's response from the result
                # Adjust this based on the actual response format from your API
                return result.get("content", "I apologize, but I couldn't generate a response.")

    except Exception as e:
        print(f"Error calling Ollama API: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Error calling Ollama API: {str(e)}"
        )

@app.get("/")
async def read_root():
    return {"status": "API is running"}

@app.post("/chat/completions")
async def chat_completions(request: VapiRequest, api_key: str = Header(None, alias="X-API-Key")):
    # Verify Vapi API key
    await verify_vapi_key(api_key)
    
    try:
        # Get response from custom LLM
        assistant_message = await custom_llm_response(request.messages)
        
        return {
            "messages": [{
                "role": "assistant",
                "content": assistant_message,
                "end_call": False  # Set to True if you want to end the call
            }]
        }

    except Exception as e:
        print(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    if not VAPI_API_KEY:
        print("Warning: VAPI_API_KEY not set in .env file")
    if not OLLAMA_API_ENDPOINT:
        print("Warning: OLLAMA_API_ENDPOINT not set in .env file")
    if not OLLAMA_USERNAME:
        print("Warning: OLLAMA_USERNAME not set in .env file")
    uvicorn.run(app, host="0.0.0.0", port=8000) 