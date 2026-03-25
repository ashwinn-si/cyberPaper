"""
server.py — Flask API server for the CyberCouncil web frontend.

Endpoints:
    POST /api/analyze       Run full council analysis on a threat description
    GET  /api/health        Health check — verifies API keys are loaded
    GET  /api/config        Returns current provider configuration (no secrets)

Usage:
    python server.py                  # default: http://localhost:5050
    python server.py --port 8080
    FLASK_ENV=development python server.py

CORS is enabled for all origins in development. Restrict in production.
"""

import sys
import os
import json
import argparse
import time
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# Ensure project root is on the path when server is run directly
sys.path.insert(0, os.path.dirname(__file__))

from council.orchestrator import CyberCouncil
from config.agent_config import (
    AGENT_A_PROVIDER, AGENT_B_PROVIDER,
    AGENT_C_PROVIDER, JUDGE_PROVIDER
)


app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

# Create one shared council instance (providers are stateless per request)
_council = CyberCouncil()


# ─────────────────────────────────────────────────────────────────
#  Serve frontend
# ─────────────────────────────────────────────────────────────────

@app.route("/")
def serve_index():
    return send_from_directory("frontend", "index.html")


# ─────────────────────────────────────────────────────────────────
#  API: analyze
# ─────────────────────────────────────────────────────────────────

@app.route("/api/analyze", methods=["POST"])
def analyze():
    data = request.get_json(force=True, silent=True)
    if not data or not data.get("threat"):
        return jsonify({"error": "Missing 'threat' field in request body."}), 400

    threat: str = data["threat"].strip()
    if len(threat) < 10:
        return jsonify({"error": "Threat description is too short (minimum 10 characters)."}), 400
    if len(threat) > 4000:
        return jsonify({"error": "Threat description is too long (maximum 4000 characters)."}), 400

    try:
        start = time.time()
        result = _council.analyze(threat)
        elapsed = round(time.time() - start, 2)

        return jsonify({
            "threat":        result["threat"],
            "agent_outputs": result["agent_outputs"],
            "final_report":  result["final_report"],
            "elapsed_sec":   elapsed
        })

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ─────────────────────────────────────────────────────────────────
#  API: health
# ─────────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    keys = {
        "ANTHROPIC_API_KEY": bool(os.getenv("ANTHROPIC_API_KEY")),
        "OPENAI_API_KEY":    bool(os.getenv("OPENAI_API_KEY")),
    }
    all_ok = any(keys.values())
    return jsonify({
        "status":   "ok" if all_ok else "degraded",
        "api_keys": keys
    }), 200 if all_ok else 503


# ─────────────────────────────────────────────────────────────────
#  API: config (no secrets exposed)
# ─────────────────────────────────────────────────────────────────

@app.route("/api/config", methods=["GET"])
def config():
    return jsonify({
        "agents": {
            "classifier":  AGENT_A_PROVIDER.provider_name(),
            "vuln_analyst": AGENT_B_PROVIDER.provider_name(),
            "impact":      AGENT_C_PROVIDER.provider_name(),
            "judge":       JUDGE_PROVIDER.provider_name(),
        }
    })


# ─────────────────────────────────────────────────────────────────
#  Entrypoint
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CyberCouncil API server")
    parser.add_argument("--port", type=int, default=5050, help="Port to listen on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind to")
    args = parser.parse_args()

    print(f"\n  CyberCouncil API server")
    print(f"  → http://{args.host}:{args.port}/")
    print(f"  → POST  /api/analyze   — run full council analysis")
    print(f"  → GET   /api/health    — check API key status")
    print(f"  → GET   /api/config    — view active provider config\n")

    app.run(host=args.host, port=args.port, debug=True)
