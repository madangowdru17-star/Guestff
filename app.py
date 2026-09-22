# app.py — HEX CHEATS OFC  |  @HeX_CiPhEr
# https://t.me/+sL3xBoiSrVZmYWI9
# Web server for guest account generator (Railway-ready)

import os
import json
import time
import threading
import uuid
from datetime import datetime
from flask import Flask, render_template, request, jsonify, Response, stream_with_context

from generator import generate_accounts, stop_flag_manager, BRAND

app = Flask(__name__)

# ============ JOB STORE (in-memory) ============
JOBS = {}
JOBS_LOCK = threading.Lock()


def new_job(region, prefix, pwd_prefix, count, threads, rarity_threshold):
    job_id = str(uuid.uuid4())[:8]
    job = {
        "id": job_id,
        "region": region,
        "prefix": prefix,
        "pwd_prefix": pwd_prefix,
        "count": count,
        "threads": threads,
        "rarity_threshold": rarity_threshold,
        "success": 0,
        "failed": 0,
        "rare": 0,
        "couples": 0,
        "started_at": time.time(),
        "finished": False,
        "stop": False,
        "accounts": [],
        "logs": [],
        "lock": threading.Lock(),
    }
    with JOBS_LOCK:
        JOBS[job_id] = job
    return job


# ============ ROUTES ============
@app.route("/")
def index():
    return render_template("index.html", brand=BRAND)


@app.route("/api/start", methods=["POST"])
def api_start():
    data = request.json or {}
    try:
        region = str(data.get("region", "IND")).upper()
        prefix = str(data.get("prefix", "HEX")).strip() or "HEX"
        pwd_prefix = str(data.get("pwd_prefix", "hex")).strip() or "hex"
        count = int(data.get("count", 10))
        threads = int(data.get("threads", 30))
        rarity_threshold = int(data.get("rarity_threshold", 8))
    except (ValueError, TypeError):
        return jsonify({"ok": False, "error": "invalid input"}), 400

    if count < 1 or count > 5000:
        return jsonify({"ok": False, "error": "count must be 1-5000"}), 400
    if threads < 1 or threads > 200:
        return jsonify({"ok": False, "error": "threads must be 1-200"}), 400

    job = new_job(region, prefix, pwd_prefix, count, threads, rarity_threshold)

    def runner():
        try:
            generate_accounts(job)
        except Exception as e:
            with job["lock"]:
                job["logs"].append({"t": time.time(), "level": "error", "msg": f"job crashed: {e}"})
        finally:
            with job["lock"]:
                job["finished"] = True

    t = threading.Thread(target=runner, daemon=True)
    t.start()

    return jsonify({"ok": True, "job_id": job["id"]})


@app.route("/api/stop/<job_id>", methods=["POST"])
def api_stop(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"ok": False, "error": "job not found"}), 404
    with job["lock"]:
        job["stop"] = True
    return jsonify({"ok": True})


@app.route("/api/status/<job_id>")
def api_status(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"ok": False, "error": "job not found"}), 404
    with job["lock"]:
        return jsonify({
            "ok": True,
            "id": job["id"],
            "region": job["region"],
            "success": job["success"],
            "failed": job["failed"],
            "rare": job["rare"],
            "couples": job["couples"],
            "count": job["count"],
            "finished": job["finished"],
            "elapsed": round(time.time() - job["started_at"], 2),
            "rate": round(job["success"] / max(0.001, time.time() - job["started_at"]), 2),
            "accounts": job["accounts"][-100:],  # last 100
            "logs": job["logs"][-50:],
        })


@app.route("/api/download/<job_id>")
def api_download(job_id):
    job = JOBS.get(job_id)
    if not job:
        return jsonify({"ok": False, "error": "job not found"}), 404
    with job["lock"]:
        data = json.dumps(job["accounts"], indent=2, ensure_ascii=False)
    return Response(
        data,
        mimetype="application/json",
        headers={
            "Content-Disposition": f"attachment; filename=hex_accounts_{job_id}.json"
        },
    )


@app.route("/health")
def health():
    return jsonify({"ok": True, "brand": BRAND["name"], "handle": BRAND["handle"]})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port, threaded=True)