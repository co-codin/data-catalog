FROM python:3.10-alpine AS builder

WORKDIR /tmp
COPY requirements.txt .
RUN apk add --no-cache --virtual .build-deps \
        gcc \
        libc-dev \
        libpq-dev \
        libffi-dev \
        openssl-dev \
        make \
    && pip3 install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

FROM python:3.10-alpine
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY app/ /app/app/
WORKDIR /app

CMD ["python3", "-m", "app"]
