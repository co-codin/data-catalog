FROM python:3.10-alpine AS builder

WORKDIR /tmp
COPY requirements.txt .
RUN apk update \
    && apk add --no-cache --virtual .build-deps postgresql-dev gcc python3-dev musl-dev \
    && pip3 install --no-cache-dir -r requirements.txt \
    && apk del .build-deps

FROM python:3.10-alpine
RUN apk add libpq
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY app/ /app/app/
WORKDIR /app

CMD ["python3", "-m", "app"]
