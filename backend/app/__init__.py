import os
from flask import Flask, jsonify
from app.config import config
from app.extensions import db, migrate, jwt, cors
from app.routes.auth import is_token_revoked
from dotenv import load_dotenv
load_dotenv()


def create_app(config_name: str = None) -> Flask:
    config_name = config_name or os.environ.get("FLASK_ENV", "default")
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": "*"}})

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
        return jsonify({"success": False, "error": "Token has expired."}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({"success": False, "error": "Invalid token."}), 401

    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({"success": False, "error": "Authorization token required."}), 401

    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({"success": False, "error": "Token has been revoked."}), 401


    @app.route("/api/health", methods=["GET"])
    def health():
        return jsonify({"status": "ok", "service": "PLV Room Monitor API"}), 200

    return app