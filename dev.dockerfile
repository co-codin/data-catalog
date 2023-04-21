FROM python:3.8-alpine

WORKDIR /app
COPY requirements.txt /tmp/
COPY requirements.dev.txt /tmp/

RUN apk add --no-cache --update build-base libffi-dev openssl-dev
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt /tmp/requirements.dev.txt

CMD ["python3", "-m", "app"]