import requests
import json

def test_api():
    url = 'https://api.porn.ai/api/v1/ollama/chat'
    headers = {
        'Content-Type': 'application/json',
        'api-key': 'OneFlewOverTheCuckoosNest'
    }
    
    data = {
        'messages': [
            {
                'role': 'system',
                'content': 'You are a helpful assistant.'
            },
            {
                'role': 'user',
                'content': 'Tell me a joke about cats.'
            }
        ],
        'stream': False,
        'username': 'xapster@gmail.com'
    }
    
    try:
        print('Sending request to API...')
        response = requests.post(url, headers=headers, json=data)
        print(f'Response status code: {response.status_code}')
        print(f'Response headers: {dict(response.headers)}')
        print(f'Response content: {response.text}')
    except Exception as e:
        print(f'Error occurred: {str(e)}')

if __name__ == '__main__':
    test_api() 