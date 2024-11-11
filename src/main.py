from fastapi import FastAPI, File, UploadFile, HTTPException,Depends,status,Form,Header
from tempfile import NamedTemporaryFile
import dotenv
import os
import sys
import requests
from pydantic import BaseModel
from src.s3_operations import upload_file_to_s3,delete_files_from_s3_folder  # Import the function
from src.auth import create_access_token,verify_secret_key,verify_access_token
import json
from src.logger import logger
app = FastAPI()

       
#==>> Load environment variables for heroku Use
# Bucket = os.environ['BUCKET']
# input_prefix = os.environ['PREFIX']
# output_prefix = os.environ['OUT_PREFIX']
    
@app.post("/token", response_model=dict)
async def get_token(secret_key: str = Form(...)):
    token=verify_secret_key(secret_key)
    # token = create_access_token()
    return {"access_token": token, "token_type": "bearer"}


#Starting the API endpoints
@app.post("/upload-pdfs/")
async def upload_pdfs(state_name: str, file_list: list[UploadFile] = File(...),authorization: str = Header(None)):
    if authorization is None:
        flag=0
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is missing",
            headers={"WWW-Authenticate": "Bearer"},
        )
    flag=1
    response = {
        "message": "Files uploaded successfully",
        "success": True,
        "error_code": None,
        "status_code": 200,
        "error_message":None,
        "uploaded_files": [],
        "total_files": 0,
    }

    try:
        
        payload = verify_access_token(authorization)
        state_name = state_name
        for uploaded_file in file_list:
            pdf_filename = upload_file_to_s3(uploaded_file, state_name, Bucket)  # Pass the required variables
            
            if "errorpdffile" in pdf_filename:
                flag=0
                break
            else:
                response["uploaded_files"].append(pdf_filename)
        if flag==1:
            
            response["total_files"] = len(file_list)
            logger.info(f"Uploaded {len(file_list)} files to S3 bucket'")
            logger.info(response)
            print(f"Uploaded {len(file_list)} files to S3 bucket'")
            print(response)
        else:
            error_lst=pdf_filename.split("_")
            if len(error_lst) >= 3:
                response["error_message"]="".join(error_lst[2:])
                response["status_code"] =error_lst[1]
                response["error_code"] =error_lst[1]
                response["success"] =False
                response["message"]="An unexpected error occurred"
                print(error_lst)
                response["total_files"] =0
    except HTTPException as e:
        response["message"] = str(e.detail)
        response["error_code"] = "S3_ERROR"
        response["success"] = False
        response["status_code"] = e.status_code
        logger.error(response)
        print(response)
    return response

           
    

#==>Enable for Heroku
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=port)
