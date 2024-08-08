
# Food Truck Mapr

Sample project to ingest publicly available food truck location data in San Francisco and present location info on google maps.

- very simplistic/"monolithic" lambda service that:
    - is scheduled to fire every hour
    - grabs the csv from public endpoint
    - records data in dynamodb
    - generates simple google maps plotting of active(?) food trucks
    - presents the map as simple html in s3 website enabled bucket

- all infra managed/created with pulumi/python

## NOTE:
Though this exercise calls for pulumi cloud, you should be well within the free tier for managed resources.


## Dependencies

- running docker environment to build images
- python 3.10+
- [pulumi account with api key/token](https://www.pulumi.com/docs/pulumi-cloud/accounts/)
- pulumi binary [(install and setup notes)](https://www.pulumi.com/docs/install/)
- AWS account with API credentials
- we assume either a linux environment, but easy to adapt to macOS
- [google maps API key](https://developers.google.com/maps/documentation/javascript/get-api-key#create-api-keys)

## Setup Instructions

1) `git clone REPO`
2) `cd REPO`
3) `export AWS_ACCESS_KEY_ID=<MY_REAL_KEY_ID_HERE>`
4) `export AWS_SECRET_ACCESS_KEY=<MY_REAL_SECRET_KEY_HERE>`
5) `export GOOGLE_MAPS_API_KEY=<MY_REAL_GOOGLE_MAPS_KEY_HERE>`
6) `pip install -r requirements.txt`
7) `pulumi login # this will prompt you for your pulumi api key`
8) `pulumi up -y`

#

If all goes well, you should see your s3 bucket url at the end of pulumi output:
```
Outputs:
    bucket_name   : "food-truck-mapr-of-excellence"
    bucket_website: "food-truck-mapr-of-excellence.s3-website-us-east-1.amazonaws.com"
```
The lambda service triggers every hour, but if you want to see the map right away, just log into the AWS console and trigger the lambda with any test event...content won't matter.

[Example Map](https://pasteboard.co/N21vPz4qN4eL.png)

## TODO:
- how do we handle stale data?
- separate data retrieval, storage, and mapping functionality
- better organize the infra-as-code
- need to be more restrictive with our lambda execution policy
- use secrets manager instead of loading in from env vars
- CI/CD the pulumi run
- add tests!!!
- observability: how well does our app perform throughout?


