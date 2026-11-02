"""Flask application factory for Visioner-Control SDLA."""

from pathlib import Path

from flask import Flask


def create_app(full_routes: bool = True, config: dict | None = None) -> Flask:
    """Create an isolated Flask application with repository-relative assets."""
    base_dir = Path(__file__).resolve().parent.parent
    app = Flask(
        __name__,
        template_folder=str(base_dir / "static" / "templates"),
        static_folder=str(base_dir / "static"),
    )
    app.config.update(JSON_SORT_KEYS=False)
    if config:
        app.config.update(config)

    if full_routes:
        from app.routes_full import register_routes
    else:
        from app.routes import register_routes

    register_routes(app)
    return app
