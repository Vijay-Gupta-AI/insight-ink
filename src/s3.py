# from fastapi import HTTPException
import boto3
from botocore.exceptions import NoCredentialsError
# from tempfile import NamedTemporaryFile
import os
import dotenv
from src.logger import logger


#Heroku Use
AWS_Access_Key_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_Secret_Access_Key = os.environ['AWS_SECRET_ACCESS_KEY']
Region = os.environ['REGION_NAME']



def get_s3_client():
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=AWS_Access_Key_ID,
            aws_secret_access_key=AWS_Secret_Access_Key,
            region_name=Region
        )
        return s3
    except NoCredentialsError:
        logger.error("AWS credentials not found. Make sure you have configured AWS credentials.")
        error_response = {
            "message": "AWS credentials not found. Make sure you have configured AWS credentials.",
            "success": False,
            "error_code": "AWS_CREDENTIALS_ERROR",
            "status_code": 500,
        }
        logger.error(error_response)
        return {"success":False, "status_code": 400, "message": "AWS credentials not found. Make sure you have configured AWS credentials.","error_message":"AWS NoCredentialsError"}
    except Exception as e:
        error_response = {
            "message": "AWS credentials Error.",
            "success": False,
            "error_code": str(e),
            "status_code": e.status_code,
        }
        logger.error(error_response)
        return {"success":False, "status_code": e.status_code, "message": "AWS credentials Error.","error_message":str(e)}


