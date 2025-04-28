from flask import Blueprint, jsonify, request, redirect, url_for
from flask_jwt_extended import (
    jwt_required, 
    create_access_token,
    get_jwt_identity,
    get_jwt
)
from datetime import datetime
from functools import wraps
from .models import User, db
from .auth import oauth

bp = Blueprint('routes', __name__)

def admin_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        jwt_required()
        claims = get_jwt()
        if claims.get('role') != 'admin':
            return jsonify({"error": "Accès admin requis"}), 403
        return fn(*args, **kwargs)
    return wrapper

@bp.route('/login')
def login():
    redirect_uri = url_for('routes.authorize', _external=True)
    return oauth.google.authorize_redirect(redirect_uri)

@bp.route('/authorize')
def authorize():
    token = oauth.google.authorize_access_token()
    user_info = oauth.google.get('userinfo').json()
    
    user = User.query.filter_by(google_id=user_info['id']).first()
    
    if not user:
        user = User(
            google_id=user_info['id'],
            email=user_info['email'],
            name=user_info.get('name', ''),
            role='employee'
        )
        db.session.add(user)
    
    user.last_login = datetime.utcnow()
    db.session.commit()
    
    additional_claims = {"role": user.role, "email": user.email}
    access_token = create_access_token(identity=user.id, additional_claims=additional_claims)
    
    return jsonify({
        "access_token": access_token,
        "user": user.to_dict()
    })

@bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    return jsonify({"message": "Déconnexion réussie"}), 200

@bp.route('/users/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get_or_404(user_id)
    return jsonify(user.to_dict())

@bp.route('/users/<int:user_id>/role', methods=['PUT'])
@jwt_required()
@admin_required
def update_user_role(user_id):
    user = User.query.get_or_404(user_id)
    new_role = request.json.get('role')
    
    if new_role not in ['admin', 'employee', 'visitor']:
        return jsonify({"error": "Rôle invalide"}), 400
    
    user.role = new_role
    db.session.commit()
    
    return jsonify(user.to_dict())