# Container/Image name
FROM brunneis/python:3.7.0-ubuntu-18.04
LABEL maintainer="Michael Chou<snoopy02m@gmail.com>"

# Prepare packages
ARG PRODUCT_NAME="app"
ENV ENV="/root/.bashrc"
RUN mkdir -p /${PRODUCT_NAME}
WORKDIR /${PRODUCT_NAME}
COPY requirements.txt .
COPY src .

# Install requirement
RUN pip --no-cache-dir install -r requirements.txt

# Startup service
CMD ["supervisord", "-n"]

# Ailas
RUN echo 'alias start="python3 start_daemon.py"' >> /root/.bashrc

