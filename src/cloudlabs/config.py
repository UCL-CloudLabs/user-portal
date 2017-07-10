import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    DEVELOPMENT = False
    DEBUG = False
    TESTING = False
    CSRF_ENABLED = True
    SECRET_KEY = 'change-this'
    SSO_ATTRIBUTE_MAP = {
        'X-Shib-User-eppn': (True, 'eppn'),
        'X-Shib-User-display-name': (True, 'display-name'),
        'X-Shib-User-upi': (True, 'upi'),
        'X-Shib-User-mail': (True, 'email'),
    }
    SSO_LOGIN_URL = '/login'


class DevConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
