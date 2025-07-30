import requests

# API endpoint
url = "http://127.0.0.1:8000/grade"

# Path to a sample MCQ sheet image
file_path = "reg_Number/photo_2025-07-25_18-57-15.jpg"

# Send POST request with the file
with open(file_path, "rb") as f:
    files = {"file": (file_path, f, "image/jpeg")}
    response = requests.post(url, files=files)

# Print the response from backend
print("Status code:", response.status_code)
print("Response JSON:", response.json())
