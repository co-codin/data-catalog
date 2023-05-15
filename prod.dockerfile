FROM repo.n3zdrav.ru:18444/python:3.8-alpine AS builder

WORKDIR /tmp
COPY requirements.txt .
RUN apk add --no-cache --virtual .build-deps \
        gcc \
        libc-dev \
        libffi-dev \
        openssl-dev \
        make \
    && pip3 install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

FROM repo.n3zdrav.ru:18444/python:3.8-alpine
COPY --from=builder /usr/local/lib/python3.8/site-packages /usr/local/lib/python3.8/site-packages
COPY app/ /app/app/
WORKDIR /app

CMD ["python3", "-m", "app"]
