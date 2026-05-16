from flask import Flask, request, jsonify, Response
from prometheus_client import Counter, generate_latest

app = Flask(__name__)

# =========================
# Prometheus Metrics
# =========================

allowed_requests = Counter(
    'allowed_requests_total',
    'Total allowed requests'
)

blocked_requests = Counter(
    'blocked_requests_total',
    'Total blocked requests'
)

# =========================
# Firewall Rules
# =========================

BLOCKED_IPS = [
    "192.168.1.10",
    "10.0.0.1"
]

BLOCKED_KEYWORDS = [
    "DROP",
    "malicious",
    "attack"
]

# =========================
# Home Route
# =========================

@app.route("/")
def home():
    return "Firewall Service Running"

# =========================
# Metrics Endpoint
# =========================

@app.route("/metrics")
def metrics():
    return Response(
        generate_latest(),
        mimetype="text/plain"
    )

# =========================
# Firewall Check Endpoint
# =========================

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

    # =========================
    # Check Blocked IPs
    # =========================

    if ip in BLOCKED_IPS:

        blocked_requests.inc()

        return jsonify({
            "status": "blocked",
            "reason": "IP blocked"
        }), 403

    # =========================
    # Check Malicious Keywords
    # =========================

    for keyword in BLOCKED_KEYWORDS:

        if keyword.lower() in content.lower():

            blocked_requests.inc()

            return jsonify({
                "status": "blocked",
                "reason": "malicious content"
            }), 403

    # =========================
    # Allowed Request
    # =========================

    allowed_requests.inc()

    return jsonify({
        "status": "allowed"
    }), 200

@app.route("/rules", methods=["GET"])
def get_rules():

    return jsonify({
        "blocked_ips": BLOCKED_IPS,
        "blocked_keywords": BLOCKED_KEYWORDS
    })

@app.route("/rules/ip", methods=["POST"])
def add_blocked_ip():

    data = request.json

    ip = data.get("ip")

    if not ip:
        return jsonify({
            "error": "IP address required"
        }), 400

    if ip not in BLOCKED_IPS:
        BLOCKED_IPS.append(ip)

    return jsonify({
        "message": "IP blocked successfully",
        "blocked_ips": BLOCKED_IPS
    }), 200
# =========================
# Main
# =========================

if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=5000
    )
