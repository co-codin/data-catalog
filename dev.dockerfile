FROM python:3.8-alpine
EXPOSE 8000
WORKDIR /app
COPY requirements.dev.txt requirements.txt ./
RUN apk add --update build-base libffi-dev openssl-dev \
    && pip install --upgrade pip setuptools wheel --no-cache-dir \
    && pip install --no-cache-dir -r requirements.txt -r requirements.dev.txt \
    && rm -rf /var/cache/apk/*

CMD ["python", "-m", "app"]
