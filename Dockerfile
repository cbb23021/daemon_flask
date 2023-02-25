# Container/Image name
FROM brunneis/python:3.7.0-ubuntu-18.04
LABEL maintainer="Michael Chou<snoopy02m@gmail.com>"

# Prepare packages
ARG PRODUCT_NAME="app"
ENV ENV="/root/.bashrc"
RUN mkdir -p /${PRODUCT_NAME}
RUN mkdir -p /etc/supervisor.d/
WORKDIR /${PRODUCT_NAME}
COPY requirements.txt .
COPY src .

RUN apt update
RUN apt install -y gcc

# Install requirement
RUN pip install --upgrade pip
RUN pip --no-cache-dir install -r requirements.txt

# Ailas
RUN echo 'alias start="python3 start_daemon.py"' >> /root/.bashrc

