FROM python:3.8-alpine

COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt
COPY app/ /app/app/
WORKDIR /app

CMD ["python3", "-m", "app"]
