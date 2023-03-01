import datetime
import logging

from flask import current_app
from flask_security import Security, login_required, MongoEngineUserDatastore

from src.database.models.Role import Role
from src.database.models.User import User
from src.database.database import db

from src import docker_global_config


def has_user():
    return User.objects.count() != 0


def has_role():
    return Role.objects.count() != 0


def create_default_user_and_roles(user_datastore):
    if not has_role():
        user_datastore.create_role(name='admin',
                                   description='Administrative user of LuckyCat')
        user_datastore.create_role(name='analyst',
                                   description='General LuckyCat user without admin privileges')

    if not has_user():
        admin_role = Role.objects.get(name='admin')
        user_datastore.create_user(email=docker_global_config.default_user_email,
                                   password=docker_global_config.default_user_password,
                                   api_key=docker_global_config.default_user_api_key,
                                   registration_date=datetime.datetime.now(),
                                   roles=[admin_role])
        logging.info('Added default user on first request')


def _add_apikey_handler(security, user_datastore):
    @security.login_manager.request_loader
    def load_user_from_request(request):
        api_key = request.headers.get('Authorization')
        if api_key:
            if "Bearer" in api_key:
                api_key = api_key.split('Bearer ')[1]
            user = user_datastore.find_user(api_key=api_key)
            if user:
                return user

    return None


def add_flask_security(app):
    with app.app_context():
        app.config['SECURITY_UNAUTHORIZED_VIEW'] = '/'
        app.config['SECRET_KEY'] = current_app.config["secret_key"]
        app.config['SECURITY_PASSWORD_SALT'] = current_app.config["secret_key"]
        app.config['SECURITY_TOKEN_AUTHENTICATION_KEY'] = 'Authorization'

        user_datastore = MongoEngineUserDatastore(db, User, Role)
        security = Security(app, user_datastore)
        create_default_user_and_roles(user_datastore)
        _add_apikey_handler(security, user_datastore)
