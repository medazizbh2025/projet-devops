from flask import Flask, request, g
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from prometheus_flask_exporter import PrometheusMetrics
from pythonjsonlogger import jsonlogger
import logging
import watchtower
import os
import uuid
from .tracing import init_tracer

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()

def create_app():
    app = Flask(__name__)
    
    # Initialize tracing
    tracer = init_tracer(app)
    
    # Configure metrics
    metrics = PrometheusMetrics(app)
    metrics.info('salle_service_info', 'Salle service info', version='1.0.0')

    # Configure JSON logging
    json_handler = logging.StreamHandler()
    json_handler.setFormatter(jsonlogger.JsonFormatter())
    
    # Configure CloudWatch logging if enabled
    if os.getenv('AWS_CLOUDWATCH_ENABLED', 'false').lower() == 'true':
        cloudwatch_handler = watchtower.CloudWatchLogHandler(
            log_group=os.getenv('AWS_LOG_GROUP', 'salle-reservation-logs'),
            stream_name='salle-service',
            region_name=os.getenv('AWS_REGION', 'eu-west-1')
        )
        app.logger.addHandler(cloudwatch_handler)
    
    app.logger.addHandler(json_handler)
    app.logger.setLevel(logging.INFO)

    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'postgresql://postgres:aziz123@salle-db:5432/salle-service')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    
    # Register routes
    from .routes import bp
    app.register_blueprint(bp)
    
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

    return app