# app/__init__.py

import os
from flask import Flask


def create_app(full_routes: bool = True) -> Flask:
    """Application factory.

    Parameters
    ----------
    full_routes:
        True  -> use app.routes_full (full REST API + live dashboard).
        False -> use app.routes      (original minimal routes).
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    app = Flask(
        __name__,
        template_folder=os.path.join(base_dir, "static", "templates"),
        static_folder=os.path.join(base_dir, "static"),
    )

    if full_routes:
        from app.routes_full import register_routes
    else:
        from app.routes import register_routes  # type: ignore[assignment]

    register_routes(app)
    return app
