FROM ubuntu:xenial

# Install system packages
RUN apt-get update --yes && apt-get --yes upgrade
RUN apt-get --yes install apache2 libapache2-mod-shib2 libapache2-mod-wsgi-py3
RUN apt-get --yes install git python3-pip unzip curl

# Get the code and install dependencies
RUN git clone https://github.com/UCL-CloudLabs/user-portal.git
WORKDIR user-portal
RUN pip3 install -r requirements/base.txt

# TODO Change secrets.py!

# Install Terraform
WORKDIR /
RUN curl -sSL -o terraform.zip "https://releases.hashicorp.com/terraform/0.11.7/terraform_0.11.7_linux_amd64.zip"
RUN unzip terraform.zip -d /usr/local/bin/

# Assume we only want to set up the staging server for now
# Eventually we'd need to set ENV and the file name based on development
# TODO add the private key file!
COPY staging.cloudlabs.key /etc/ssl/private/staging.cloudlabs.key
ENV ENV staging

# Get the certificate etc files and configure them
# First, before building, a user with access to the repository needs to do:
# git clone git@github.com:UCL-RITS/CloudLabs.git
# and then we can copy the directory into the container
COPY CloudLabs CloudLabs
WORKDIR CloudLabs
RUN python make_conf_files.py
COPY secrets/cloudlabs_rc_ucl_ac_uk.crt /etc/ssl/certs/
COPY secrets/QuoVadisOVchain.pem /etc/ssl/certs/
COPY conf_files/{000-default.conf,default-ssl.conf} /etc/apache2/sites-available/

RUN chmod 600 /etc/ssl/private/staging.cloudlabs.key
RUN chmod 644 /etc/ssl/certs/{cloudlabs,QuoVadisOV}*
# Create a separate unprivileged user for the WSGI daemon to run as
RUN adduser --system --disabled-login --group cloudlabs-wsgi
RUN a2enmod wsgi shib2 ssl rewrite headers
RUN a2ensite default-ssl
RUN service apache2 restart
