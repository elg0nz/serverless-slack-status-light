# Slack Status Light Firmware

## Wiring
![circuit](./circuit.png)

| NodeMCU | BlinkM MaxM |
|---------|-------------|
| 3V      | +           |
| GND     | -           |
| D5      | C           |
| D6      | D           |

## Build Instructions

### Build firmware
`$ mos build --platform esp8266`
### Flash firmware
`$ mos flash`
### Retrieve and Set Credentials for AWS IoT
`$ AWS_PROFILE=aws-iot mos aws-iot-setup --aws-region us-east-1 --aws-iot-policy mos-default`
### Set device name
`$ mos config-set app.dname=blinker`
### Set Wi-Fi
`$ mos wifi SSID PASSWORD`

### (Optional) Enable debug console
`$ mos console`