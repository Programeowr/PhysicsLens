import requests

API_KEY = "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"

response = requests.post(
    "https://openrouter.ai/api/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    },
    json={
        "model": "openrouter/free",
        "messages": [
            {
                "role": "user",
                "content": "Reply with exactly: PhysicsLens API works"
            }
        ],
    },
)

print("Status:", response.status_code)
print(response.text)