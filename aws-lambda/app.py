from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder
from chalice import Chalice
from chalice import Rate
from urllib import parse
import json
import sys
import ssl
import uuid
import time
import logging
import datetime
import json
import os
import random

app = Chalice(app_name="blinker")


def on_connection_interrupted(connection, error, **kwargs):
    app.log.info("Connection interrupted. error: {}".format(error))


def on_connection_resumed(connection, return_code, session_present, **kwargs):
    app.log.info(
        "Connection resumed. return_code: {} session_present: {}".format(
            return_code, session_present
        )
    )

    if return_code == mqtt.ConnectReturnCode.ACCEPTED and not session_present:
        app.log.info("Session did not persist. Resubscribing to existing topics...")
        resubscribe_future, _ = connection.resubscribe_existing_topics()
        resubscribe_future.add_done_callback(on_resubscribe_complete)


def on_resubscribe_complete(resubscribe_future):
    resubscribe_results = resubscribe_future.result()
    app.log.info("Resubscribe results: {}".format(resubscribe_results))

    for topic, qos in resubscribe_results["topics"]:
        if qos is None:
            sys.exit("Server rejected resubscribe to topic: {}".format(topic))


def get_paths():
    certPath = os.path.realpath("./chalicelib")
    ca = "{}/AmazonRootCA1.pem".format(certPath)
    cert = "{}/certificate.pem.crt".format(certPath)
    private = "{}/private.pem.key".format(certPath)
    return {"ca": ca, "cert": cert, "private": private}


def create_ssl_context():
    paths = get_paths()
    IoT_protocol_name = "x-amzn-mqtt-ca"
    ssl_context = ssl.create_default_context()
    ssl_context.set_alpn_protocols([IoT_protocol_name])
    ssl_context.load_verify_locations(cafile=paths["ca"])
    ssl_context.load_cert_chain(certfile=paths["cert"], keyfile=paths["private"])

    return ssl_context


def on_publish(client, userdata, mid):
    app.log.debug(json.dumps({"on_publish": {"userdata": userdata, "mid": mid}}))


ssl.PROTOCOL_TLS
AWS_IOT_ENDPOINT = ENV["AWS_IOT_ENDPOINT"]
blinker_topic = "/commands/write/blinker"
event_loop_group = io.EventLoopGroup(1)
host_resolver = io.DefaultHostResolver(event_loop_group)
client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)
client_id = str(uuid.uuid4())

paths = get_paths()
mqtt_connection = mqtt_connection_builder.mtls_from_path(
    endpoint=AWS_IOT_ENDPOINT,
    cert_filepath=paths["cert"],
    pri_key_filepath=paths["private"],
    client_bootstrap=client_bootstrap,
    ca_filepath=paths["ca"],
    on_connection_interrupted=on_connection_interrupted,
    on_connection_resumed=on_connection_resumed,
    client_id=client_id,
    clean_session=False,
    keep_alive_secs=6,
)
connect_future = mqtt_connection.connect()
connect_future.result()


def publish_mqtt_msg(topic, msg):
    mqtt_connection.publish(topic=topic, payload=msg, qos=mqtt.QoS.AT_LEAST_ONCE)
    time.sleep(0.2)
    app.log.info("topic: {}, payload: {}".format(topic, msg))
    return msg


def now_in_utc():
    return (
        datetime.datetime.now(tz=datetime.timezone.utc)
        .replace(microsecond=0)
        .isoformat()
    )

def set_color(red=0, green=0, blue=0):
    payload = {"time": now_in_utc(), "red": red, "green": green, "blue": blue}
    msg = json.dumps(payload)
    return publish_mqtt_msg(blinker_topic, msg)


@app.route("/slack_event", methods=["POST"])
def slack_event():
    payload = app.current_request.json_body

    if "challenge" in payload.keys():
        challenge = payload["challenge"]
        return json.dumps({"challenge": challenge})

GREEN = {"text": "available", "red": 0, "green": 255, "blue": 0}
YELLOW = {"text": "away", "red": 255, "green": 255, "blue": 0}
RED = {"text": "busy", "red": 255, "green": 0, "blue": 0}
STATUS_OPTIONS = {
    "b'available'": GREEN,
    "b'away'": YELLOW,
    "b'busy'": RED,
}

def _handle_set_status(text):
    if not (text in STATUS_OPTIONS.keys()) :
        return json.dumps(
            {
                "response_type": "in_channel",
                "text": f"Invalid status option. Please choose between available, away or busy",
            }
        )

    current_status = STATUS_OPTIONS[text]
    status = current_status["text"]
    red = current_status["red"]
    green = current_status["green"]
    blue = current_status["blue"]
    set_color(red, green, blue)

    return json.dumps(
        {"response_type": "in_channel", "text": f"Status updated to {status}"}
    )

def _build_dict(raw_body):
    data = parse.parse_qsl(raw_body)
    data_dict = dict()
    for pair in data:
        data_dict[str(pair[0])] = str(pair[1])
    return data_dict

@app.route(
    "/slack_command",
    methods=["POST"],
    content_types=["application/x-www-form-urlencoded"],
)
def slack_command():
    raw_body = app.current_request.raw_body
    data_dict = _build_dict(raw_body)

    command = data_dict["b'command'"]

    SET_STATUS_COMMAND = "b'/set_status'"
    if command == SET_STATUS_COMMAND:
        return _handle_set_status(data_dict["b'text'"])

    return json.dumps({"response_type": "in_channel", "text": "Unsupported command."})


@app.route("/commands/write/blinker", methods=["PUT"])
def set_color_request():
    request = app.current_request
    red = request.json_body["red"]
    green = request.json_body["green"]
    blue = request.json_body["blue"]
    return set_color(red, green, blue)
