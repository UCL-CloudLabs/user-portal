# User portal for CloudLabs

This Flask web application provides the main interface for researchers
seeking to deploy their apps on the cloud.

## Setting up the portal

This is a Python 3 project. The portal can be run locally for limited
development, but there is at yet no mocking of external services.

### Install requirements into virtualenv

```bash
pip install -r requirements/base.txt
```

or, for local dev setup:

```bash
pip install -r requirements/local.txt
```

### Configure environment

```bash
export FLASK_APP=autoapp.py
export FLASK_DEBUG=True
export APP_SETTINGS=cloudlabs.config.DevConfig
```

### Run the webapp

```bash
flask run
```

## Installation on Azure


```bash
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install libapache2-mod-shib2 libapache2-mod-wsgi-py3
```