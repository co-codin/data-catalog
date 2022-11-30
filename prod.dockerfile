FROM python:3.8-alpine
ARG SERVICE_PORT=8000
COPY requirements.txt /tmp/
RUN pip3 install -r /tmp/requirements.txt
RUN mkdir -p /var/logs/
RUN mkdir /data_catalog
WORKDIR /data_catalog
RUN mkdir logs
COPY app/ ./app/
EXPOSE $SERVICE_PORT
CMD ["uvicorn", "app.main:app" , "--host", "0.0.0.0", "--port", "8000"]
#CMD ["python3","-m","app.main.py"]