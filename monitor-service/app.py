from flask import Flask, request, jsonify
from datetime import datetime
import requests
import time

app = Flask(__name__)

# Local storage (for testing /logs endpoint)
logs = []

# Elasticsearch service (Docker network)
ELASTIC_URL = "http://elasticsearch:9200/logs/_doc"


@app.route("/")
def home():
    return "Monitor Service Running"


@app.route("/log", methods=["POST"])
def log_request():
    data = request.json
    ip = request.headers.get("X-Forwarded-For", "unknown")

    entry = {
        "ip": ip,
        "data": data,
        "timestamp": datetime.now().isoformat()
    }

    # ✅ Save locally
    logs.append(entry)

    # ✅ Send to Elasticsearch (with retry + headers)
    headers = {"Content-Type": "application/json"}

    for i in range(3):
        try:
            res = requests.post(ELASTIC_URL, json=entry, headers=headers)
            print("Elasticsearch status:", res.status_code)
            print("Elasticsearch response:", res.text)
            break
        except Exception as e:
            print("Retrying Elasticsearch...", e)
            time.sleep(2)

    return jsonify({"status": "logged"}), 200


@app.route("/logs", methods=["GET"])
def get_logs():
    return jsonify(logs), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
