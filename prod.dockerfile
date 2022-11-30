FROM python:3.8-alpine
ARG SERVICE_PORT=8000

COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt
COPY app/ /app/app/
WORKDIR /app

EXPOSE $SERVICE_PORT
CMD ["python3", "-m", "app"]
