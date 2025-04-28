from flask import current_app
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy import func
from .models import Reservation, db
from prometheus_client import Gauge
import os
import requests

# Prometheus metrics for reservation statistics
room_utilization = Gauge('room_utilization_percent', 'Room utilization percentage', ['room_id'])
daily_reservations = Gauge('daily_reservations_total', 'Number of reservations per day')
avg_duration = Gauge('reservation_average_duration_minutes', 'Average reservation duration in minutes')

def update_metrics():
    """Update metrics in Prometheus"""
    from prometheus_client import Gauge

    # Define metrics
    reservation_total = Gauge(
        'reservation_total',
        'Total number of reservations',
        ['status']
    )
    room_usage = Gauge(
        'room_usage_percent',
        'Room usage percentage',
        ['room_id']
    )
    avg_duration = Gauge(
        'reservation_duration_minutes_avg',
        'Average reservation duration in minutes'
    )

    # Update metrics
    now = datetime.utcnow()
    start_date = now - timedelta(days=1)

    # Total reservations by status
    status_counts = db.session.query(
        Reservation.status,
        func.count()
    ).filter(
        Reservation.start_time >= start_date
    ).group_by(Reservation.status).all()

    for status, count in status_counts:
        reservation_total.labels(status=status).set(count)

    # Room usage
    for room_id in range(1, 11):  # Assuming room IDs 1-10
        total_minutes = (now - start_date).total_seconds() / 60
        used_minutes = db.session.query(
            func.sum(
                func.extract('epoch', Reservation.end_time) -
                func.extract('epoch', Reservation.start_time)
            ) / 60
        ).filter(
            Reservation.salle_id == room_id,
            Reservation.status == 'confirmed',
            Reservation.start_time >= start_date
        ).scalar() or 0

        usage_percent = (used_minutes / total_minutes) * 100
        room_usage.labels(room_id=str(room_id)).set(usage_percent)

    # Average duration
    avg = db.session.query(
        func.avg(
            func.extract('epoch', Reservation.end_time) -
            func.extract('epoch', Reservation.start_time)
        ) / 60
    ).filter(
        Reservation.status == 'confirmed',
        Reservation.start_time >= start_date
    ).scalar() or 0

    avg_duration.set(avg)

def generate_usage_report(start_date=None, end_date=None):
    """Generate a usage report for reservations"""
    if not start_date:
        start_date = datetime.utcnow() - timedelta(days=30)
    if not end_date:
        end_date = datetime.utcnow()

    reservations = Reservation.query.filter(
        Reservation.start_time.between(start_date, end_date),
        Reservation.status == 'confirmed'
    ).all()

    # Calculate metrics
    total_reservations = len(reservations)
    if total_reservations == 0:
        return {
            'total_reservations': 0,
            'avg_duration_minutes': 0,
            'reservations_per_room': {},
            'peak_hours': []
        }

    # Calculate average duration
    total_duration = sum(
        (r.end_time - r.start_time).total_seconds() / 60
        for r in reservations
    )
    avg_duration = total_duration / total_reservations

    # Reservations per room
    room_counts = {}
    for r in reservations:
        room_counts[r.salle_id] = room_counts.get(r.salle_id, 0) + 1

    # Find peak hours
    hour_counts = db.session.query(
        func.date_part('hour', Reservation.start_time),
        func.count()
    ).filter(
        Reservation.start_time.between(start_date, end_date),
        Reservation.status == 'confirmed'
    ).group_by(
        func.date_part('hour', Reservation.start_time)
    ).all()

    peak_hours = sorted(
        [{'hour': int(hour), 'count': count} for hour, count in hour_counts],
        key=lambda x: x['count'],
        reverse=True
    )[:5]

    return {
        'total_reservations': total_reservations,
        'avg_duration_minutes': round(avg_duration, 2),
        'reservations_per_room': room_counts,
        'peak_hours': peak_hours
    }

def get_sonarqube_metrics():
    """Fetch metrics from SonarQube"""
    sonar_url = os.getenv('SONAR_URL', 'http://sonarqube:9000')
    sonar_token = os.getenv('SONAR_TOKEN')

    if not sonar_token:
        current_app.logger.error('SONAR_TOKEN not configured')
        return None

    headers = {'Authorization': f'Bearer {sonar_token}'}
    project_key = 'salle-reservation'

    try:
        # Get main metrics
        response = requests.get(
            f'{sonar_url}/api/measures/component',
            headers=headers,
            params={
                'component': project_key,
                'metricKeys': 'coverage,bugs,vulnerabilities,code_smells,duplicated_lines_density'
            }
        )
        response.raise_for_status()
        
        # Get quality gate status
        gate_response = requests.get(
            f'{sonar_url}/api/qualitygates/project_status',
            headers=headers,
            params={'projectKey': project_key}
        )
        gate_response.raise_for_status()

        metrics = response.json()['component']['measures']
        gate_status = gate_response.json()['projectStatus']['status']

        return {
            'quality_gate': gate_status,
            'metrics': {m['metric']: m['value'] for m in metrics}
        }

    except requests.exceptions.RequestException as e:
        current_app.logger.error(f'Error fetching SonarQube metrics: {str(e)}')
        return None

def generate_quality_report():
    """Generate a comprehensive quality report"""
    sonar_metrics = get_sonarqube_metrics()
    if not sonar_metrics:
        return {'error': 'Unable to fetch SonarQube metrics'}

    return {
        'timestamp': datetime.utcnow().isoformat(),
        'quality_gate_status': sonar_metrics['quality_gate'],
        'code_quality': {
            'coverage': float(sonar_metrics['metrics'].get('coverage', 0)),
            'bugs': int(sonar_metrics['metrics'].get('bugs', 0)),
            'vulnerabilities': int(sonar_metrics['metrics'].get('vulnerabilities', 0)),
            'code_smells': int(sonar_metrics['metrics'].get('code_smells', 0)),
            'duplication': float(sonar_metrics['metrics'].get('duplicated_lines_density', 0))
        },
        'threshold_status': {
            'coverage': float(sonar_metrics['metrics'].get('coverage', 0)) >= 80,
            'bugs': int(sonar_metrics['metrics'].get('bugs', 0)) == 0,
            'vulnerabilities': int(sonar_metrics['metrics'].get('vulnerabilities', 0)) == 0,
            'code_smells': int(sonar_metrics['metrics'].get('code_smells', 0)) < 10,
            'duplication': float(sonar_metrics['metrics'].get('duplicated_lines_density', 0)) < 3
        }
    }