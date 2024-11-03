import os
import json
import boto3
import dotenv
from src.s3 import get_s3_client

s3 = get_s3_client()  # You can use get_s3_client from your s3.py module

# Load environment variables
dotenv.load_dotenv('system.env')
Bucket = os.environ.get('BUCKET')
output_prefix = os.environ.get('OUT_PREFIX')