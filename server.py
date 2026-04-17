"""
server.py — Flask API server for the CyberCouncil web frontend.

Endpoints:
    POST /api/analyze       Run full council analysis on a threat description
    GET  /api/health        Health check — verifies Ollama is reachable
    GET  /api/config        Returns current provider configuration (no secrets)

Usage:
    python server.py                  # default: http://localhost:5050
    python server.py --port 8080
"""

import sys
import os
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import time
import argparse
import requests as _requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

sys.path.insert(0, os.path.dirname(__file__))

from council.orchestrator import CyberCouncil
from config.agent_config import (
    AGENT_VALIDATOR_PROVIDER,
    AGENT_A_PROVIDER, AGENT_B_PROVIDER,
    AGENT_C_PROVIDER, AGENT_D_PROVIDER,
    JUDGE_PROVIDER,
)

app = Flask(__name__, static_folder="frontend", static_url_path="")
CORS(app)

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
    user_answers: str = data.get("user_answers", "").strip()

    if len(threat) < 10:
        return jsonify({"error": "Threat description is too short (minimum 10 characters)."}), 400
    if len(threat) > 4000:
        return jsonify({"error": "Threat description is too long (maximum 4000 characters)."}), 400

    try:
        start = time.time()
        result = _council.analyze_sync(threat, user_answers)
        elapsed = round(time.time() - start, 2)

        if result["status"] == "rejected":
            return jsonify({
                "status": "rejected",
                "reason": result["validation"].get("reason", "Input rejected by validator."),
            })

        if result["status"] == "needs_clarification":
            return jsonify({
                "status":    "needs_clarification",
                "questions": result["questions"],
            })

        return jsonify({
            "status":          "analyzed",
            "clean_threat":    result["clean_threat"],
            "round1_outputs":  result["round1_outputs"],
            "draft_report":    result["draft_report"],
            "round2_outputs":  result["round2_outputs"],
            "final_report":    result["final_report"],
            "elapsed_sec":     elapsed,
        })

    except Exception as exc:
        return jsonify({"error": str(exc)}), 500


# ─────────────────────────────────────────────────────────────────
#  API: health — checks if Ollama is reachable
# ─────────────────────────────────────────────────────────────────

@app.route("/api/health", methods=["GET"])
def health():
    ollama_base = os.getenv("OLLAMA_API_BASE", "http://localhost:11434")
    try:
        resp = _requests.get(f"{ollama_base}/api/tags", timeout=3)
        ollama_ok = resp.status_code == 200
        models = [m["name"] for m in resp.json().get("models", [])] if ollama_ok else []
    except Exception:
        ollama_ok = False
        models = []

    return jsonify({
        "status":     "ok" if ollama_ok else "degraded",
        "ollama":     ollama_ok,
        "ollama_url": ollama_base,
        "models":     models,
    }), 200 if ollama_ok else 503


# ─────────────────────────────────────────────────────────────────
#  API: config (no secrets exposed)
# ─────────────────────────────────────────────────────────────────

@app.route("/api/config", methods=["GET"])
def config():
    return jsonify({
        "agents": {
            "validator":    AGENT_VALIDATOR_PROVIDER.provider_name(),
            "classifier":   AGENT_A_PROVIDER.provider_name(),
            "vuln_analyst": AGENT_B_PROVIDER.provider_name(),
            "impact":       AGENT_C_PROVIDER.provider_name(),
            "remediation":  AGENT_D_PROVIDER.provider_name(),
            "judge":        JUDGE_PROVIDER.provider_name(),
        }
    })


# ─────────────────────────────────────────────────────────────────
#  Entrypoint
# ─────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CyberCouncil API server")
    parser.add_argument("--port", type=int, default=5050)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    print(f"\n  CyberCouncil API server")
    print(f"  -> http://{args.host}:{args.port}/")
    print(f"  -> POST  /api/analyze   - run full council analysis")
    print(f"  -> GET   /api/health    - check Ollama status")
    print(f"  -> GET   /api/config    - view active provider config\n")

    # use_reloader=False prevents Windows from spawning a child process that
    # loses the WindowsSelectorEventLoopPolicy set above.
    app.run(host=args.host, port=args.port, debug=True, use_reloader=False)
