from flask import Flask, request, jsonify, Response
from prometheus_client import Counter, generate_latest

app = Flask(__name__)

# Metrics
allowed_requests = Counter(
    'allowed_requests_total',
    'Total allowed requests'
)
# testing webhook
blocked_requests = Counter(
    'blocked_requests_total',
    'Total blocked requests'
)

# Firewall rules
BLOCKED_IPS = ["192.168.1.10", "10.0.0.1"]

BLOCKED_KEYWORDS = [
    "DROP",
    "malicious",
    "attack"
]

@app.route("/")
def home():
    return "Firewall Service Running"

@app.route("/metrics")
def metrics():
    return Response(
        generate_latest(),
        mimetype='text/plain'
    )

@app.route("/check", methods=["POST"])
def firewall_check():

    data = request.json

    if not data:
        return jsonify({
            "error": "Invalid JSON"
        }), 400

    ip = request.headers.get(
        "X-Forwarded-For",
        "unknown"
    )

    content = str(data)

    # Check blocked IPs
    if ip in BLOCKED_IPS:

        blocked_requests.inc()

        return jsonify({
            "status": "blocked",
            "reason": "IP blocked"
        }), 403

    # Check malicious content
    for keyword in BLOCKED_KEYWORDS:

        if keyword.lower() in content.lower():

            blocked_requests.inc()

            return jsonify({
                "status": "blocked",
                "reason": "malicious content"
            }), 403

    # Allowed request
    allowed_requests.inc()

    return jsonify({
        "status": "allowed"
    }), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
