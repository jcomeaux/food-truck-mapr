#!/usr/bin/env python3

"""
Grabs food truck location data from https://data.sfgov.org/api/views/rqzj-sfat/

Creates a google map with pins overlayed.

Assuming region is us-east-1, map will be available at:
http://<bucket-name>.s3-website-us-east-1.amazonaws.com

The data is actually for permits and some of them expire, so probably filter out EXPIRED permits
- there are also some pending ("REQUESTED") permits that haven't been granted yet...filter these out too
- there's also a "SUSPEND" status...my guess is we don't want to track these either
- we're only interested in locations with APPROVED status

Not all of the locations have physically street addresses, but all have a "Location" column with latitude and longitude.

references:
reading in csv content: https://stackoverflow.com/questions/35371043/use-python-requests-to-download-csv/35371451
boto3/dynamodb docs: https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/dynamodb.html
dynamodb queries: https://dynobase.dev/dynamodb-python-with-boto3/#scan

Getting Google Maps API key:
https://developers.google.com/maps/documentation/javascript/get-api-key#create-api-keys

"""

import csv
import os
import time
import boto3
from boto3.dynamodb.conditions import Key, Attr
import gmplot
import requests



CSV_URL = 'https://data.sfgov.org/api/views/rqzj-sfat/rows.csv'
S3_BUCKET = os.environ['S3_BUCKET']
DYNAMODB_TABLE_NAME = os.environ['DYNAMODB_TABLE_NAME']
GOOGLE_MAPS_API_KEY = os.environ['GOOGLE_MAPS_API_KEY']

def get_foodtruck_data(url):
    """
    retrieves & returns csv data as list of dicts
    TODO: check ETag to determine if updating is necessary
    """
    try:
        with requests.Session() as s:
            download = s.get(CSV_URL)
            decoded_content = download.content.decode('utf-8')
            cr = csv.DictReader(decoded_content.splitlines(), delimiter=',')
            data = []
            for row in cr:
                data.append(row)
            return(data)
    except Exception as e:
        print(f"error retrieving csv data from {url}: {e}")
        exit(1)


def write_data_to_dynamodb(data):
    client = boto3.client('dynamodb', region_name='us-east-1')
    for item in data:
        epoch_time = str(int(time.time())) # handling some weirdness with how boto handles types for dynamodb
        try:
            client.put_item(
                TableName=DYNAMODB_TABLE_NAME, # hardcoding for now
                Item={
                    'locationid':       {'N': item.get('locationid')},
                    'applicant':        {'S': item.get('Applicant')},
                    'facility_type':    {'S': item.get('FacilityType')},
                    'food_items':       {'S': item.get('FoodItems')},
                    'latitude':         {'N': item.get('Latitude')},
                    'longitude':        {'N': item.get('Longitude')},
                    'status':           {'S': item.get('Status')},
                    'epoch_timestamp':  {'N': epoch_time}, # adding in timestamp to test for stale data?
                }
            )
        except Exception as e:
            print(f"problem with item: {item}")
            print(f"error: {e}")

def create_map():
    """
    TODO: dynamodb scans are against best practice...learn how to implement query!
    """
    resource = boto3.resource('dynamodb', region_name='us-east-1')
    table = resource.Table(DYNAMODB_TABLE_NAME)

    response = table.scan(
        FilterExpression=Attr('status').eq('APPROVED')  &~ Attr('longitude').eq(0),
    )
    data = response['Items']
    gmap = gmplot.GoogleMapPlotter(data[0]['latitude'], data[0]['longitude'], 13, apikey=GOOGLE_MAPS_API_KEY)
    for item in data:
        #print(item['longitude'])
        gmap.marker(item['latitude'], item['longitude'], title=item['food_items'], label=item['applicant'])
    gmap.draw('/tmp/map.html')

def upload_map_to_s3():
    s3 = boto3.resource('s3', region_name='us-east-1')
    bucket = s3.Bucket(S3_BUCKET)
    bucket.upload_file('/tmp/map.html', 'map.html', ExtraArgs={'ACL':'public-read', 'ContentType': 'text/html'})

def handler(event, context):
    data = get_foodtruck_data(CSV_URL)
    write_data_to_dynamodb(data)
    create_map()
    upload_map_to_s3()

