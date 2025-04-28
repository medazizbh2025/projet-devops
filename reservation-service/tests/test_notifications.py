import pytest
from unittest.mock import patch, MagicMock
from app.notifications import NotificationHandler
import responses
import os

@pytest.fixture
def notification_handler():
    os.environ['SLACK_WEBHOOK_URL'] = 'http://slack-webhook.test'
    os.environ['TEAMS_WEBHOOK_URL'] = 'http://teams-webhook.test'
    os.environ['NOTIFICATION_LEVEL'] = 'ERROR'
    return NotificationHandler()

@pytest.fixture
def sample_event_data():
    return {
        'project_key': 'test-project',
        'quality_gate_status': 'ERROR',
        'timestamp': '2025-04-22T10:00:00Z',
        'conditions': [
            {
                'status': 'ERROR',
                'metricKey': 'new_coverage',
                'value': '60',
                'threshold': '80'
            },
            {
                'status': 'ERROR',
                'metricKey': 'new_bugs',
                'value': '5',
                'threshold': '0'
            }
        ]
    }

@responses.activate
def test_slack_notification(notification_handler, sample_event_data):
    # Mock Slack webhook
    responses.add(
        responses.POST,
        'http://slack-webhook.test',
        json={'ok': True},
        status=200
    )

    notification_handler.notify_quality_gate_status(sample_event_data)

    assert len(responses.calls) == 1
    request_body = responses.calls[0].request.body.decode()
    assert 'Quality Gate ERROR' in request_body
    assert 'test-project' in request_body
    assert 'new_coverage' in request_body
    assert 'new_bugs' in request_body

@responses.activate
def test_teams_notification(notification_handler, sample_event_data):
    # Mock Teams webhook
    responses.add(
        responses.POST,
        'http://teams-webhook.test',
        json={'ok': True},
        status=200
    )

    notification_handler.notify_quality_gate_status(sample_event_data)

    assert len(responses.calls) == 1
    request_body = responses.calls[0].request.body.decode()
    assert 'Quality Gate ERROR' in request_body
    assert 'test-project' in request_body
    assert 'new_coverage' in request_body
    assert 'new_bugs' in request_body

def test_notification_level_filtering(notification_handler):
    with patch.object(notification_handler, '_send_notifications') as mock_send:
        # Test ERROR level
        os.environ['NOTIFICATION_LEVEL'] = 'ERROR'
        notification_handler = NotificationHandler()
        
        # Should notify for ERROR
        notification_handler.notify_quality_gate_status({
            'quality_gate_status': 'ERROR',
            'project_key': 'test'
        })
        assert mock_send.call_count == 1
        
        # Should not notify for WARNING
        notification_handler.notify_quality_gate_status({
            'quality_gate_status': 'WARNING',
            'project_key': 'test'
        })
        assert mock_send.call_count == 1
        
        # Test WARNING level
        os.environ['NOTIFICATION_LEVEL'] = 'WARNING'
        notification_handler = NotificationHandler()
        
        # Should notify for both WARNING and ERROR
        notification_handler.notify_quality_gate_status({
            'quality_gate_status': 'WARNING',
            'project_key': 'test'
        })
        assert mock_send.call_count == 2
        
        notification_handler.notify_quality_gate_status({
            'quality_gate_status': 'ERROR',
            'project_key': 'test'
        })
        assert mock_send.call_count == 3

def test_message_formatting(notification_handler, sample_event_data):
    message = notification_handler._format_quality_gate_message(sample_event_data)
    
    assert message['title'] == 'SonarQube Quality Gate ERROR'
    assert message['project'] == 'test-project'
    assert message['status'] == 'ERROR'
    assert len(message['failed_conditions']) == 2
    
    coverage_condition = next(
        c for c in message['failed_conditions']
        if c['metric'] == 'new_coverage'
    )
    assert coverage_condition['value'] == '60'
    assert coverage_condition['threshold'] == '80'
    
    bugs_condition = next(
        c for c in message['failed_conditions']
        if c['metric'] == 'new_bugs'
    )
    assert bugs_condition['value'] == '5'
    assert bugs_condition['threshold'] == '0'

@responses.activate
def test_notification_error_handling(notification_handler, sample_event_data):
    # Mock failed webhook calls
    responses.add(
        responses.POST,
        'http://slack-webhook.test',
        status=500
    )
    responses.add(
        responses.POST,
        'http://teams-webhook.test',
        status=500
    )
    
    # Should not raise exception on webhook failures
    notification_handler.notify_quality_gate_status(sample_event_data)
    assert len(responses.calls) == 2  # Both webhooks attempted

def test_empty_webhooks(sample_event_data):
    # Test with no webhooks configured
    os.environ.pop('SLACK_WEBHOOK_URL', None)
    os.environ.pop('TEAMS_WEBHOOK_URL', None)
    
    handler = NotificationHandler()
    # Should not raise any exceptions
    handler.notify_quality_gate_status(sample_event_data)