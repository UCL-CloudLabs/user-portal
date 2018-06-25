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
RUN unzip terraform.zip
COPY terraform /usr/local/bin/terraform
