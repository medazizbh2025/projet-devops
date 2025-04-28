from flask import Blueprint, request, jsonify, current_app
import hmac
import hashlib
from .kafka_producer import publish_message
from .notifications import NotificationHandler

webhook_bp = Blueprint('webhooks', __name__)
notification_handler = NotificationHandler()

def verify_sonarqube_webhook(request):
    """Verify SonarQube webhook signature"""
    if 'X-Sonar-Webhook-HMAC-SHA256' not in request.headers:
        return False
    
    secret = current_app.config.get('SONARQUBE_WEBHOOK_SECRET')
    if not secret:
        return False
    
    signature = request.headers['X-Sonar-Webhook-HMAC-SHA256']
    
    # Calculate expected signature
    mac = hmac.new(
        secret.encode(),
        msg=request.get_data(),
        digestmod=hashlib.sha256
    )
    expected_signature = mac.hexdigest()
    
    return hmac.compare_digest(signature, expected_signature)

@webhook_bp.route('/webhooks/sonarqube', methods=['POST'])
def sonarqube_webhook():
    """Handle SonarQube analysis webhook"""
    if not verify_sonarqube_webhook(request):
        return jsonify({'error': 'Invalid signature'}), 401
    
    data = request.json
    
    # Extract relevant quality metrics
    quality_gate = data.get('qualityGate', {})
    project = data.get('project', {})
    
    # Prepare event data
    event_data = {
        'project_key': project.get('key'),
        'quality_gate_status': quality_gate.get('status'),
        'conditions': quality_gate.get('conditions', []),
        'analysis_id': data.get('analysisId'),
        'timestamp': data.get('analysedAt')
    }
    
    # Publish event to Kafka
    try:
        publish_message('sonarqube-events', event_data)
        current_app.logger.info(f"Published SonarQube analysis event for {project.get('key')}")
        
        # Send notifications if needed
        notification_handler.notify_quality_gate_status(event_data)
        
        # Log additional details for failed quality gates
        if quality_gate.get('status') == 'ERROR':
            failed_conditions = [
                c for c in quality_gate.get('conditions', [])
                if c.get('status') == 'ERROR'
            ]
            current_app.logger.warning(
                f"Quality gate failed for {project.get('key')}. "
                f"Failed conditions: {failed_conditions}"
            )
    
    except Exception as e:
        current_app.logger.error(f"Failed to process webhook: {str(e)}")
        return jsonify({'error': 'Failed to process webhook'}), 500
    
    return jsonify({'status': 'success'}), 200