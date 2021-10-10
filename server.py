#!/usr/bin/python3

from flask import Flask, request, jsonify
import requests
import paho.mqtt.client as mqtt 
import paho.mqtt.subscribe as subscribe
import json
import time
import re
from threading import Thread, Event

#--------------------------------------------
# Configuration
#--------------------------------------------

# --------
# MQTT
MQTT_BROKER = "192.168.1.250" 	# Address of the MQTT broker to publish/receive messages to/from
MQTT_PORT = 1883			# Port of the MQTT broker, typically 1883 for non secured communication

# --------
# Nuki Smart Lock
NUKI_TOKEN = "TOKEN"				# Token as visible on the nuki app
NUKI_HOST = "http://192.168.100.21:8080"	# IP address of the Nuki bridge

# --------
# This gateway
GATEWAY_IP = "0.0.0.0"			# IP address to bind this gateway to
GATEWAY_PORT = 5001			# Port to bind this gateway to


#--------------------------------------------
# Application
#--------------------------------------------
app = Flask(__name__)

#
# Periodic query of the nuki bridge to get current state.
# A state is then published on mqtt as a keep alive msg
#
class KeepAliveThread(Thread):
    def __init__(self, event):
        Thread.__init__(self)
        self.stopped = event

    def run(self):
        while not self.stopped.wait(30):
            r = requests.get(NUKI_HOST + "/list", params = {"token" : NUKI_TOKEN})
            nukis = r.json()           
            for nuki in nukis:
            	id = format(nuki["nukiId"], 'X')
            	mqttClient.publish("nuki/" + id + "/state", json.dumps(nuki))
            
#
# Receive callbacks from Nuki device at this endpoint
# HTTP -> MQTT
#
@app.route('/callback', methods=['POST'])    
def get_callback():
  
  if request.method == 'POST':
    nuki = request.json
    id = format(nuki["nukiId"], 'X')
    mqttClient.publish("nuki/" + id + "/update", json.dumps(nuki))
    print("nuki2mqtt: callback received for %s -> %s" % (id, nuki)) 
    
    return 'OK',200
    
  else:
    abort(400)

#
# Receive messages throuch mqtt and forward to Nuki
# MQTT -> HTTP
#
def on_mqtt_message(client, userdata, message):
    
    # extract nukiid and action
    pattern = re.compile("(nuki)/([0-9a-fA-F]+)/(\S+)")
    match = re.search(pattern, message.topic)
    
    if match and match.group(2):
        nukiid = match.group(2)
        
        # supported endpoints
        if match.group(3) == 'lockAction':
            r = requests.get(NUKI_HOST + "/lockAction", params = {"action" : message.payload, "nukiId" : nukiid, "token" : NUKI_TOKEN})
            print("nuki2mqtt: set lockAction for %s to %s -> %s" % (nukiid, str(message.payload, 'utf-8'), r.content)) 
	        
#
# Anything we don't support is an error response
#    
@app.errorhandler(404)
def page_not_found(e):
    return 'INVALID',400

#
# Entry point for the server
#    
if __name__ == '__main__':

    # connet to mqtt broker
    print("nuki2mqtt: connect to mqtt")
    mqttClient = mqtt.Client()
    mqttClient.connect(MQTT_BROKER, MQTT_PORT)
    mqttClient.subscribe("nuki/#")
    mqttClient.message_callback_add("nuki/+/+", on_mqtt_message)
    mqttClient.loop_start()
    
    # start thread for periodic keep alive messages
    print("nuki2mqtt: start periodic keepalive")
    stopFlag = Event()
    keepAliveThread = KeepAliveThread(stopFlag)
    keepAliveThread.start()

    # run gateway
    print("nuki2mqtt: start gateway")
    from waitress import serve
    serve(app, host = GATEWAY_IP, port = GATEWAY_PORT)
    
    print("nuki2mqtt: exit")
    mqttClient.loop_stop()
    stopFlag.set()
    
