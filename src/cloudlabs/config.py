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

    # Settings for Celery
    CELERY_BROKER_URL = 'amqp://guest@localhost'
    CELERY_TIMEZONE = 'Europe/London'
    CELERY_ENABLE_UTC = True

    # We need a result backend to track task status.
    # However we don't need to store results, since tasks write to the DB.
    CELERY_RESULT_BACKEND = 'rpc://'
    CELERY_TASK_IGNORE_RESULT = True

    # We don't make use of rate limiting, so turn it off for a performance boost
    CELERY_WORKER_DISABLE_RATE_LIMITS = True

    # We expect to have few tasks, but long running, so don't reserve more than you're working on
    # (this works well combined with the -Ofair option to the workers, which is now default)
    CELERY_WORKER_PREFETCH_MULTIPLIER = 1
    CELERY_TASK_ACKS_LATE = True
    # Since tasks are long-running, we want to know if they are actually running
    CELERY_TASK_TRACK_STARTED = True
    CELERY_TASK_SOFT_TIME_LIMIT = 60 * 30  # 30 minutes
    CELERY_TASK_TIME_LIMIT = 60 * 35  # Hard limit of 35 minutes

    # Just in case, restart workers once they've run this many jobs
    CELERY_WORKER_MAX_TASKS_PER_CHILD = 50

    # How many worker processes to run
    CELERY_WORKER_CONCURRENCY = 4


class DevConfig(Config):
    DEVELOPMENT = True
    DEBUG = True
    # Default to an insecure secret key for local development
    SECRET_KEY = os.environ.get('CLOUDLABS_SECRET_KEY', 'change-this!')
    # Default to travis config
    PRIVATE_SSH_KEY_PATH = os.environ.get(
        'PRIVATE_SSH_KEY_PATH',
        '~/build/UCL-CloudLabs/user-portal/src/test/id_rsa_travis_azure')

    # How many worker processes to run
    CELERY_WORKER_CONCURRENCY = 2
