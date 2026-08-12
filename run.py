"""
run.py — Flask application entry point.

Usage:
    python run.py

Or with Flask CLI:
    flask --app run run

The application is created via the factory so tests can also
import create_app without triggering a server start.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(debug=app.config.get("DEBUG", True), host="0.0.0.0", port=5000)
