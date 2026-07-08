"""
CareerLift AI — Application Factory & Configuration
"""

import os
from flask import Flask
from dotenv import load_dotenv

load_dotenv()


def create_app() -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # --- Config ---
    app.secret_key = os.getenv("FLASK_SECRET_KEY", "careerlift-dev-secret-2024")
    app.config["MAX_CONTENT_LENGTH"] = int(os.getenv("MAX_CONTENT_LENGTH_MB", 10)) * 1024 * 1024
    app.config["UPLOAD_FOLDER"]      = os.path.join(os.path.dirname(__file__), os.getenv("UPLOAD_FOLDER", "uploads"))
    app.config["APP_NAME"]           = os.getenv("APP_NAME", "CareerLift")
    app.config["APP_TAGLINE"]        = os.getenv("APP_TAGLINE", "Dream. Prepare. Shine.")
    app.config["DEBUG"]              = os.getenv("FLASK_DEBUG", "True").lower() == "true"

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)

    # --- Register Blueprint ---
    from routes import main_bp
    app.register_blueprint(main_bp)

    return app
