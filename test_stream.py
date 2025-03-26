import requests
import json

def test_streaming():
    data = {
        "messages": [
            {
                "role": "user",
                "content": "Write a short poem about programming."
            }
        ],
        "model": "gpt-3.5-turbo",
        "stream": True
    }
    
    print("Testing streaming with gpt-3.5-turbo model:")
    response = requests.post(
        'http://localhost:5000/chat/completions',
        json=data,
        stream=True
    )
    
    if response.status_code == 200:
        print("Stream started successfully...")
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    line = line[6:]  # Remove 'data: ' prefix
                    if line == '[DONE]':
                        print("\nStream completed.")
                        break
                    try:
                        chunk = json.loads(line)
                        if 'choices' in chunk and chunk['choices'] and 'delta' in chunk['choices'][0]:
                            content = chunk['choices'][0]['delta'].get('content', '')
                            print(content, end='', flush=True)
                    except json.JSONDecodeError:
                        print(f"Error parsing JSON: {line}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    test_streaming() 