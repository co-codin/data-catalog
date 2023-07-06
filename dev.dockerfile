FROM python:3.10-alpine

WORKDIR /app
COPY requirements.dev.txt requirements.txt ./
RUN apk add --update build-base libffi-dev openssl-dev libpq-dev \
    && pip3 install --upgrade pip setuptools wheel --no-cache-dir \
    && pip3 install --no-cache-dir -r requirements.dev.txt \
    && rm -rf /var/cache/apk/*

CMD ["python", "-m", "app"]
