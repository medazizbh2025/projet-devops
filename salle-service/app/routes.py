from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt
from .models import Salle, db
import requests

bp = Blueprint('routes', __name__)
RESERVATION_SERVICE_URL = "http://reservation-service:5002"

@bp.route('/salles', methods=['GET'])
def get_salles():
    min_capacity = request.args.get('min_capacity', type=int)
    equipments = request.args.getlist('equipment')
    
    query = Salle.query.filter_by(active=True)
    
    if min_capacity:
        query = query.filter(Salle.capacite >= min_capacity)
        
    if equipments:
        query = query.filter(Salle.equipements.contains(equipments))
    
    salles = query.all()
    return jsonify([salle.to_dict() for salle in salles])

@bp.route('/salles/search', methods=['GET'])
def search_salles():
    min_capacity = request.args.get('min_capacity', type=int)
    equipments = request.args.getlist('equipment')
    date = request.args.get('date')
    time_range = request.args.get('time_range')
    
    query = Salle.query.filter_by(active=True)
    
    if min_capacity:
        query = query.filter(Salle.capacite >= min_capacity)
        
    if equipments:
        query = query.filter(Salle.equipements.contains(equipments))
    
    salles = query.all()
    
    if date and time_range:
        available_salles = []
        for salle in salles:
            if check_availability(salle.id, date, time_range):
                available_salles.append(salle)
        return jsonify([s.to_dict() for s in available_salles])
    
    return jsonify([s.to_dict() for s in salles])

def check_availability(salle_id, date, time_range):
    try:
        response = requests.get(
            f"{RESERVATION_SERVICE_URL}/reservations/availability",
            params={
                'salle_id': salle_id,
                'date': date,
                'time_range': time_range
            }
        )
        return response.status_code == 200 and response.json().get('available', False)
    except requests.RequestException:
        return False

@bp.route('/salles', methods=['POST'])
@jwt_required()
def create_salle():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({"error": "Accès refusé"}), 403
        
    data = request.json
    salle = Salle(
        nom=data['nom'],
        capacite=data['capacite'],
        equipements=data.get('equipements', [])
    )
    db.session.add(salle)
    db.session.commit()
    return jsonify(salle.to_dict()), 201

@bp.route('/salles/<int:salle_id>', methods=['PUT'])
@jwt_required()
def update_salle(salle_id):
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({"error": "Accès refusé"}), 403
        
    salle = Salle.query.get_or_404(salle_id)
    data = request.json
    
    if 'nom' in data: salle.nom = data['nom']
    if 'capacite' in data: salle.capacite = data['capacite']
    if 'equipements' in data: salle.equipements = data['equipements']
    if 'active' in data: salle.active = data['active']
    
    db.session.commit()
    return jsonify(salle.to_dict())

@bp.route('/salles/<int:salle_id>', methods=['DELETE'])
@jwt_required()
def delete_salle(salle_id):
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({"error": "Accès refusé"}), 403
        
    salle = Salle.query.get_or_404(salle_id)
    salle.active = False
    db.session.commit()
    return jsonify({"message": "Salle désactivée"})