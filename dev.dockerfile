#FROM python:3.8-alpine3.17
#ENV PYTHONUNBUFFERED 1
#RUN pip3 install --no-cache-dir -U pip
#
#COPY requirements.txt /tmp/
#COPY requirements.dev.txt /tmp/
#RUN pip3 install --compile --no-cache-dir -r /tmp/requirements.txt -r /tmp/requirements.dev.txt
#
#WORKDIR /app
#COPY ./app .
#CMD ["python", "-m", "app"]

FROM python:3.8-alpine
EXPOSE 8000
WORKDIR /app
COPY ./requirements.dev.txt .
COPY ./requirements.txt .
RUN apk add --update build-base libffi-dev openssl-dev \
    && pip install --upgrade pip setuptools wheel \
    && pip install -r requirements.txt -r requirements.dev.txt --no-cache-dir \
    && rm -rf /var/cache/apk/*
CMD ["python", "-m", "app"]