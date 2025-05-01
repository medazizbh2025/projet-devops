import os
import requests
from flask import current_app
from opentelemetry import trace
from .tracing import inject_trace_info, extract_trace_info
from kafka import KafkaProducer, KafkaConsumer
import json

class NotificationHandler:
    def __init__(self, kafka_bootstrap_servers=None):
        self.slack_webhook = os.getenv('SLACK_WEBHOOK_URL')
        self.teams_webhook = os.getenv('TEAMS_WEBHOOK_URL')
        self.notification_level = os.getenv('NOTIFICATION_LEVEL', 'ERROR')  # ERROR, WARNING, or ALL
        self.kafka_bootstrap_servers = kafka_bootstrap_servers
        if kafka_bootstrap_servers:
            self.producer = KafkaProducer(
                bootstrap_servers=kafka_bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8')
            )
        self.tracer = trace.get_tracer(__name__)
    
    def _should_notify(self, severity):
        if self.notification_level == 'ALL':
            return True
        if self.notification_level == 'WARNING':
            return severity in ['ERROR', 'WARNING']
        return severity == 'ERROR'
    
    def notify_quality_gate_status(self, event_data):
        """Handle quality gate status notification"""
        status = event_data['quality_gate_status']
        project_key = event_data['project_key']
        
        if status == 'ERROR' or self._should_notify(status):
            message = self._format_quality_gate_message(event_data)
            self._send_notifications(message)
    
    def _format_quality_gate_message(self, event_data):
        """Format the notification message"""
        status = event_data['quality_gate_status']
        project = event_data['project_key']
        conditions = event_data.get('conditions', [])
        
        failed_conditions = [
            c for c in conditions
            if c.get('status') == 'ERROR'
        ]
        
        message = {
            "title": f"SonarQube Quality Gate {status}",
            "project": project,
            "status": status,
            "analysis_time": event_data.get('timestamp'),
            "failed_conditions": [
                {
                    "metric": c.get('metricKey'),
                    "value": c.get('value'),
                    "threshold": c.get('threshold')
                }
                for c in failed_conditions
            ],
            "sonarqube_url": os.getenv('SONARQUBE_URL', 'http://sonarqube:9000')
        }
        
        return message
    
    def _send_notifications(self, message):
        """Send notifications to configured platforms"""
        if self.slack_webhook:
            self._send_slack_notification(message)
        
        if self.teams_webhook:
            self._send_teams_notification(message)
        
        if self.kafka_bootstrap_servers:
            self.send_notification("quality_gate_notifications", message)
    
    def _send_slack_notification(self, message):
        """Send notification to Slack"""
        slack_message = {
            "blocks": [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": message['title']
                    }
                },
                {
                    "type": "section",
                    "fields": [
                        {
                            "type": "mrkdwn",
                            "text": f"*Project:*\n{message['project']}"
                        },
                        {
                            "type": "mrkdwn",
                            "text": f"*Status:*\n{message['status']}"
                        }
                    ]
                }
            ]
        }
        
        if message['failed_conditions']:
            failed_conditions_text = "\n".join([
                f"• {c['metric']}: {c['value']} (threshold: {c['threshold']})"
                for c in message['failed_conditions']
            ])
            slack_message['blocks'].append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Failed Conditions:*\n{failed_conditions_text}"
                }
            })
        
        try:
            response = requests.post(self.slack_webhook, json=slack_message)
            response.raise_for_status()
        except Exception as e:
            current_app.logger.error(f"Failed to send Slack notification: {str(e)}")
    
    def _send_teams_notification(self, message):
        """Send notification to Microsoft Teams"""
        teams_message = {
            "@type": "MessageCard",
            "@context": "http://schema.org/extensions",
            "themeColor": "0076D7",
            "summary": message['title'],
            "sections": [{
                "activityTitle": message['title'],
                "facts": [
                    {
                        "name": "Project",
                        "value": message['project']
                    },
                    {
                        "name": "Status",
                        "value": message['status']
                    },
                    {
                        "name": "Analysis Time",
                        "value": message['analysis_time']
                    }
                ]
            }]
        }
        
        if message['failed_conditions']:
            teams_message['sections'].append({
                "title": "Failed Conditions",
                "text": "\n\n".join([
                    f"- {c['metric']}: {c['value']} (threshold: {c['threshold']})"
                    for c in message['failed_conditions']
                ])
            })
        
        try:
            response = requests.post(self.teams_webhook, json=teams_message)
            response.raise_for_status()
        except Exception as e:
            current_app.logger.error(f"Failed to send Teams notification: {str(e)}")
    
    def send_notification(self, topic, message):
        with self.tracer.start_as_current_span("send_notification") as span:
            # Create headers carrier for trace context
            carrier = {}
            inject_trace_info(carrier)
            
            # Convert carrier to Kafka-compatible headers
            headers = [(k, str(v).encode('utf-8')) for k, v in carrier.items()]
            
            # Add trace info to message
            message['trace_id'] = str(span.get_span_context().trace_id)
            message['span_id'] = str(span.get_span_context().span_id)
            
            # Send message with trace context
            self.producer.send(
                topic,
                value=message,
                headers=headers
            )
            self.producer.flush()
            
            # Add message details to span
            span.set_attribute("messaging.system", "kafka")
            span.set_attribute("messaging.destination", topic)
            span.set_attribute("messaging.message_id", message.get('id', ''))

    def consume_notifications(self, topic, callback):
        consumer = KafkaConsumer(
            topic,
            bootstrap_servers=self.kafka_bootstrap_servers,
            value_deserializer=lambda v: json.loads(v.decode('utf-8'))
        )
        
        for message in consumer:
            # Extract trace context from headers
            carrier = {k: v.decode('utf-8') for k, v in message.headers}
            context = extract_trace_info(carrier)
            
            with self.tracer.start_as_current_span(
                "process_notification",
                context=context
            ) as span:
                # Add message details to span
                span.set_attribute("messaging.system", "kafka")
                span.set_attribute("messaging.operation", "process")
                span.set_attribute("messaging.message_id", 
                                 message.value.get('id', ''))
                
                # Process message
                callback(message.value)