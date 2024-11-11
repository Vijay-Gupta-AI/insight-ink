import os
import json
import boto3
import dotenv
from src.s3 import get_s3_client

s3 = get_s3_client()  # You can use get_s3_client from your s3.py module

