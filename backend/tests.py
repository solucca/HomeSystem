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
        print(response.text)
    else:
        print(f"Failed to create entity. Status code: {response.status_code}")
        print(response.text)


if __name__ == "__main__":
    # Replace with the desired payload
    payload = {
        "id" : "lucca_temp",
        "type" : "weather_observer",
        "temperature" : {"type":"float","value":15.0,"unit":"Celsius"},
        "relative_humidity" : {"type":"int","value":27,"unit":"Percent"},
        "absolute_humidity" : {"type":"float","value":15.0,"unit":"g/m3"}
    }
    send_post_request(payload)
