import os
import boto3
import dotenv
from botocore.exceptions import NoCredentialsError
from tempfile import NamedTemporaryFile
from fastapi import HTTPException
from src.logger import logger  
from src.s3 import get_s3_client


#==>For Heroku

Bucket = os.environ['BUCKET']
output_prefix = os.environ['OUT_PREFIX']
del_input_flag = os.environ['DEL_INPUT']
input_prefix=os.environ['PREFIX']

def list_objects_to_delete(s3, Bucket_name, folder_prefix):
    objects_to_delete = []
    
    paginator = s3.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=Bucket_name, Prefix=folder_prefix):
        for obj in page.get('Contents', []):
            objects_to_delete.append({'Key': obj['Key']})
    final_object_to_delete=[obj for obj in objects_to_delete if not obj['Key']==folder_prefix]
    return final_object_to_delete

def delete_files_from_s3_folder(state_name):#Pass the State Name, S3 Bucket and S3 Folder whose content needs to be deleted
    
    
    
        try:
            s3 = get_s3_client()  # You can use get_s3_client from your s3.py module
            Bucket_name=Bucket
            state=state_name
            s3_folder_name=output_prefix
            folder_prefix=s3_folder_name+state+"/"
            objects_to_delete=[]
            # List of Files to delete from s3 folder
            objects_to_delete=list_objects_to_delete(s3, Bucket_name, folder_prefix)
            if del_input_flag=='Y':
                objects_input_to_delete=[]
                folder_input_prefix=input_prefix+state+"/"
                objects_input_to_delete=list_objects_to_delete(s3, Bucket_name, folder_input_prefix)
                objects_to_delete=  objects_to_delete +  objects_input_to_delete
                        
            # Delete objects in bulk
            if objects_to_delete:
                response = s3.delete_objects(Bucket=Bucket_name, Delete={'Objects': objects_to_delete})
                return {"success":True, "status_code": 200, "message": "Files deleted successfully", "deleted_objects": response.get('Deleted', [])}
            else:
                return {"success":True,"status_code": 200, "message": "No files found to delete", "deleted_objects": []}
        except Exception as e:
            return {"success":False,"status_code": 500, "message": "An unexpected error occurred", "error_message": str(e)}
    

def upload_file_to_s3(file, state_name, bucket):
    response={}
    pdf_filename = file.filename
 
    s3_folder = input_prefix + state_name

    s3_key = f"{s3_folder}/{pdf_filename}"
    try:

        # Create a temporary file to store the uploaded PDF
        with NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
            
            while chunk := file.file.read(10000):
                temp_pdf.write(chunk)
            # except Exception as e:
            #     logger.error(f"Error reading file: {e}")
            #     raise HTTPException(status_code=400, detail="Error reading file")

        s3 = get_s3_client()  # You can use get_s3_client from your s3.py module

        # try:
        upload_status=s3.upload_file(temp_pdf.name, bucket, s3_key)
        print(upload_status)
        # except Exception as e:
            # logger.error(f"Error uploading file to S3: {e}")
            

        # Clean up the temporary file
        os.remove(temp_pdf.name)
        
        # response= {"success":True,"status_code": 200, "message": f"File Uploaded to S3 {bucket} successfully", "error_message":None}
    except Exception as e:
        response= {"success":False,"status_code": 500, "message": "An unexpected error occurred", "error_message": str(e)}
        logger.error(response)
        pdf_filename="errorpdffile_500_"+str(e)
    return pdf_filename 
