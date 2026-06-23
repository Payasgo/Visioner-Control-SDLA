import os

from flask import Flask


def create_app() -> Flask:
    """Application factory. Resolves template/static paths relative to this file."""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "static", "templates"),
        static_folder=os.path.join(base_dir, "static"),
    )

    from app.routes import register_routes

    register_routes(app)
    return app
