FROM ubuntu:xenial

# Install system packages
RUN apt-get update --yes && apt-get --yes upgrade
RUN apt-get --yes install apache2 libapache2-mod-shib2 libapache2-mod-wsgi-py3
RUN apt-get --yes install git python3-pip unzip curl postgresql

# Get the code and install dependencies
RUN git clone https://github.com/UCL-CloudLabs/user-portal.git
WORKDIR user-portal
RUN pip3 install -r requirements/base.txt

# TODO Change secrets.py!

# Install Terraform
WORKDIR /
RUN curl -sSL -o terraform.zip "https://releases.hashicorp.com/terraform/0.11.7/terraform_0.11.7_linux_amd64.zip"
RUN unzip terraform.zip -d /usr/local/bin/

# Get the certificate etc files and configure them
# First, before building, a user with access to the repository needs to do:
# git clone git@github.com:UCL-RITS/CloudLabs.git
# and then we can copy the directory into the container
COPY CloudLabs CloudLabs
WORKDIR CloudLabs
# Assume we only want to set up the staging server for now
# Eventually we'd need to set ENV and the file name based on development
ENV ENV staging
RUN python3 make_conf_files.py
RUN cp secrets/staging.cloudlabs.key /etc/ssl/private/staging.cloudlabs.key
RUN cp secrets/cloudlabs_rc_ucl_ac_uk.crt /etc/ssl/certs/
RUN cp secrets/QuoVadisOVchain.pem /etc/ssl/certs/
RUN cp conf_files/000-default.conf conf_files/default-ssl.conf  /etc/apache2/sites-available/

RUN chmod 600 /etc/ssl/private/staging.cloudlabs.key
RUN chmod 644 /etc/ssl/certs/cloudlabs* /etc/ssl/certs/QuoVadisOV*
# Create a separate unprivileged user for the WSGI daemon to run as
RUN adduser --system --disabled-login --group cloudlabs-wsgi
RUN a2enmod wsgi shib2 ssl rewrite headers
RUN a2ensite default-ssl
# RUN service apache2 restart

# Configure CloudLabs's Flask app
WORKDIR /
RUN cp CloudLabs/secrets/secrets.py user-portal/src/cloudlabs/
WORKDIR /user-portal/src
ENV FLASK_APP autoapp.py
ENV FLASK_DEBUG True
ENV APP_SETTINGS cloudlabs.config.DevConfig
# These two are needed by flask db upgrade
ENV LC_ALL C.UTF-8
ENV LANG C.UTF-8

# Configure CloudLabs' portal DB
USER postgres
RUN /etc/init.d/postgresql start &&\
    psql --command "CREATE USER root WITH SUPERUSER PASSWORD 'docker';" &&\
    createdb --echo cloudlabs &&\
    flask db upgrade
USER root

EXPOSE 5000

ENV RABBITMQ_NODE_IP_ADDRESS 127.0.0.1

RUN /etc/init.d/postgresql start && \
    psql -d cloudlabs -c "insert into user_roles (name, user_id) values ('admin', 1);"

CMD /etc/init.d/postgresql start && \
    rabbitmq-server -detached && \
    (celery beat -A cloudlabs.tasks.worker.celery --loglevel=info &) && \
    (celery worker -A cloudlabs.tasks.worker.celery --loglevel=info --statedb=worker_state &)
