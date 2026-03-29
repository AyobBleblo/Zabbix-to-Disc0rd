import sqlite3
import json
import os
from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = os.getenv("DASHBOARD_SECRET_KEY", "dev-secret-change-me")

DB_PATH = os.getenv("DASHBOARD_DB_PATH", "dashboard.db")


def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # So rows behave like dicts
    return conn


def init_db():
    """Create tables if they don't exist."""
    conn = get_db()
    conn.executescript(
    """
    CREATE TABLE IF NOT EXISTS channels (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        discord_channel_id TEXT NOT NULL,
        bot_token TEXT NOT NULL,
        allowed_severities TEXT DEFAULT '[0,1,2,3,4,5]',
        include_substrings TEXT DEFAULT '[]',
        exclude_substrings TEXT DEFAULT '[]',
        host_ignores TEXT DEFAULT '[]',
        enabled INTEGER DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS message_tracking (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        channel_config_id INTEGER NOT NULL,
        severity INTEGER NOT NULL,
        discord_message_id TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (channel_config_id) REFERENCES channels(id)
    );
""")
    conn.commit()
    conn.close()


# Auto-create tables on startup
init_db()
# ─── List all channels ──────────────────────────────────────────


@app.route("/")
def index():
    conn = get_db()
    channels = conn.execute("SELECT * FROM channels ORDER BY id").fetchall()
    conn.close()
    return render_template("index.html", channels=channels)


# ─── New channel form ───────────────────────────────────────────
@app.route("/channel/new")
def channel_new():
    return render_template("channel_form.html", channel=None)


# ─── Create channel ─────────────────────────────────────────────
@app.route("/channel/create", methods=["POST"])
def channel_create():
    conn = get_db()
    conn.execute(
        """INSERT INTO channels
           (name, discord_channel_id, bot_token, allowed_severities,
            include_substrings, exclude_substrings, host_ignores, enabled)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            request.form["name"],
            request.form["discord_channel_id"],
            request.form["bot_token"],
            _parse_severities(request.form.getlist("severity")),
            _parse_comma_list(request.form.get("include_substrings", "")),
            _parse_comma_list(request.form.get("exclude_substrings", "")),
            _parse_host_ignores(request.form),
            1 if request.form.get("enabled") else 0,
        ),
    )
    conn.commit()
    conn.close()
    flash("Channel created!", "success")
    return redirect(url_for("index"))


# ─── Edit channel form ──────────────────────────────────────────
@app.route("/channel/<int:channel_id>/edit")
def channel_edit(channel_id):
    conn = get_db()
    channel = conn.execute(
        "SELECT * FROM channels WHERE id = ?", (channel_id,)
    ).fetchone()
    conn.close()
    if not channel:
        flash("Channel not found", "error")
        return redirect(url_for("index"))
    return render_template("channel_form.html", channel=channel)


# ─── Update channel ─────────────────────────────────────────────
@app.route("/channel/<int:channel_id>/update", methods=["POST"])
def channel_update(channel_id):
    conn = get_db()
    conn.execute(
        """UPDATE channels SET
           name=?, discord_channel_id=?, bot_token=?, allowed_severities=?,
           include_substrings=?, exclude_substrings=?, host_ignores=?, enabled=?
           WHERE id=?""",
        (
            request.form["name"],
            request.form["discord_channel_id"],
            request.form["bot_token"],
            _parse_severities(request.form.getlist("severity")),
            _parse_comma_list(request.form.get("include_substrings", "")),
            _parse_comma_list(request.form.get("exclude_substrings", "")),
            _parse_host_ignores(request.form),
            1 if request.form.get("enabled") else 0,
            channel_id,
        ),
    )
    conn.commit()
    conn.close()
    flash("Channel updated!", "success")
    return redirect(url_for("index"))


# ─── Delete channel ─────────────────────────────────────────────
@app.route("/channel/<int:channel_id>/delete", methods=["POST"])
def channel_delete(channel_id):
    conn = get_db()
    conn.execute(
        "DELETE FROM message_tracking WHERE channel_config_id = ?", (channel_id,))
    conn.execute("DELETE FROM channels WHERE id = ?", (channel_id,))
    conn.commit()
    conn.close()
    flash("Channel deleted!", "success")
    return redirect(url_for("index"))


# ─── Helper functions ────────────────────────────────────────────
def _parse_severities(values: list) -> str:
    """Convert form checkbox values like ['1','3','4'] → '[1,3,4]' JSON."""
    ints = sorted({int(v) for v in values if v.isdigit() and 0 <= int(v) <= 5})
    return json.dumps(ints if ints else [0, 1, 2, 3, 4, 5])


def _parse_comma_list(text: str) -> str:
    """Convert 'power, test, link' → '["power","test","link"]' JSON"""
    items = [s.strip() for s in text.split(",") if s.strip()]
    return json.dumps(items)


def _parse_host_ignores(form) -> str:
    """Parse dynamic host-ignore rows from the form."""
    ignores = []
    # The form sends: host_ignore_sub_0, host_ignore_host_0, etc.
    i = 0
    while True:
        sub = form.get(f"host_ignore_sub_{i}")
        host = form.get(f"host_ignore_host_{i}")
        if sub is None:
            break
        if sub.strip() and host.strip():
            ignores.append({"substring": sub.strip(),
                           "hostname": host.strip()})
        i += 1
    return json.dumps(ignores)


# ─── Run ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=True, port=5000)
