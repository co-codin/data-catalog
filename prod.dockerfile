FROM python:3.8-alpine

COPY requirements.txt /tmp/
RUN pip install --upgrade pip setuptools wheel --no-cache-dir \
    && pip3 install --no-cache-dir -r /tmp/requirements.txt
COPY app/ /app/app/
WORKDIR /app

CMD ["python3", "-m", "app"]
