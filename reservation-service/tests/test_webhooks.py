import pytest
import json
import hmac
import hashlib
from unittest.mock import patch, MagicMock
from flask import Flask
from app.webhooks import webhook_bp, verify_sonarqube_webhook

@pytest.fixture
def app():
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SONARQUBE_WEBHOOK_SECRET'] = 'test-secret'
    app.register_blueprint(webhook_bp)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def webhook_data():
    return {
        'serverUrl': 'http://sonarqube:9000',
        'taskId': 'AYx_spell6BVOXvd51auH',
        'status': 'SUCCESS',
        'analysedAt': '2025-04-22T10:00:00+0000',
        'revision': 'abc123',
        'project': {
            'key': 'salle-reservation',
            'name': 'Salle Reservation System',
            'url': 'http://sonarqube:9000/dashboard?id=salle-reservation'
        },
        'qualityGate': {
            'name': 'Salle Reservation Quality Gate',
            'status': 'ERROR',
            'conditions': [
                {
                    'metric': 'new_coverage',
                    'operator': 'LESS_THAN',
                    'value': '60.0',
                    'status': 'ERROR',
                    'errorThreshold': '80'
                }
            ]
        },
        'properties': {}
    }

def generate_signature(data, secret):
    mac = hmac.new(
        secret.encode(),
        msg=json.dumps(data).encode(),
        digestmod=hashlib.sha256
    )
    return mac.hexdigest()

def test_verify_webhook_signature(app, webhook_data):
    with app.test_request_context():
        # Valid signature
        signature = generate_signature(webhook_data, 'test-secret')
        headers = {'X-Sonar-Webhook-HMAC-SHA256': signature}
        assert verify_sonarqube_webhook(type('Request', (), {
            'headers': headers,
            'get_data': lambda: json.dumps(webhook_data).encode()
        }))

        # Invalid signature
        headers = {'X-Sonar-Webhook-HMAC-SHA256': 'invalid-signature'}
        assert not verify_sonarqube_webhook(type('Request', (), {
            'headers': headers,
            'get_data': lambda: json.dumps(webhook_data).encode()
        }))

        # Missing signature
        assert not verify_sonarqube_webhook(type('Request', (), {
            'headers': {},
            'get_data': lambda: json.dumps(webhook_data).encode()
        }))

@patch('app.webhooks.publish_message')
def test_webhook_endpoint_success(mock_publish, client, webhook_data):
    signature = generate_signature(webhook_data, 'test-secret')
    response = client.post(
        '/webhooks/sonarqube',
        json=webhook_data,
        headers={'X-Sonar-Webhook-HMAC-SHA256': signature}
    )
    
    assert response.status_code == 200
    assert response.json == {'status': 'success'}
    
    mock_publish.assert_called_once()
    call_args = mock_publish.call_args[0]
    assert call_args[0] == 'sonarqube-events'
    event_data = call_args[1]
    assert event_data['project_key'] == 'salle-reservation'
    assert event_data['quality_gate_status'] == 'ERROR'

def test_webhook_endpoint_invalid_signature(client, webhook_data):
    response = client.post(
        '/webhooks/sonarqube',
        json=webhook_data,
        headers={'X-Sonar-Webhook-HMAC-SHA256': 'invalid-signature'}
    )
    
    assert response.status_code == 401
    assert response.json == {'error': 'Invalid signature'}

@patch('app.webhooks.publish_message')
def test_webhook_kafka_error(mock_publish, client, webhook_data):
    mock_publish.side_effect = Exception('Kafka error')
    
    signature = generate_signature(webhook_data, 'test-secret')
    response = client.post(
        '/webhooks/sonarqube',
        json=webhook_data,
        headers={'X-Sonar-Webhook-HMAC-SHA256': signature}
    )
    
    assert response.status_code == 500
    assert response.json == {'error': 'Failed to process webhook'}

def test_webhook_invalid_payload(client):
    invalid_data = {'invalid': 'data'}
    signature = generate_signature(invalid_data, 'test-secret')
    response = client.post(
        '/webhooks/sonarqube',
        json=invalid_data,
        headers={'X-Sonar-Webhook-HMAC-SHA256': signature}
    )
    
    assert response.status_code == 500

@patch('app.webhooks.publish_message')
def test_webhook_different_quality_gates(mock_publish, client, webhook_data):
    signature = generate_signature(webhook_data, 'test-secret')
    
    # Test SUCCESS status
    webhook_data['qualityGate']['status'] = 'SUCCESS'
    response = client.post(
        '/webhooks/sonarqube',
        json=webhook_data,
        headers={'X-Sonar-Webhook-HMAC-SHA256': signature}
    )
    
    assert response.status_code == 200
    mock_publish.assert_called_with('sonarqube-events', {
        'project_key': 'salle-reservation',
        'quality_gate_status': 'SUCCESS',
        'conditions': webhook_data['qualityGate']['conditions'],
        'analysis_id': webhook_data['taskId'],
        'timestamp': webhook_data['analysedAt']
    })
    
    # Test WARNING status
    webhook_data['qualityGate']['status'] = 'WARNING'
    response = client.post(
        '/webhooks/sonarqube',
        json=webhook_data,
        headers={'X-Sonar-Webhook-HMAC-SHA256': signature}
    )
    
    assert response.status_code == 200
    mock_publish.assert_called_with('sonarqube-events', {
        'project_key': 'salle-reservation',
        'quality_gate_status': 'WARNING',
        'conditions': webhook_data['qualityGate']['conditions'],
        'analysis_id': webhook_data['taskId'],
        'timestamp': webhook_data['analysedAt']
    })