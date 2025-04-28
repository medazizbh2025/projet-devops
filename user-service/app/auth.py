from flask_jwt_extended import JWTManager
from authlib.integrations.flask_client import OAuth
from datetime import timedelta
import os

jwt = JWTManager()
oauth = OAuth()

def init_auth(app):
    # Configuration JWT
    jwt.init_app(app)
    
    # Configuration OAuth Google
    oauth.init_app(app)
    oauth.register(
        name='google',
        client_id=app.config['GOOGLE_CLIENT_ID'],
        client_secret=app.config['GOOGLE_CLIENT_SECRET'],
        access_token_url='https://accounts.google.com/o/oauth2/token',
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        api_base_url='https://www.googleapis.com/oauth2/v1/',
        client_kwargs={'scope': 'email profile'},
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration'
    )