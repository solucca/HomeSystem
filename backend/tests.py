import requests
import json

# Replace with the appropriate URL for your FastAPI server
BASE_URL = "http://mypi:8000/entities/"

def send_post_request(payload):
    url = BASE_URL
    headers = {"Content-Type": "application/json"}
    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 200:
        print("POST request successful. Entity created.")
    else:
        print(f"Failed to create entity. Status code: {response.status_code}")
        print(response.text)

def modify_table(payload):
    url = "http://mypi:8000/types/weather"
    headers = {"Content-Type": "application/json"}
    response = requests.patch(url, headers=headers, data=json.dumps(payload))
    if response.status_code == 200:
        print("POST request successful. Entity created.")
        print(response.text)
    else:
        print(f"Failed to create entity. Status code: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    # Replace with the desired payload
    payload = {"field":"humidity", "type":"float"}
    modify_table(payload)
    payload = {"field":"heat_index", "type":"float"}
    modify_table(payload)
