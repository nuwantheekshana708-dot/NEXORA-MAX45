
from flask import (
    Flask,
    render_template,
    request,
    flash,
    redirect,
    url_for,
    send_from_directory,
    abort
)

from flask_wtf import CSRFProtect
from flask_wtf.csrf import generate_csrf
from pathlib import Path
import os
import secrets
import sqlite3
# ----------------------------------
# FLASK APP SETTINGS
# ----------------------------------

app = Flask(__name__)

BASE_DIR = Path(__file__).resolve().parent

DATABASE = BASE_DIR / "messages.db"


def init_db():
    conn = sqlite3.connect(DATABASE)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL,
            message TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


init_db()

app.secret_key = os.environ.get("SECRET_KEY") or secrets.token_hex(32)

# CSRF PROTECTION
csrf = CSRFProtect()

csrf.init_app(app)

@app.context_processor
def inject_csrf_token():
    return {
        "csrf_token": generate_csrf
    }
# APP CONFIGURATION
app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024

app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False
)


# ----------------------------------
# WEBSITE INFORMATION
# ----------------------------------

BASE_DIR = Path(__file__).resolve().parent
DOWNLOAD_DIR = BASE_DIR / "static" / "downloads"

SITE_NAME = "NEXORA MAX45"

YOUTUBE_CHANNEL = "https://www.youtube.com/@NuwanTheekshanamax"
YOUTUBE_SUBSCRIBE = YOUTUBE_CHANNEL + "?sub_confirmation=1"

# ----------------------------------
# DOWNLOAD FILES
# ----------------------------------

DOWNLOADS = {
    "cyberon-browser": {
        "name": "CYBERON Browser",
        "filename": "CYBERON Browser.exe",
        "platform": "Windows 10 / 11",
        "version": "1.0.0",
    },
    "driver-manager": {
        "name": "NEXORA Driver Manager",
        "filename": "NEXORA_Driver_Manager.exe",
        "platform": "Windows 10 / 11",
        "version": "1.0.0",
    },
    "media-player": {
        "name": "NEXORA Media Player",
        "filename": "NEXORA Media Player.exe",
        "platform": "Windows 10 / 11",
        "version": "1.0.0",
    },
    "hsk1-master": {
        "name": "HSK1 Master",
        "filename": "HSK1_Master.exe",
        "platform": "Windows 10 / 11",
        "version": "1.0.0",
    },
    "nexora-calculator": {
        "name": "NEXORA Calculator",
        "filename": "NEXORA Calculator.exe",
        "platform": "Windows 10 / 11",
        "version": "1.0.0",
    },
    "windows": {
        "name": "NEXORA Driver Backup App for Windows",
        "filename": "NEXORA-Driver-Backup-Setup.exe",
        "platform": "Windows 10 / 11 (64-bit)",
        "version": "1.0.0",
    },
    "android": {
        "name": "NEXORA Driver Backup App for Android",
        "filename": "NEXORA-Driver-Backup.apk",
        "platform": "Android",
        "version": "1.0.0",
    },
}

# ----------------------------------
# GLOBAL TEMPLATE VARIABLES
# ----------------------------------

@app.context_processor
def inject_globals():
    return {
        "site_name": SITE_NAME,
        "youtube_channel": YOUTUBE_CHANNEL,
        "youtube_subscribe": YOUTUBE_SUBSCRIBE,
    }

# ----------------------------------
# SECURITY HEADERS
# ----------------------------------

@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=()"
    )

    return response

# ----------------------------------
# HOME PAGE
# ----------------------------------

@app.route("/")
def home():
    return render_template(
        "index.html",
        downloads=DOWNLOADS
    )

# ----------------------------------
# DOWNLOADS PAGE
# ----------------------------------

@app.route("/downloads")
def downloads():
    display_downloads = {}

    for key, item in DOWNLOADS.items():
        display_item = item.copy()

        file_path = DOWNLOAD_DIR / item["filename"]

        if file_path.is_file():
            size_bytes = file_path.stat().st_size
            size_mb = size_bytes / (1024 * 1024)

            display_item["size"] = f"{size_mb:.2f} MB"
            display_item["available"] = True
        else:
            display_item["size"] = "File unavailable"
            display_item["available"] = False

        display_downloads[key] = display_item

    return render_template(
        "downloads.html",
        downloads=display_downloads
    )

# ----------------------------------
# DOWNLOAD FILE ROUTE
# ----------------------------------

@app.route("/download/<platform>")
def download_file(platform):
    item = DOWNLOADS.get(platform)

    if not item:
        abort(404)

    file_path = DOWNLOAD_DIR / item["filename"]

    if not file_path.is_file():
        flash(
            f'{item["filename"]} file එක downloads folder එකේ නැහැ.',
            "error"
        )
        return redirect(url_for("downloads"))

    return send_from_directory(
        DOWNLOAD_DIR,
        item["filename"],
        as_attachment=True
    )

# ----------------------------------
# YOUTUBE PAGE
# ----------------------------------

@app.route("/youtube")
def youtube():
    return render_template("youtube.html")

# ----------------------------------
# ABOUT PAGE
# ----------------------------------

@app.route("/about")
def about():
    return render_template("about.html")

# ----------------------------------
# CONTACT PAGE
# ----------------------------------




@app.route("/contact", methods=["GET", "POST"])
def contact():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            flash("Please fill in all fields.", "error")
            return redirect(url_for("contact"))

        try:
            conn = sqlite3.connect(DATABASE)

            conn.execute(
                """
                INSERT INTO messages (name, email, message)
                VALUES (?, ?, ?)
                """,
                (name, email, message)
            )

            conn.commit()
            conn.close()

            flash("Your message has been saved successfully!", "success")

        except sqlite3.Error:
            flash("Sorry! Something went wrong. Please try again.", "error")

        return redirect(url_for("contact"))

    return render_template("contact.html", site_name="NEXORA MAX45")


   
# ----------------------------------
# ERROR HANDLERS
# ----------------------------------

@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


@app.errorhandler(413)
def file_too_large(error):
    return "Request is too large.", 413


# ----------------------------------
# RUN WEBSITE
# ----------------------------------

@app.errorhandler(Exception)
def diagnostic_error(error):
    import traceback

    print("\n========== REAL SERVER ERROR ==========", flush=True)
    traceback.print_exception(
        type(error), error, error.__traceback__
    )
    print("========== END SERVER ERROR ==========", flush=True)

    return "DIAGNOSTIC ERROR: " + str(error), 500

if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
