import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    DEVELOPMENT = False
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'change-this'
    SSO_ATTRIBUTE_MAP = {
        'eppn': (True, 'eppn'),
        'displayName': (True, 'name'),
        'employeeID': (True, 'upi'),
        'mail': (True, 'email'),
    }
    SSO_LOGIN_URL = '/login'
    SSO_LOGIN_ENDPOINT = 'login'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql:///cloudlabs')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PRIVATE_SSH_KEY_PATH = os.environ.get('PRIVATE_SSH_KEY_PATH', '~/.ssh/id_rsa_unencrypt')


class DevConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
