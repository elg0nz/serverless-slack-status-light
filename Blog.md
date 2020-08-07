# My Availability jar: How I built a Slack controlled lamp to minimize accidental Zoom guests

![bbc gif](https://media.giphy.com/media/3oKIPoAP1wLvewc7QI/giphy.gif)

By now, if you have a home office, this must have happened to you: your partner/roommate/children must have crashed right in the middle of delivering that important presentation...
This has happened to me, and after the second or third time, I decided to do something about it. This is what I built.

## Introducing the Status Jar

![demo](demo.gif)

My solution to this "are you on a call?" problem is this multi-color Jar controlled by Slack.
Green indicates Available, Yellow Away and, Red Busy.

Since I spend most of my working hours on Slack, using slack commands to control the Jar turned out to be the most logical interface.

These are the Slack commands my Jar responds to:
```
/set_availability available
/set_availability away
/set_availability busy
```

The goal with this article is not just to document how this device was built, but to: a. draw the parallels between Developing Web APIs and building Embedded Systems, b. prove you can do IoT with a Serverless infrastructure.

## How I built this
The process to tackle a project like this is as follows:
1. Gather requirements
2. Choose Hardware
3. Plan Software architecture
4. Pick Framework and build app
5. Deploy

### 1. Gathering Requirements
Creativity loves constraints, so I usually start my projects by creating a list of requirements:
1. To minimize the lamp becoming a distraction, the lamp should get online in less than a minute
2. To minimize maintenance, the lamp should be able to run without being hooked up to a computer or server (serverless FTW)
3. To prevent security risks, the lamp should be able to operate without opening any ports on my network

These requirements gave me lots of guidance of how to approach this project and to understand its moving parts:
1. A Micro-controller (MCU) & Electronics to control the LED
2. A WiFi Module
3. A way to interact with Slack

### 2. Choose Hardware
Given these requirements I decided to go with an ESP8266 NodeMCU, an inexpensive MCU available on [Amazon](https://amzn.to/2DHOSVU)(affiliate link) for less than $5.

This device has everything needed for a project like this, 16 GPIO pins, I2C communication, and, a built-in WiFi module.
The last piece needed for my project (hardware wise), was a RGB LED, looking at my parts drawer I stumbled upon a BlinkM module,
a nice RGB led that can be controlled using only two wires via [I2C](https://en.wikipedia.org/wiki/I%C2%B2C).

Here's how the wired up circuit looks like:

![circuit](firmware/circuit.png)

Moving up to software, let's go over this project's diagram

### 3. Plan Software architecture

```
                                     XXXXXXXXX
+----------+    +----------+        XX       XX      +----------+    +----------+
| RGB LED  |    | MCU      |        X  AWS    X      | AWS      |    | Slack    |
| (BlinkM) +<---+(ESP8266) +<------ X  IoT    X<-----+ Lambda   +<---+ Command  |
|          |    |          |  MQTT  XX       XX      |          |    |          |
+----------+    +----------+         XXXXXXXXX       +----------+    +----------+
```
(ASCII version of this project's Napkin diagram)

Instead of running a server to talk with our device, I used [AWS Lambda Functions](https://aws.amazon.com/lambda/) to send commands from Slack to the lamp.

As the diagram shows, the communication flow is as follows:
* A command is sent via Slack
* AWS Lambda receives that command and sends it over to our MCU
* The MCU receives the command via MQTT
* The MCU changes the LED color based on the command params

#### This project secret sauce: AWS IoT Core
The [MQTT](https://en.wikipedia.org/wiki/MQTT) protocol is the backbone of most [IoT](https://en.wikipedia.org/wiki/Internet_of_things) devices. If you ever wondered what the "Hub" on your Home IoT does, its mostly this; most hubs act as a MQTT server (i.e. broker) and a gateway to connect to the manufacturer's cloud.

Because of this, for most projects of this kind, the first step would be to run your own MQTT broker like [Mosquitto](https://mosquitto.org/) on a local or cloud server, but as I mentioned before, early on I made the decision of wanting to go serverless. 

Lucky for me, [AWS IoT Core](https://aws.amazon.com/iot-core/getting-started/?nc=sn&loc=5) provides a fully managed MQTT broker for developers to use, which eliminates the need of hosting a MQTT server yourself.
While there are plenty of alternative brokers, I chose AWS IoT because it is dead simple to get up and running.

### 4. Pick Frameworks and build
The criteria to pick up a framework are very similar regardless of it being used for Embedded Systems or an API.

A great framework:
1. Is easy to setup, easy to learn
2. Provides a base structure to your App 
3. Makes it easy to change configurations without having to modify your code
4. Gives you easy access to logs and operating metrics
5. Makes it easy to build/deploy your App

(You might notice some parallels with the criteria presented on the [12factor.net](https://12factor.net/) methodology, its is no coincidence)

### Picking Chalice as a Framework for AWS Lambda
While Lambda Functions are usually small enough that for most cases a Framework would be overkill, I wanted to build these functions in a way that I could easily extend the code to support new commands.

[AWS Chalice](https://aws.github.io/chalice/) was the natural choice for this, not only because it's written by the AWS team, but also because how it adheres to the criteria I presented before:
1. You can get setup in minutes. Basically you just need to do `pip install chalice` and `chalice deploy` to get a lambda function live
2. Routing is the foundation of any Web framework, and [Chalice Routing](https://aws.github.io/chalice/topics/routing.html) is simple and straightforward. A decorator is all you need to get a function linked to an URL.
3. Chalice provides [Stage and Lambda](https://aws.github.io/chalice/topics/configfile.html#) specific configurations, for us this means that we can easily create Development, Staging and Production configurations without having to touch our app code
4. Remote logs are only a command away. `chalice logs` gives you access to these logs on the terminal, but you can also just as easily access them over [CloudWatch](https://docs.aws.amazon.com/AmazonCloudWatch/latest/logs/WhatIsCloudWatchLogs.html)


### Picking MongooseOS as a Framework for our Embedded System

One of the best things about ESP8266 MCUs is that they can be programmed in a myriad of ways.
* Lua using [NodeMCU firmware](https://www.nodemcu.com/)
* Javascript using [Espurino](https://www.espruino.com/)
* C using [Arduino](https://www.arduino.cc/)
* C using [Mongoose OS](https://mongoose-os.com)

In the end, I chose Mongoose OS because its features really lined up with the criteria I outlined above:
1. It takes about [12 Minutes to setup](https://mongoose-os.com/docs/mongoose-os/quickstart/setup.md) and its [RPC System](https://mongoose-os.com/docs/mongoose-os/userguide/rpc.md) is powerful and easy to understand
2. The [Mongoose API](https://mongoose-os.com/docs/mongoose-os/api/core/mgos_app.h.md) is elegantly abstracts your MCU into Apps, Events and Systems. These abstractions provide a base structure for you to reason about your app
3. [Configuration on Mongoose OS](https://mongoose-os.com/docs/mongoose-os/userguide/configuration.md) allows you to use YAML to create multiple configurations without having to change your code at all
4. Running a `mos console` command is all it takes to access the device logs
5. Running a `mos build` command is all it takes to compile, link and get your code ready to flash

Also, Mongoose OS has a [great integration with AWS IoT](https://mongoose-os.com/docs/mongoose-os/api/cloud/aws.md) which proved to be pretty handy for this project

### Building, and Deploying the app

I won't go into the nitty-gritty details on how to build this project because I wrote detailed instructions on this project's
[Github repo](https://github.com/elg0nz/serverless-slack-status-light). But just for completeness, here is a small overview of the steps that were required:

1. Create an AWS account & Slack
2. Design MQTT/HTTP/Slack commands & payloads
3. Wire up the circuit and Write, Build & Flash the Embedded Firmware
4. Write and Deploy Chalice Lambda Functions

### Lessons Learned
#### Designing MQTT/HTTP/Slack Commands beforehand is a timesaver
During the early stages of this project, I kept running into issues where the embedded code was not responding correctly to the commands that were sent from Slack. The issue turned out to be some mismatches between the payload being sent and its parsing.
At this point I went back and wrote down how these commands should look like and what they should do, this investment quickly payed off by allowing me to see issues with the payloads before finishing implementing them.

#### Not all Python MQTT clients are created the same
Though MQTT is a ubiquitous protocol, clients can behave in different ways. Some of those ways might not be correctly
interpreted by your MQTT broker or other clients. Be sure to test this extensively.

For example, AWS IoT requires client IDs to be unique in order to allow MQTT connections to be established, some clients unfortunately opaquely set this value to a default which will cause connections to fail in an non-obvious way.

#### Lambdas can be terminated before messages have been fully published
In a nutshell AWS Lambdas are terminated when the HTTP request is over. In an ideal environment, this would be enough time for sending an MQTT message out. However during testing I noticed that this is seldomly the case. Sending an MQTT message can take somewhere between 20-200ms. In order to guarantee delivery I had to hardcode a 200ms wait on the endpoints before returning an HTTP response. This gave the Lambda's MQTT client enough time to fully send this message before going away.

#### Parsing JSON messages on embedded devices is an expensive operation
When working with Web applications we are used to sending relatively large and expensive JSON payloads, which is fine for servers with copious amounts of RAM and CPUs, but in Embedded devices, we have little room to play with. On a MCU where we have barely around 80 KB available, we need to be mindful about these sizes. In my implementation 300 characters was as much as I had available to work with, which meant having to make some important decisions on what should be sent down the line and what we could implicitly calculate without it being part of the payload.

#### Doing integration early is still key to getting things done
This system has many moving pieces, and a small misalignment in any of these pieces would prevent the system from working correctly.
Testing the system at multiple stages was key to making sure things were working as designed. In any system differences between running locally and remotely require fine adjustments. In this project where we have multiple third party dependencies (AWS IoT Core and Slack), these adjustments are not only expected, but something our software had to compensate for.

# Results and Next steps
I'm happy to say that this Jar has been running for the last few months and it has reduced the number of "Zoom guest appearances" to almost zero. One of my favorite things about this Jar is that you just need to plug it in to a USB battery and it's ready to go. No software to run, no servers to reboot "every once in a while".

This project began as a way to ensure a Temperature logging system I've been working on was working correctly (a lengthier project that deserves its own post) and it quickly turned out to be a tool that is now an important part of my daily routine.
And as it turns out, this "test rig" is still being used months after the original project was finished.

Keep shining bright like a diamond desk buddy.

![demo](demo.gif)