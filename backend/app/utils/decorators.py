from functools import wraps
from flask import jsonify
from flask_jwt_extended import verify_jwt_in_request, get_jwt_identity
from app.models.user import User


def _get_current_user():
    user_id = get_jwt_identity()
    return User.query.get(user_id)


def jwt_required_with_active(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        verify_jwt_in_request()
        user = _get_current_user()
        if not user or not user.is_active:
            return jsonify({"error": "Account is inactive or does not exist."}), 403
        return fn(*args, **kwargs)
    return wrapper


def roles_required(*roles):
    """
    Decorator factory.  Usage:
        @roles_required("superadmin")
        @roles_required("superadmin", "admin")
    """
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            verify_jwt_in_request()
            user = _get_current_user()
            if not user or not user.is_active:
                return jsonify({"error": "Account is inactive or does not exist."}), 403
            if user.role not in roles:
                return jsonify({"error": "Insufficient permissions."}), 403
            return fn(*args, **kwargs)
        return wrapper
    return decorator

def superadmin_required(fn):
    return roles_required("superadmin")(fn)

def admin_required(fn):
    return roles_required("admin", "superadmin")(fn)

def any_authenticated(fn):
    return jwt_required_with_active(fn)