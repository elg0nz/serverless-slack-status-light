# Serverless Slack Status Light

Type `/set_status busy` in Slack and the jar on your desk turns red.

Nothing runs in between: a Lambda function built with Chalice publishes to AWS IoT Core's managed MQTT broker, and a $5 ESP8266 running Mongoose OS changes the LED. No hub, no self-hosted Mosquitto, no Raspberry Pi you find unplugged three weeks later.

![Demo gif](demo.gif)

This repo doubles as a small study in where Lambda architecture makes sense for IoT, and where it leaks. The full build log, including the architecture decisions and the mistakes, is in [Blog.md](Blog.md).

## Why serverless fits here

A status light is close to the ideal serverless workload: rare, human-triggered events, payloads under 100 bytes, and no state between them. Running an always-on broker and a server to move that little data is the wrong shape. A function that wakes per slash command, plus an MQTT broker AWS hosts for you, matches the traffic exactly. The jar ran on my desk for months off a USB battery with nothing to patch, reboot, or SSH into.

## Where the abstraction leaked

Three lessons, all still visible in the code:

* **Lambda can die before MQTT delivers.** Publishing a message takes 20-200ms; returning the HTTP response takes less. Return too early and the sandbox freezes with the message still in flight. The fix is an unglamorous `time.sleep(0.2)` before responding ([app.py](aws-lambda/app.py)).
* **MQTT client IDs must be unique, and concurrent Lambdas are natural twins.** AWS IoT fails duplicate-ID connections in non-obvious ways, so each container generates a fresh `uuid4` client ID at init.
* **The other end has about 80KB of RAM.** The firmware parses JSON into a 300-byte buffer ([main.c](firmware/src/main.c)), so the payload carries exactly four fields and nothing speculative.

If you want a status light without a soldering iron, buy one. This build is for seeing how the pieces fit.

## How it works

```
                                     XXXXXXXXX
+----------+    +----------+        XX       XX      +----------+    +----------+
| RGB LED  |    | MCU      |        X  AWS    X      | AWS      |    | Slack    |
| (BlinkM) +<---+(ESP8266) +<------ X  IoT    X<-----+ Lambda   +<---+ Command  |
|          |    |          |  MQTT  XX       XX      |          |    |          |
+----------+    +----------+         XXXXXXXXX       +----------+    +----------+
```

1. You run `/set_status available | away | busy` in Slack.
2. Slack POSTs the command to a Chalice-managed Lambda endpoint.
3. The Lambda maps the status to an RGB value and publishes it at QoS 1 to the `/commands/write/blinker` topic on AWS IoT Core.
4. The ESP8266, subscribed over TLS, acks the message and sets the BlinkM color over I2C.

## Repo layout

* `aws-lambda/`: the Chalice app. Slack slash-command endpoint, MQTT publisher, plus a `PUT /commands/write/blinker` HTTP route for testing colors without Slack.
* `firmware/`: Mongoose OS firmware in C, with configs for both ESP8266 and ESP32.

## Parts

* NodeMCU ESP8266 microcontroller [Amazon*](https://amzn.to/2DHOSVU)
* BlinkM I2C RGB LED [Amazon*](https://amzn.to/3e010OH)
* Prototyping breadboard [Amazon*](https://amzn.to/3f186DX)
* Jumper wires [Amazon*](https://amzn.to/2NWUttq)
* Mason jar, as the diffuser [Amazon*](https://amzn.to/2ZEoO5C)

\*Affiliate links

You will also need an AWS account and a Slack workspace where you can install apps.

## Build it

1. Flash the firmware: follow [firmware/README.md](firmware/README.md).
2. In the [AWS IoT console](https://console.aws.amazon.com/iot/home), open Settings and copy your custom endpoint.
3. In `aws-lambda/.chalice/config.json`, replace `CUSTOM_AWS_IOT_ENDPOINT` with that endpoint.
4. Deploy the Lambda: follow [aws-lambda/README.md](aws-lambda/README.md).
5. From `aws-lambda/`, run `chalice url` and keep the URL it prints.

### Slack setup

1. Create a new app at [api.slack.com/apps](https://api.slack.com/apps) and pick your workspace.
2. Under Features > Slash Commands, create a new command:
   * Command: `/set_status`
   * Request URL: the Chalice URL from step 5 above, plus `slack_command` (for example `https://<id>.execute-api.<region>.amazonaws.com/api/slack_command`)
   * Usage hint: `available | away | busy`
3. Save, then run `/set_status busy` and watch the jar turn red.

## MQTT API

**Topic:** `/commands/write/blinker`

Sample request:

```json
{"time": "2020-05-24T06:59:02+00:00", "red": 255, "green": 0, "blue": 0}
```

Parameters:

* `time`: request timestamp, ISO 8601 with timezone
* `red`, `green`, `blue`: 0-255

Keep the payload under 300 bytes; that is all the parser on the MCU has to work with.
