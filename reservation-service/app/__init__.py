from flask import Flask, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from prometheus_flask_exporter import PrometheusMetrics
from prometheus_client import start_http_server
from pythonjsonlogger import jsonlogger
import logging
import watchtower
import os
import uuid
from .tracing import init_tracer
from .metrics_scheduler import MetricsScheduler

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Initialize tracing
    tracer = init_tracer(app)
    
    # Configure metrics
    metrics = PrometheusMetrics(app)
    metrics.info('reservation_service_info', 'Reservation service info', version='1.0.0')

    # Start Prometheus metrics server
    metrics_port = int(os.getenv('METRICS_PORT', '9090'))
    start_http_server(metrics_port)
    
    # Initialize and start metrics scheduler
    metrics_scheduler = MetricsScheduler()
    metrics_scheduler.start()
    
    # Store scheduler in app context for cleanup
    app.metrics_scheduler = metrics_scheduler
    
    # Configure JSON logging
    json_handler = logging.StreamHandler()
    json_handler.setFormatter(jsonlogger.JsonFormatter())
    
    # Configure CloudWatch logging if enabled
    if os.getenv('AWS_CLOUDWATCH_ENABLED', 'false').lower() == 'true':
        cloudwatch_handler = watchtower.CloudWatchLogHandler(
            log_group=os.getenv('AWS_LOG_GROUP', 'salle-reservation-logs'),
            stream_name='reservation-service',
            region_name=os.getenv('AWS_REGION', 'eu-west-1')
        )
        app.logger.addHandler(cloudwatch_handler)
    
    app.logger.addHandler(json_handler)
    app.logger.setLevel(logging.INFO)

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:aziz123@reservation-db:5432/reservation-service')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Kafka configuration
    app.config['KAFKA_BOOTSTRAP_SERVERS'] = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
    
    # SonarQube webhook configuration
    app.config['SONARQUBE_WEBHOOK_SECRET'] = os.getenv('SONARQUBE_WEBHOOK_SECRET', 'your-webhook-secret')
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register routes and initialize Kafka
    from .routes import bp
    from .kafka_producer import init_kafka
    from .webhooks import webhook_bp
    
    app.register_blueprint(bp)
    app.register_blueprint(webhook_bp)
    init_kafka(app)
    
    with app.app_context():
        db.create_all()
    
    @app.before_request
    def before_request():
        request_id = request.headers.get('X-Request-ID')
        if request_id:
            g.request_id = request_id
        else:
            g.request_id = str(uuid.uuid4())

    @app.after_request
    def after_request(response):
        app.logger.info({
            'request_id': g.get('request_id'),
            'method': request.method,
            'path': request.path,
            'status': response.status_code,
            'duration': g.get('duration', 0)
        })
        return response
    
    @app.teardown_appcontext
    def cleanup(exception=None):
        scheduler = app.metrics_scheduler
        if scheduler:
            scheduler.stop()

    return app