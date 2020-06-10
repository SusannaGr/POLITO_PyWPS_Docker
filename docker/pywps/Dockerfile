FROM ubuntu:bionic
MAINTAINER Gis3W "info@gis3w.it"

ENV PYTHONUNBUFFERED 1
ENV DEBIAN_FRONTEND noninteractive
ENV LANG C.UTF-8

# FIX for W: GPG error: http://archive.ubuntu.com/ubuntu bionic InRelease: Couldn't create temporary file
RUN chmod 1777 /tmp

RUN apt-get update && apt-get install -y \
    python3.6 \
    python3.6-dev \
    python3-pip \
    libxslt-dev \
    python3-distutils \
    flex

# Install GRASS
RUN echo 'deb http://ppa.launchpad.net/ubuntugis/ubuntugis-unstable/ubuntu bionic main' >> /etc/apt/sources.list && \
    gpg --keyserver keyserver.ubuntu.com --recv 089EBE08314DF160 && \
    gpg --export --armor 089EBE08314DF160 |  apt-key add - && \
    apt-get update -qq && \
    apt-get install -y grass

# clone pywps code into /code folder
RUN apt install git -y && \
    git clone https://github.com/wlorenzetti/pywps-flask-grasso.git --single-branch --branch master /code

#COPY pywps_polito.py /code/wsgi/pywps.py
# run setup.py and install gunicorn and requirements
RUN cd /code && \
    python3 setup.py install && \
    pip3 install gunicorn && \
    pip3 install -r requirements-dev-renerfor.txt

