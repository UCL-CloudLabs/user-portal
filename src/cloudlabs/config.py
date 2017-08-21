import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    DEVELOPMENT = False
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = os.environ.get('CLOUDLABS_SECRET_KEY')
    SSO_ATTRIBUTE_MAP = {
        'eppn': (True, 'eppn'),
        'displayName': (True, 'name'),
        'employeeID': (True, 'upi'),
        'mail': (True, 'email'),
    }
    SSO_LOGIN_URL = '/login'
    SSO_LOGIN_ENDPOINT = 'login'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL',
                                             'postgresql:///cloudlabs')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    # Require this to be set explicitly
    PRIVATE_SSH_KEY_PATH = os.environ.get('PRIVATE_SSH_KEY_PATH')


class DevConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    # Default to an insecure secret key for local development
    SECRET_KEY = os.environ.get('CLOUDLABS_SECRET_KEY', 'change-this!')
    # Default to travis config
    PRIVATE_SSH_KEY_PATH = os.environ.get(
        'PRIVATE_SSH_KEY_PATH',
        '~/build/UCL-CloudLabs/user-portal/src/test/id_rsa_travis_azure')
