from src.logger import logger 
from src.process import process_files

def worker_function_process_files(prompt_template):
    response = {
        "message": "Files Processed successfully",
        "success": True,
        "error_code": None,
        "error_message":None,
        "status_code": 200,
        "output": [],
        "total_files": 0,
    }
    try:
        
        
        logger.info(f"Starting the Process for {prompt_template} prompt_template in worker")
        logger.info(f"Starting the Process for {prompt_template} prompt_template in worker")
        logger.info(f"Debug: Value of 'prompt_template' in worker_function: {prompt_template}")
        result = process_files(prompt_template)
        json_results=[{f'row_{i+1}': row.to_dict()} for i, row in result.iloc[0:].iterrows()]
        response["output"]=json_results
        response["total_files"]=len(result)
        
    except Exception as e:
        print(f"Debug: Exception in worker_function: {e}")
        # Return the error message if an exception is raised
        response["message"] = str(e)
        response["error_code"] = "OCR PROCESS Error"
        response["success"] = False
        response["status_code"] = 500#e.status_code
        logger.error(response)
        print(response)
    return response    
