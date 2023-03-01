FROM phusion/baseimage:0.10.0
MAINTAINER Thomas Barabosch <thomas.barabosch@fkie.fraunhofer.de>

# install dependencies 
RUN apt-get update -y && apt-get install -y gcc cmake make wget screen gdb htop mailutils \
automake build-essential git python3 python3-setuptools python3-yaml python3-dev python3-pip \
python3-pika

# install radamsa
WORKDIR /opt
RUN git clone https://gitlab.com/akihe/radamsa.git
WORKDIR /opt/radamsa
RUN make && make install

RUN pip3 install flask-mongoengine flask-security tabulate

# copy f3c source into container and install
WORKDIR /opt
RUN mkdir /opt/src && mkdir /opt/src/samples && mkdir /opt/src/results && mkdir /opt/src/results/crashes
COPY . /opt/luckycat/
COPY docker/backend/start_backend.sh /opt/luckycat/
ENV ENV=DOCKER
CMD ["/bin/bash", "/opt/luckycat/start_backend.sh"]
