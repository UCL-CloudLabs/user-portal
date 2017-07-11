# User portal for CloudLabs

This Flask web application provides the main interface for researchers
seeking to deploy their apps on the cloud.

## Setting up the portal

This is a Python 3 project. The portal can be run locally for limited
development, but there is as yet no mocking of external services.

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
cd src
flask run
```

## Installation on Azure

This is documenting all the steps I'm performing on the staging machine to get a test instance running.
It will be automated later.

Add security rules allowing HTTPS and HTTP access, under 'Network interface' -> 'Network security group' -> 'Inbound security rules'

Install system packages:

```bash
sudo apt-get update
sudo apt-get upgrade
sudo apt-get install apache2 libapache2-mod-shib2 libapache2-mod-wsgi-py3
sudo apt-get install git python3-pip
```

Clone repo and set up virtual environment:

```bash
git clone git@github.com:UCL-CloudLabs/user-portal.git
sudo -H pip3 install virtualenv
cd user-portal
virtualenv venv
source venv/bin/activate
pip install -r requirements/base.txt
```

(TODO: investigate using ``python3 -m venv `pwd`/venv`` instead)

Quick & dirty test:

```bash
cd src
sudo apache2ctl stop
sudo FLASK_APP=autoapp.py /home/cloudlabs/user-portal/venv/bin/flask run --host=0.0.0.0 --port=80
```

Set up Apache:
* Place private key in `/etc/ssl/private/staging.cloudlabs.key`

```bash
git clone git@github.com:UCL-RITS/CloudLabs.git
sudo cp CloudLabs/secrets/staging_cloudlabs_rc_ucl_ac_uk.crt /etc/ssl/certs/
sudo cp CloudLabs/secrets/QuoVadisOVchain.pem /etc/ssl/certs/
sudo cp CloudLabs/conf_files/{000-default.conf,default-ssl.conf} /etc/apache2/sites-available/

sudo chmod 600 /etc/ssl/private/staging.cloudlabs.key
sudo chmod 644 /etc/ssl/certs/{*cloudlabs,QuoVadisOV}*
# Create a separate unprivileged user for the WSGI daemon to run as
sudo adduser --system --disabled-login --group cloudlabs-wsgi
sudo a2enmod wsgi shib2 ssl rewrite headers
sudo a2ensite default-ssl
sudo service apache2 restart
```

Set up Shibboleth:

```bash
sudo shib-keygen -e https://sp.staging.cloudlabs.rc.ucl.ac.uk/shibboleth -h staging.cloudlabs.rc.ucl.ac.uk -o /etc/shibboleth -y 10
sudo cp ~/CloudLabs/conf_files/{shibboleth2.xml,attribute-map.xml,idp-ucl-metadata.xml} /etc/shibboleth/
sudo /etc/init.d/shibd restart
```

Visit https://staging.cloudlabs.rc.ucl.ac.uk/Shibboleth.sso/Metadata to get the metadata file to send to is-webteam@ucl.ac.uk.


## Useful reference websites

* https://github.com/UCL-RITS/RSD-Dashboard/blob/development/docs/integrations/shibboleth.md
* Dashboard rc_puppet configuration:
    * https://github.com/UCL-RITS/rc_puppet/tree/master/modules/rsd_dashboard
    * https://github.com/UCL-RITS/rc_puppet/tree/master/modules/shibboleth_rhel
* Setting up Flask and mod_wsgi
    * http://flask.pocoo.org/docs/0.12/deploying/mod_wsgi/
    * http://modwsgi.readthedocs.io/en/develop/user-guides/virtual-environments.html
