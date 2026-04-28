import os
from flask import Flask, jsonify, send_from_directory, abort
from app.config import config
from app.extensions import db, migrate, jwt, cors
from app.routes.auth import is_token_revoked
from dotenv import load_dotenv
load_dotenv()


def create_app(config_name: str = None) -> Flask:
    config_name = config_name or os.environ.get("FLASK_ENV", "default")

    # Absolute path to the project root (two levels up from app/)
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    frontend_dir = os.path.join(project_root, "frontend")

    app = Flask(
        __name__,
        static_folder=os.path.join(frontend_dir, "assets"),
        static_url_path="/assets",
    )
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*", "supports_credentials": True}})

    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        return is_token_revoked(jwt_header, jwt_payload)

    from app.routes import auth_bp, superadmin_bp, rooms_bp, reservations_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(superadmin_bp)
    app.register_blueprint(rooms_bp)
    app.register_blueprint(reservations_bp)

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"success": False, "error": "Resource not found."}), 404

    @app.errorhandler(405)
    def method_not_allowed(e):
        return jsonify({"success": False, "error": "Method not allowed."}), 405

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()
        return jsonify({"success": False, "error": "Internal server error."}), 500

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        app.logger.warning("JWT expired: %s", jwt_payload)
        return jsonify({"success": False, "error": "Token has expired."}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        app.logger.warning("JWT invalid: %s", error)
        return jsonify({"success": False, "error": "Invalid token."}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        app.logger.warning("JWT missing: %s", error)
        return jsonify({"success": False, "error": "Authorization token required."}), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        app.logger.warning("JWT revoked: %s", jwt_payload)
        return jsonify({"success": False, "error": "Token has been revoked."}), 401


    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "PLV Room Monitor API"}), 200

    # Serve the root index page
    @app.route("/", methods=["GET"])
    def serve_index():
        return send_from_directory(frontend_dir, "index.html")

    # Serve other frontend pages and static files
    @app.route("/<path:path>", methods=["GET"])
    def serve_frontend(path):
        # Let Flask's built-in static handler serve /assets/*
        if path.startswith("api/") or path.startswith("assets/"):
            abort(404)
        requested = os.path.abspath(os.path.join(frontend_dir, path))
        if not requested.startswith(os.path.abspath(frontend_dir)):
            abort(404)
        if os.path.isfile(requested):
            return send_from_directory(frontend_dir, path)
        # If the path doesn't match a file, try serving index.html for SPA behavior
        index_path = os.path.join(frontend_dir, "index.html")
        if os.path.isfile(index_path):
            return send_from_directory(frontend_dir, "index.html")
        abort(404)

    return app
