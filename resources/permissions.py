'''
	You must replace <bucket-name> with your actual bucket name
'''
import boto3
import json
from pathlib import Path

S3API = boto3.client("s3", region_name="us-east-1")
bucket_name = "<FMI_1>"

policy_file = open(Path(__file__).with_name("website_security_policy.json"), "r")


S3API.put_bucket_policy(
    Bucket = bucket_name,
    Policy = policy_file.read()
)
print ("DONE")
