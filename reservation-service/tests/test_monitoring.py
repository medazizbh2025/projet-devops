import pytest
from datetime import datetime, timedelta
from app import create_app
from app.models import Reservation, db
from app.reporting import generate_usage_report, update_metrics
from unittest.mock import patch, MagicMock
import json
import os
from app.metrics_exporter import fetch_sonarqube_metrics
from app.metrics_scheduler import MetricsScheduler
import time
import prometheus_client

@pytest.fixture
def app():
    app = create_app()
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_metrics_update_endpoint(client):
    response = client.post('/api/metrics/update')
    assert response.status_code == 200
    assert response.json['status'] == 'success'

def test_usage_report_endpoint(client, app):
    # Create some test reservations
    with app.app_context():
        now = datetime.utcnow()
        reservations = [
            Reservation(
                salle_id=1,
                user_id=1,
                start_time=now - timedelta(hours=2),
                end_time=now - timedelta(hours=1),
                status='confirmed'
            ),
            Reservation(
                salle_id=1,
                user_id=2,
                start_time=now - timedelta(hours=4),
                end_time=now - timedelta(hours=3),
                status='confirmed'
            )
        ]
        db.session.bulk_save_objects(reservations)
        db.session.commit()

    # Test without date parameters
    response = client.get('/api/reports/usage')
    assert response.status_code == 200
    data = response.json
    assert 'total_reservations' in data
    assert 'avg_duration_minutes' in data
    assert 'reservations_per_room' in data
    assert 'peak_hours' in data

    # Test with date parameters
    start_date = (now - timedelta(days=1)).isoformat()
    end_date = now.isoformat()
    response = client.get(f'/api/reports/usage?start_date={start_date}&end_date={end_date}')
    assert response.status_code == 200

    # Test with invalid date format
    response = client.get('/api/reports/usage?start_date=invalid-date')
    assert response.status_code == 400

def test_generate_usage_report(app):
    with app.app_context():
        # Create test data
        now = datetime.utcnow()
        reservations = [
            Reservation(
                salle_id=1,
                user_id=1,
                start_time=now - timedelta(hours=2),
                end_time=now - timedelta(hours=1),
                status='confirmed'
            ),
            Reservation(
                salle_id=2,
                user_id=2,
                start_time=now - timedelta(hours=3),
                end_time=now - timedelta(hours=2),
                status='confirmed'
            )
        ]
        db.session.bulk_save_objects(reservations)
        db.session.commit()

        # Test report generation
        report = generate_usage_report(now - timedelta(days=1), now)
        assert report['total_reservations'] == 2
        assert 60 <= report['avg_duration_minutes'] <= 61  # Should be 60 minutes
        assert len(report['peak_hours']) > 0

def test_update_metrics(app):
    with app.app_context():
        # Create test data
        now = datetime.utcnow()
        reservation = Reservation(
            salle_id=1,
            user_id=1,
            start_time=now - timedelta(minutes=30),
            end_time=now + timedelta(minutes=30),
            status='confirmed'
        )
        db.session.add(reservation)
        db.session.commit()

        # Test metrics update
        update_metrics()
        # Note: We can't easily test the Prometheus metrics directly,
        # but we can verify the function runs without errors

@pytest.fixture
def mock_sonarqube_response():
    return {
        'component': {
            'measures': [
                {'metric': 'coverage', 'value': '75.5'},
                {'metric': 'code_smells', 'value': '15'},
                {'metric': 'sqale_index', 'value': '240'},
                {'metric': 'duplicated_lines_density', 'value': '3.2'}
            ]
        }
    }

@pytest.fixture
def mock_issues_response():
    return {
        'facets': [{
            'property': 'severities',
            'values': [
                {'val': 'MAJOR', 'count': 3, 'label': 'Bug severity: Major'},
                {'val': 'CRITICAL', 'count': 1, 'label': 'Vulnerability severity: Critical'}
            ]
        }]
    }

@pytest.fixture
def mock_gate_response():
    return {
        'projectStatus': {
            'status': 'OK'
        }
    }

@patch('requests.get')
def test_fetch_sonarqube_metrics(mock_get, mock_sonarqube_response, mock_issues_response, mock_gate_response):
    # Setup mock responses
    def mock_response(url, **kwargs):
        mock = MagicMock()
        if 'measures/component' in url:
            mock.json.return_value = mock_sonarqube_response
        elif 'issues/search' in url:
            mock.json.return_value = mock_issues_response
        elif 'qualitygates/project_status' in url:
            mock.json.return_value = mock_gate_response
        mock.raise_for_status.return_value = None
        return mock

    mock_get.side_effect = mock_response
    os.environ['SONAR_TOKEN'] = 'test-token'

    # Reset metrics (needed because Prometheus metrics are global)
    for collector in list(prometheus_client.REGISTRY._collector_to_names.keys()):
        prometheus_client.REGISTRY.unregister(collector)

    # Execute metrics collection
    fetch_sonarqube_metrics()

    # Verify metrics were updated correctly
    metrics = {}
    for metric in prometheus_client.REGISTRY.collect():
        for sample in metric.samples:
            metrics[sample.name] = sample.value

    assert metrics.get('sonarqube_coverage') == 75.5
    assert metrics.get('sonarqube_code_smells') == 15
    assert metrics.get('sonarqube_technical_debt_minutes') == 240
    assert metrics.get('sonarqube_quality_gate_status') == 1

def test_metrics_scheduler_lifecycle():
    scheduler = MetricsScheduler(interval=0.1)
    
    # Test start
    scheduler.start()
    assert scheduler.thread is not None
    assert scheduler.thread.is_alive()
    
    # Test duplicate start
    scheduler.start()  # Should log warning but not create new thread
    assert scheduler.thread.is_alive()
    
    # Test stop
    scheduler.stop()
    assert not scheduler.thread.is_alive()
    assert scheduler.thread is None
    
    # Test duplicate stop
    scheduler.stop()  # Should log warning but not error

@patch('app.metrics_exporter.fetch_sonarqube_metrics')
def test_metrics_scheduler_collection(mock_fetch):
    scheduler = MetricsScheduler(interval=0.1)
    scheduler.start()
    
    # Wait for at least one collection
    time.sleep(0.2)
    
    scheduler.stop()
    assert mock_fetch.called

@patch('app.metrics_exporter.fetch_sonarqube_metrics')
def test_metrics_scheduler_error_handling(mock_fetch):
    mock_fetch.side_effect = Exception("Test error")
    
    scheduler = MetricsScheduler(interval=0.1)
    scheduler.start()
    
    # Wait for at least one collection
    time.sleep(0.2)
    
    scheduler.stop()
    assert mock_fetch.called  # Should continue running despite errors