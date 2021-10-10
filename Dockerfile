FROM python:3.8-slim-buster
WORKDIR /app
RUN pip3 install waitress flask paho-mqtt requests
COPY . .
CMD [ "python3", "server.py"]
 
