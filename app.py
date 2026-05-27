import os
import threading
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, url_for

import database as db

app = Flask(__name__)
app.secret_key = os.urandom(24)

_scrape_lock = threading.Lock()
_last_scrape = {"time": None, "result": None}


# ── Dashboard ────────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    data = db.get_full_dashboard_data()
    last_scrape = _last_scrape.get("time")
    return render_template("index.html",
                           players=data,
                           last_scrape=last_scrape,
                           now=datetime.now().strftime("%B %d, %Y %I:%M %p"))


# ── API: data ─────────────────────────────────────────────────────────────────

@app.route("/api/data")
def api_data():
    return jsonify(db.get_full_dashboard_data())


# ── API: add batting line ────────────────────────────────────────────────────

@app.route("/api/batting", methods=["POST"])
def add_batting():
    d = request.json or {}
    try:
        def iv(k, default=0):
            try:
                return int(d.get(k, default))
            except Exception:
                return default

        ab = iv("AB")
        pa = iv("PA") or ab + iv("BB") + iv("HBP")
        db.add_batting_line(
            player_id=iv("player_id"),
            game_date=d.get("game_date", ""),
            opponent=d.get("opponent", ""),
            home_away=d.get("home_away", "H"),
            H=iv("H"),
            doubles=iv("doubles"),
            triples=iv("triples"),
            HR=iv("HR"),
            BB=iv("BB"),
            HBP=iv("HBP"),
            AB=ab,
            PA=pa,
        )
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


# ── API: add pitching line ───────────────────────────────────────────────────

@app.route("/api/pitching", methods=["POST"])
def add_pitching():
    d = request.json or {}
    try:
        def iv(k, default=0):
            try:
                return int(d.get(k, default))
            except Exception:
                return default

        ip_str = d.get("IP", "0.0")
        parts = str(ip_str).split(".")
        outs = int(parts[0]) * 3 + (int(parts[1]) if len(parts) > 1 else 0)
        strikes = iv("strikes")
        balls = iv("balls")
        total_pitches = iv("total_pitches") or strikes + balls

        db.add_pitching_line(
            player_id=iv("player_id"),
            game_date=d.get("game_date", ""),
            opponent=d.get("opponent", ""),
            home_away=d.get("home_away", "H"),
            outs=outs,
            BF=iv("BF"),
            K=iv("K"),
            BB=iv("BB"),
            HBP=iv("HBP"),
            strikes=strikes,
            balls=balls,
            total_pitches=total_pitches,
            H_allowed=iv("H_allowed"),
            HR_allowed=iv("HR_allowed"),
            doubles_allowed=iv("doubles_allowed"),
            triples_allowed=iv("triples_allowed"),
            R=iv("R"),
            ER=iv("ER"),
        )
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


# ── API: delete lines ─────────────────────────────────────────────────────────

@app.route("/api/batting/<int:line_id>", methods=["DELETE"])
def delete_batting(line_id):
    db.delete_batting_line(line_id)
    return jsonify({"ok": True})


@app.route("/api/pitching/<int:line_id>", methods=["DELETE"])
def delete_pitching(line_id):
    db.delete_pitching_line(line_id)
    return jsonify({"ok": True})


# ── API: scrape ───────────────────────────────────────────────────────────────

@app.route("/api/scrape", methods=["POST"])
def trigger_scrape():
    if not _scrape_lock.acquire(blocking=False):
        return jsonify({"ok": False, "error": "Scrape already running"}), 409

    def run():
        try:
            import scraper
            result = scraper.scrape_all(headless=True)
            _last_scrape["time"] = datetime.now().strftime("%B %d, %Y %I:%M %p")
            _last_scrape["result"] = result
        finally:
            _scrape_lock.release()

    threading.Thread(target=run, daemon=True).start()
    return jsonify({"ok": True, "message": "Scrape started in background"})


@app.route("/api/scrape/status")
def scrape_status():
    return jsonify({
        "running": not _scrape_lock.acquire(blocking=False) or _scrape_lock.release() or False,
        "last_scrape": _last_scrape.get("time"),
        "last_result": _last_scrape.get("result"),
    })


# ── API: players list ─────────────────────────────────────────────────────────

@app.route("/api/players")
def api_players():
    return jsonify(db.get_all_players())


if __name__ == "__main__":
    db.init_db()
    print("\n  Summer Stats Dashboard")
    print("  Open http://127.0.0.1:5000 in your browser\n")
    app.run(debug=True, port=5000, use_reloader=False)
