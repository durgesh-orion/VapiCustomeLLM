# Vapi Custom Call

A Flask-based API server that provides a custom implementation of the OpenAI chat completions API using Groq's LLM models.

## Features

- OpenAI-compatible chat completions API
- Support for multiple models (mapped to Groq's llama-3.3-70b-versatile)
- Streaming response support
- Error handling and proper HTTP status codes

## Setup

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file with your Groq API key:
   ```
   GROQ_API_KEY=your_api_key_here
   ```
4. Run the server:
   ```bash
   python app.py
   ```

## API Endpoints

- `GET /`: Health check endpoint
- `POST /chat/completions`: Chat completions endpoint (OpenAI-compatible)

## Supported Models

- gpt-3.5-turbo (mapped to llama-3.3-70b-versatile)
- gpt-4 (mapped to llama-3.3-70b-versatile)
- llama-3.3-70b-versatile

## License

MIT
