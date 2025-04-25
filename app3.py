from flask import Flask, request, jsonify
import requests
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)

VAPI_URL = "https://api.vapi.ai/assistants"
RETELL_URL = "https://api.retellai.com/agents"

VAPI_API_KEY = "9dce4862-024b-48e6-b26f-42e4869850d7"
RETELL_API_KEY = "key_9243de26f1e80e60bc2aa0f2a68c"

@app.route("/create-agent", methods=["POST"])
def create_agent():
    req = request.get_json()

    platform = req.get("platform")
    data = req.get("data")

    if not platform or not data:
        return jsonify({"error": "Missing 'platform' or 'data'"}), 400

    headers = {"Content-Type": "application/json"}

    if platform.lower() == "vapi":
        headers["Authorization"] = f"Bearer {VAPI_API_KEY}"
        response = requests.post(VAPI_URL, json=data, headers=headers)

    elif platform.lower() == "retell":
        headers["Authorization"] = f"Bearer {RETELL_API_KEY}"
        response = requests.post(RETELL_URL, json=data, headers=headers)

    else:
        return jsonify({"error": "Invalid platform. Use 'vapi' or 'retell'."}), 400

    return jsonify({
        "status_code": response.status_code,
        "response": response.json()
    }), response.status_code


if __name__ == "__main__":
    app.run(debug=True)
