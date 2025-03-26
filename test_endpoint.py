import requests
import json

def test_home():
    response = requests.get('http://localhost:5000/')
    print("\nTesting home endpoint:")
    print(json.dumps(response.json(), indent=2))

def test_chat():
    data = {
        "messages": [
            {
                "role": "user",
                "content": "Hello, how are you?"
            }
        ],
        "model": "llama-3.3-70b-versatile"
    }
    
    response = requests.post(
        'http://localhost:5000/chat/completions',
        json=data
    )
    print("\nTesting chat completions endpoint:")
    print(json.dumps(response.json(), indent=2))

if __name__ == "__main__":
    test_home()
    test_chat() 