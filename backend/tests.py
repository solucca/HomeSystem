import requests
import json

# Replace with the appropriate URL for your FastAPI server
BASE_URL = "http://localhost:8000/entities/"

def send_post_request(payload):
    url = BASE_URL
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        print("POST request successful. Entity created.")
    else:
        print(f"Failed to create entity. Status code: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    # Replace with the desired payload
    
    payload = {
        "id": "01",
        "type": "Weather",
        "temperature": { "type": "float",  "value": 15.0 },
        "humidity": { "type": "int",  "value": 28 }
    }

    send_post_request(payload)