# Container/Image name
FROM cbb23021/python3.7:1.0
LABEL maintainer="Michael Chou<snoopy02m@gmail.com>"

# Prepare packages
ARG PRODUCT_NAME="app"
ENV ENV="/root/.bashrc"
RUN mkdir -p /${PRODUCT_NAME}
RUN mkdir -p /etc/supervisor.d/
WORKDIR /${PRODUCT_NAME}
COPY requirements.txt .
COPY src .

RUN pip --no-cache-dir install -r requirements.txt

# Ailas
RUN echo 'alias start="python3 start_daemon.py"' >> /root/.bashrc

