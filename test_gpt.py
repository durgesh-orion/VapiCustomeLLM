import requests
import json

def test_gpt_model():
    data = {
        "messages": [
            {
                "role": "user",
                "content": "Hello, how are you?"
            }
        ],
        "model": "gpt-3.5-turbo"
    }
    
    response = requests.post(
        'http://localhost:5000/chat/completions',
        json=data
    )
    print("\nTesting with gpt-3.5-turbo model:")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_gpt_model() 