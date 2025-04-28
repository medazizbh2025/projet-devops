from kafka import KafkaProducer
import json
from prometheus_client import Counter, Histogram
import time
from flask import current_app
from datetime import datetime

# Prometheus metrics
kafka_message_counter = Counter('kafka_messages_total', 'Number of messages published to Kafka', ['topic'])
kafka_message_latency = Histogram('kafka_publish_latency_seconds', 'Time spent publishing messages to Kafka')

producer = None

def init_kafka(app):
    global producer
    producer = KafkaProducer(
        bootstrap_servers=app.config['KAFKA_BOOTSTRAP_SERVERS'],
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

def publish_message(topic, message):
    if producer is None:
        raise RuntimeError("Kafka producer not initialized")
    
    start_time = time.time()
    try:
        future = producer.send(topic, message)
        future.get(timeout=10)  # Wait for message to be sent
        
        # Record metrics
        kafka_message_counter.labels(topic=topic).inc()
        kafka_message_latency.observe(time.time() - start_time)
        
        current_app.logger.info({
            'event': 'kafka_message_published',
            'topic': topic,
            'status': 'success',
            'duration': time.time() - start_time
        })
        
    except Exception as e:
        current_app.logger.error({
            'event': 'kafka_message_failed',
            'topic': topic,
            'error': str(e),
            'duration': time.time() - start_time
        })
        raise

def send_reservation_event(event_type, reservation):
    if not producer:
        raise RuntimeError("Kafka producer not initialized")
    
    event = {
        "event_type": event_type,
        "reservation_id": reservation.id,
        "salle_id": reservation.salle_id,
        "user_id": reservation.user_id,
        "start_time": reservation.start_time.isoformat(),
        "end_time": reservation.end_time.isoformat(),
        "timestamp": datetime.utcnow().isoformat()
    }
    
    publish_message('reservation-events', event)