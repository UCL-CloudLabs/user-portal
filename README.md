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

Download the appropriate Terraform binary for your system following [Terraform's instructions](https://www.terraform.io/intro/getting-started/install.html) and put it in your virtualenv's `bin` folder so it can be run by the Flask app.

### Configure environment

```bash
export FLASK_APP=autoapp.py
export FLASK_DEBUG=True
export APP_SETTINGS=cloudlabs.config.DevConfig
export PRIVATE_SSH_KEY_PATH=<path/to/an/ssh/private/key>
```

You will also need the following environment variables set in order to deploy machines. Ask a team member for their secret values:
```bash
export TF_VAR_azure_tenant_id=
export TF_VAR_azure_client_id=
export TF_VAR_azure_client_secret=
export TF_VAR_azure_subscription_id=
```

### Create a database and run migrations

To set up the database and initial migration for the very first time in this repo:
```bash
flask db init
# Review migrations folder manually, add to version control
createdb --echo cloudlabs
flask db migrate
# Review migrations folder manually, add to version control
flask db upgrade
```

To create a fresh database on a new (development) system:
```bash
createdb --echo cloudlabs
```

To create new migrations if the models change:
```bash
flask db migrate
# Review migrations folder manually, add to version control
```

To apply any new migrations to prepare an existing database for use:
```bash
cd src
flask db upgrade
```

Note that once you have created a test user account / signed in with SSO for the first time, you will need to give you user the admin role explicitly using the Postgres command-line:
```bash
psql -d cloudlabs
> insert into user_roles (name, user_id) values ('admin', 1);
```
Replacing `1` with your user's id if necessary.

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

Copy `src/secrets.example.py` to `src/secrets.py` and fill in values.

Quick & dirty test:

```bash
cd src
sudo apache2ctl stop
sudo FLASK_APP=autoapp.py /home/cloudlabs/user-portal/venv/bin/flask run --host=0.0.0.0 --port=80
```

Install Terraform:
```bash
cd
curl -sSL -o terraform.zip "https://releases.hashicorp.com/terraform/0.10.2/terraform_0.10.2_linux_amd64.zip"
sudo apt-get install unzip
unzip terraform.zip
cp terraform venv/bin/
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

Set up database:

```bash
sudo apt-get install postgresql
sudo -u postgres createuser -DRS cloudlabs-wsgi
sudo -u postgres createdb -O cloudlabs-wsgi cloudlabs
```

Apply DB migrations:

```bash
export FLASK_APP=autoapp.py
export DATABASE_URL=postgresql:///cloudlabs
cd ~/user-portal/src
source ../venv/bin/activate
sudo -u cloudlabs-wsgi -E -- `which flask` db upgrade
```


## Useful reference websites

* https://github.com/UCL-RITS/RSD-Dashboard/blob/development/docs/integrations/shibboleth.md
* Dashboard rc_puppet configuration:
    * https://github.com/UCL-RITS/rc_puppet/tree/master/modules/rsd_dashboard
    * https://github.com/UCL-RITS/rc_puppet/tree/master/modules/shibboleth_rhel
* Setting up Flask and mod_wsgi
    * http://flask.pocoo.org/docs/0.12/deploying/mod_wsgi/
    * http://modwsgi.readthedocs.io/en/develop/user-guides/virtual-environments.html
* Flask & related extensions documentation
    * http://flask-sqlalchemy.pocoo.org/2.1/quickstart/
    * https://flask-migrate.readthedocs.io/en/latest/
    * http://docs.sqlalchemy.org/en/latest/orm/tutorial.html
