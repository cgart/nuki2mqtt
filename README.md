# Nuki to MQTT bridge

Very simple python based http to mqtt bridge used to control Nuki Smart Door Lock.
The idea for the bridge is inspired from https://github.com/petkov/http_to_mqtt/.
The bridge listens for `application/json` `POST` requests as send through Nuki's callback API to `/callback`. 
Received json string is published to the `nuki/<NUKIID>/update` topic.
Periodically the gateway will query nuki's bridge to request last cached state and will publish state of each nuki device
on `nuki/<NUKIID>/state`.

I implemented the bridge for my OpenHab installation after experiencing multiple issues with the official nuki addon. 
I could have tried to fix openhab addon, but my goal was to spend not more than 5 hours for a fix. Few hours to write this bridge and several minutes to setup MQTT Thing on OpenHab.

**Note**: This gateay is neither a beautiful python code, nor a super stable mqtt client. Everything is built from the off the shelf components to achieve the goal for my current setup.

## Usage

### Configuration

Configure content of `setup.py` with your mqtt broker ip address in `MQTT_BROKER` and port in `MQTT_PORT`.
Set `GATEWAY_IP` and `GATEWAY_PORT` (default = `*:5001`) to set ip address on which this gateway will run.
You need to get an auth token from the Nuki Bridge. Use `auth` endpoint to receive a token: https://developer.nuki.io/page/nuki-bridge-http-api-1-12/4/#heading--auth
Put received token into `NUKI_TOKEN` and set Nuki's bridge IP in `NUKI_HOST`.

### Docker image

To run the bridge within docker container, first create the docker image.

```bash
docker build -t nuki2mqtt .
docker run -d -p 5001:5001 nuki2mqtt
```

This will run the server on port 5001 as a daemon. 
**Note**: Ensure that used port matches the one the server listens to, see `Configuration`.

### Standalone

If you prefer standalone applications, without docker, you would need to install few dependencies first.
```bash
pip3 install flask paho-mqtt waitress requests
```

Afterwards you can start the server with:
```bash
python3 server.py
```

### Using with Nuki Doorbell

To use the bridge together with `Nuki Doorbell` and for example `OpenHab` I use the bridge to forward http callbacks to mqtt broker.
You need to setup Nuki's bridge to send callbacks to this gateway. You can do so with:
```bash
curl -G --data-urlencode --data-urlencode "token=<TOKEN>" --data-urlencode "url=http://<BRIDGE_IP>:5001/callback" http://<NUKI_IP>:8080/callback/add
``` 



