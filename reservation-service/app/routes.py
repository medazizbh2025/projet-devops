from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, get_jwt
from datetime import datetime, timedelta
from .models import Reservation, db
from .kafka_producer import send_reservation_event
from .reporting import generate_monthly_report, generate_usage_report, update_metrics, generate_quality_report
import pandas as pd

bp = Blueprint('routes', __name__)

@bp.route('/reservations', methods=['POST'])
@jwt_required()
def create_reservation():
    data = request.json
    current_user = get_jwt_identity()
    
    try:
        start_time = datetime.fromisoformat(data['start_time'])
        end_time = datetime.fromisoformat(data['end_time'])
    except ValueError:
        return jsonify({"error": "Format de date invalide"}), 400
    
    if end_time <= start_time:
        return jsonify({"error": "La fin doit être après le début"}), 400
    
    conflict = Reservation.query.filter(
        Reservation.salle_id == data['salle_id'],
        Reservation.status == 'confirmed',
        Reservation.start_time < end_time,
        Reservation.end_time > start_time
    ).first()
    
    if conflict:
        return jsonify({
            "error": "Conflit de réservation",
            "conflicting_reservation": conflict.to_dict()
        }), 409
    
    reservation = Reservation(
        salle_id=data['salle_id'],
        user_id=current_user,
        start_time=start_time,
        end_time=end_time
    )
    db.session.add(reservation)
    db.session.commit()
    
    send_reservation_event('reservation_created', reservation)
    return jsonify(reservation.to_dict()), 201

@bp.route('/reservations/<int:reservation_id>', methods=['DELETE'])
@jwt_required()
def cancel_reservation(reservation_id):
    reservation = Reservation.query.get_or_404(reservation_id)
    current_user = get_jwt_identity()
    claims = get_jwt()
    
    if reservation.user_id != current_user and claims.get('role') != 'admin':
        return jsonify({"error": "Accès refusé"}), 403
    
    reservation.status = 'cancelled'
    db.session.commit()
    
    event_type = 'admin_cancelled_reservation' if claims.get('role') == 'admin' else 'reservation_cancelled'
    send_reservation_event(event_type, reservation)
    
    return jsonify({"message": "Réservation annulée"})

@bp.route('/reservations/availability', methods=['GET'])
def check_availability():
    salle_id = request.args.get('salle_id', type=int)
    date = request.args.get('date')
    time_range = request.args.get('time_range')
    
    if not all([salle_id, date, time_range]):
        return jsonify({"error": "Paramètres manquants"}), 400
    
    try:
        start_str, end_str = time_range.split('-')
        start_time = datetime.fromisoformat(f"{date}T{start_str}")
        end_time = datetime.fromisoformat(f"{date}T{end_str}")
    except ValueError:
        return jsonify({"error": "Format de date/heure invalide"}), 400
    
    conflict = Reservation.query.filter(
        Reservation.salle_id == salle_id,
        Reservation.status == 'confirmed',
        Reservation.start_time < end_time,
        Reservation.end_time > start_time
    ).first()
    
    return jsonify({"available": not conflict})

@bp.route('/admin/reservations/history', methods=['GET'])
@jwt_required()
def get_reservation_history():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({"error": "Accès refusé"}), 403
        
    salle_id = request.args.get('salle_id', type=int)
    user_id = request.args.get('user_id', type=int)
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Reservation.query
    
    if salle_id:
        query = query.filter_by(salle_id=salle_id)
    if user_id:
        query = query.filter_by(user_id=user_id)
    if start_date:
        query = query.filter(Reservation.start_time >= start_date)
    if end_date:
        query = query.filter(Reservation.start_time <= end_date)
    
    reservations = query.order_by(Reservation.start_time.desc()).all()
    return jsonify([r.to_dict() for r in reservations])

@bp.route('/admin/reports/monthly', methods=['GET'])
@jwt_required()
def monthly_report():
    claims = get_jwt()
    if claims.get('role') != 'admin':
        return jsonify({"error": "Accès refusé"}), 403
        
    report = generate_monthly_report()
    return jsonify(report)

@bp.route('/api/metrics/update', methods=['POST'])
def update_metrics_endpoint():
    """Endpoint to manually trigger metrics update"""
    try:
        update_metrics()
        return jsonify({'status': 'success', 'message': 'Metrics updated successfully'}), 200
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/api/reports/usage', methods=['GET'])
def get_usage_report():
    """Generate usage report for a given time period"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        if start_date:
            start_date = datetime.fromisoformat(start_date)
        if end_date:
            end_date = datetime.fromisoformat(end_date)
            
        report = generate_usage_report(start_date, end_date)
        return jsonify(report), 200
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Invalid date format. Use ISO format (YYYY-MM-DDTHH:MM:SS)'}), 400
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@bp.route('/api/quality/report', methods=['GET'])
def get_quality_report():
    """Get quality report from SonarQube"""
    try:
        report = generate_quality_report()
        if 'error' in report:
            return jsonify(report), 500
        return jsonify(report), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Schedule metrics update every 5 minutes
@bp.before_app_first_request
def init_metrics():
    update_metrics()