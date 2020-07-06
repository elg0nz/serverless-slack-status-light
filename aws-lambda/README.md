# Lambda Functions

## Setup

1. Login to the AWS Console
2. Navigate to the [iot-dashboard] (https://console.aws.amazon.com/iot/home)
3. Create a new 'thing' (Manage > Things > Create). Make sure it matches the 
4. Copy the certificates created during creation into the chalicelib folder. Your folder should look as follows:
    (note: you might need to rename the files you downloaded to match the names above)
    ```
    chalicelib
    ├── AmazonRootCA1.pem
    ├── G2-RootCA1.pem
    ├── certificate.pem.crt
    └── private.pem.key

    ```

5. [Setup your Chalice env](https://aws.github.io/chalice/quickstart.html#quickstart)
6. [Setup your chalice creds](https://aws.github.io/chalice/quickstart.html#credentials)
7. Finally, [deploy your function](https://aws.github.io/chalice/quickstart.html#deploying)