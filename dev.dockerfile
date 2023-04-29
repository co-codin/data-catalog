FROM repo.n3zdrav.ru:18444/python:3.8-alpine

WORKDIR /app
COPY requirements.dev.txt requirements.txt ./
RUN apk add --update build-base libffi-dev openssl-dev \
    && pip3 install --upgrade pip setuptools wheel --no-cache-dir \
    && pip3 install --no-cache-dir -r requirements.txt -r requirements.dev.txt \
    && rm -rf /var/cache/apk/*

CMD ["python", "-m", "app"]
