FROM python:3.10-slim

ENV PYTHONUNBUFFERED=1

RUN mkdir -p /usr/src/app/
WORKDIR /usr/src/app/

COPY . /usr/src/app/

RUN  apt-get update \
     && apt-get install -y libc++-dev \
     && apt clean \
     && rm -rf /var/lib/apt/lists/*

ENV TZ=Europe/Moscow
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

RUN pip install --no-cache-dir -r requirements.txt
