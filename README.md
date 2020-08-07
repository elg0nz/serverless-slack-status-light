# Serverless IoT Slack Status Light

A light controlled by Slack to communicate your availability.
Powered by AWS IoT

![Demo gif](demo.gif)

More details available here: [Blog](Blog.md)

## Directory Structure:
* aws-lambda - AWS Lambda functions powered by Chalice
* firmware - Source code our ESP8266 Firmware powered by Mongoose OS

## Requirements:
* A AWS account
* A NodeMCU ESP8266 Microcontroller [Amazon*](https://amzn.to/2DHOSVU)
* A BlinkM LED [Amazon*](https://amzn.to/3e010OH)
* Prototyping Breadboard [Amazon*](https://amzn.to/3f186DX)
* Jumper Wires [Amazon*](https://amzn.to/2NWUttq)
* Mason Jar [Amazon*](https://amzn.to/2ZEoO5C)

*Affiliate Links

## Instructions:
1. Follow the Firmware setup in firmware/README.md 
2. Navigate to [AWS IoT dashboard](https://console.aws.amazon.com/iot/home) and head over to settings
3. Write down the Custom Endpoint
4. Modify aws-lambda/.chalice/config.json and change "CUSTOM_AWS_IOT_ENDPOINT" to the url you wrote down on the step before
5. Follow the Lambda setup in aws-lambda/README.md 
6. Execute `$ chalice url` and write down the URL displayed
7. Follow Slack setup instructions below


## Slack Setup
1. Navigate to [Slack API Apps](https://api.slack.com/apps)
2. Click on "Create New App"
3. Select your App Name & Workspace
4. Navigate to Features > Slash Commands
5. Create New Command 
6. Set command to "/set_status"
7. Update request URL to CHALICE_URL.amazonaws.com/api/slack_command where CHALICE_URL is the URL you stored on step 6 above
8. Set Usage hint to: "available | away | busy"
9. Save and test!

## MQTT commands & responses

### Set Color Request
topic: "/commands/write/blinker"
Sample request:
```
{"time": "2020-05-24T06:59:02+00:00", "red": 255, "green": 0, "blue": 0}
```
Parameters:
* time: Timestamp of the request in ISO8601 format with timezones.
* red: 0-255 value
* green: 0-255 value
* blue: 0-255 value
