from src.document_processor import DocumentProcessor
from src.document import Document
import os
import json
import boto3
import dotenv
import tempfile
import pandas as pd
import argparse
from src.models import return_prompt_template
import time
import datetime
import tqdm
import pdb
import boto3
import re
from src.logger import logger 
import logging
from src.s3 import get_s3_client
'''
get_inputs scans s3 input folder for file names to process
get_inputs must contain all of the documents, otherwise they will be missing from the results
currently no validation to determine if all files are missing, but not difficult to implement
'''


#Heroku    

AWS_Access_Key_ID = os.environ['AWS_ACCESS_KEY_ID']
AWS_Secret_Access_Key = os.environ['AWS_SECRET_ACCESS_KEY']
Bucket=os.environ['BUCKET']
output_prefix_var = os.environ['OUT_PREFIX']
input_prefix_var=os.environ['PREFIX']
region_name=os.environ['TEXTRACT_REGION_NAME'] 
Textract_timeout=os.environ['TEXTRACT_TIMEOUT']
'''
region_name is the region where the s3 bucket is located
textract and bucket must be in the same region for processing to work
'''



def process_documents(analyzer, files, queries, input_prefix, output_prefix):
    logger = logging.getLogger(__name__)

    # Variable to track whether all startProcessing calls were successful
    all_successful = True

    for file in files:
        print(f'Starting processing for document: {file}')
        logger.info(f'Starting processing for document: {file}')

        try:
            # Attempt to process the document
            analyzer.startProcessing(file, queries, input_prefix, output_prefix)

        except Exception as e:
            print(f'Error processing document: {file}')
            # Log the error
            logger.error(f'Error processing document: {file}. Error: {str(e)}')
            all_successful = False  # Mark that not all processing attempts were successful
            break  # Exit the loop if any processing attempt fails

    if all_successful:
        # If all processing attempts were successful, run the tqdm loop
        # Check if Textract_timeout_str is not None and is a valid integer
        global Textract_timeout

        #Heroku Variable
        Textract_timeout_str=os.environ['TEXTRACT_TIMEOUT']
        if Textract_timeout_str is not None and Textract_timeout_str.isdigit():
            Textract_timeout = int(Textract_timeout_str)
        else:
        # Default value if TEXTRACT_TIMEOUT is not set or is not a valid integer
            Textract_timeout = 100  # Example default value, replace with your desired default

        # Log and print Textract timeout
        timeout_message = f'TextRact Timeout Set in Config, {Textract_timeout}'
        logger.info(timeout_message)
        print(timeout_message)

        # Loop with tqdm progress bar
        for i in tqdm.tqdm(range(Textract_timeout)):
            time.sleep(3)
            remaining_seconds = (Textract_timeout - i) * 3
            wait_message = f'Waiting for Textract to process documents, {remaining_seconds} seconds remaining'
            logger.info(wait_message)
            print(wait_message)




def extract_organization_name(text):
    # Remove any digits (numbers) from the text
    text = re.sub(r'\d', '', text)
    
    # Remove known suffixes and content within parentheses
    text = re.sub(r'\.pdf$', '', text)       # Remove ".pdf" suffix
    text = re.sub(r'\(.*\)', '', text)       # Remove anything within parentheses
    
    # Split the text by underscores (_) and hyphens (-)
    parts = re.split(r'[_-]', text)
    
    # Filter out empty parts
    parts = list(filter(None, parts))
    
    # Check if any part contains "ST"
    for part in parts:
        if "ST" in part:
            return parts[-2].strip()  # Return the element at index -2
    
    # If "ST" is not found, return the last element
    if parts:
        return parts[-1].strip()
        


def get_inputs(client, bucket, prompt_template, prefix_name):
    
    files = []

    try:
        # Build the prefix for the input files
        prefix = f'{prefix_name}{prompt_template}/'
        logger.info(f"Function 'get_inputs': Prefix is {prefix}")

        # Retrieve the initial set of results
        results = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        logger.info(f"Function 'get_inputs': Results are {results}")

        # Extract file keys from the initial results
        files.extend(file['Key'] for file in results.get('Contents', []))
        logger.info(f"Function 'get_inputs': Files are {files}")

        # Remove the prefix itself from the list
        files.remove(prefix)

    except Exception as e:
        logger.error(f"Function 'get_inputs': An exception occurred - {str(e)}")
        # Handle the exception gracefully, log it, and possibly raise it again if needed.

    try:
        # Check if the result set is truncated
        continuation_token = results.get('NextContinuationToken')

    except KeyError:
        logger.warning("Function 'get_inputs': NextContinuationToken not found in results.")
        # Handle the case where 'NextContinuationToken' is not present.

    else:
        # Continue fetching more results if the result set is truncated
        while continuation_token:
            try:
                result = client.list_objects_v2(Bucket=bucket, Prefix=prefix, ContinuationToken=continuation_token)

            except Exception as e:
                logger.error(f"Function 'get_inputs': An exception occurred during continuation - {str(e)}")
                # Handle the continuation exception gracefully

            else:
                # Extract file keys from the continuation results
                files.extend(file['Key'] for file in result.get('Contents', []))

                # Update the continuation token for the next iteration
                continuation_token = result.get('NextContinuationToken')

        logger.info("Function 'get_inputs': All results have been retrieved.")

    return files



'''
get_results returns the results of the last completed job for a specified document
pairs with get_ouputs
downloads the actual json file, so will take some time
'''



def get_results(file, client, bucket, prompt_template,prefix_name):
   

    # Build the prefix for the output files
    # prefix = f'{prefix_name}/{prompt_template}/' + file.split('/')[-1]
    prefix = f'{prefix_name}' + file.split('/')[-1]
    logger.info(f"get_results - prefix - {prefix}")
    try:
        # Retrieve the list of jobs for the specified file
        jobs = client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        # logger.info(f"get_results - from jobs - {jobs}")
    except Exception as e:
        logger.error(f"An error occurred while retrieving jobs for {file}: {str(e)}")
        print(f'Document {file} not processed')
        return None

    try:
        # Find the most recent job based on LastModified timestamp
        latest_job_key = max(jobs.get('Contents', []), key=lambda x: x['LastModified'])['Key']
        latest_job_prefix = '/'.join(latest_job_key.split('/')[:-1])

    except ValueError:
        logger.warning(f"No jobs found for {file}")
        print(f'Document {file} not processed')
        return None

    # Filter files based on the latest job prefix
    files = [x['Key'] for x in jobs.get('Contents', []) if x['Key'].startswith(latest_job_prefix)]
    # logger.info(f"get_results - from files - {files}")
    with tempfile.TemporaryDirectory() as tmpdir:
        for file_key in files:
            if file_key == latest_job_prefix + '/.s3_access_check':
                continue
            else:
                local_path = os.path.join(tmpdir, file_key.split('/')[-1])
                client.download_file(bucket, file_key, local_path)

        results = []

        for local_file in os.listdir(tmpdir):
            file_path = os.path.join(tmpdir, local_file)

            try:
                with open(file_path, 'r') as json_file:
                    file_data = json.load(json_file)

                if not results:
                    results = file_data
                else:
                    results['Blocks'] += file_data['Blocks']

            except Exception as e:
                logger.error(f"An error occurred while processing file {file_path}: {str(e)}")

    return results



'''
get_outputs scans s3 output folder for files that have already been processed
can be used to validate if all of the input files have been processed
like get_inputs, returns a list of all of the file names that have been processed
'''
def get_outputs(client, bucket, prompt_template,output_prefix_name):
    files = []
    continuation_token = None
    complete = False

    prefix = f'{output_prefix_name}{prompt_template}/'

    results = client.list_objects_v2(Bucket=bucket, Prefix=prefix, Delimiter='/')
    logger.info(results)
    try:

        if 'CommonPrefixes' in results:
            for file in results['CommonPrefixes']:

                files.append(file['Prefix'])

    
        
    except Exception as e:
        logger.error(f"An error occurred while listing objects for prefix '{prefix}': {str(e)}")
        print(f"An error occurred while listing objects for prefix '{prefix}'.")
        
    try:
        continuation_token = results['NextContinuationToken']
    except:
        print('Not truncated, all results returned')
        return files

    while not complete:
        result = client.list_objects_v2(Bucket=bucket, Prefix=prefix, ContinuationToken=continuation_token, Delimiter='/')
        for file in result['CommonPrefixes']:
            files.append(file['Prefix'])

        if result['IsTruncated']:
            continuation_token = result['NextContinuationToken']
        else:
            complete = True

    
    return files









#if __name__ == '__main__':
def process_files(prompt_template_name):
    





    '''
    Check if the passed prompt_template args are valid
    '''

    prompt_template=prompt_template_name
    





    try:
        client = get_s3_client()
        inputs = list(map(lambda x: x.removeprefix(f'{input_prefix_var}{prompt_template}/'), get_inputs(client, Bucket, prompt_template,input_prefix_var)))
        logger.info(f"inputs in process_files is {inputs}")
       
        outputs = list(map(lambda x: x.removeprefix(f'{output_prefix_var}{prompt_template}/'), get_outputs(client, Bucket, prompt_template,output_prefix_var)))
        files = [x for x in inputs if x.removeprefix(f'{input_prefix_var}{prompt_template}/') not in list(map(lambda x: x.removeprefix(f'{output_prefix_var}{prompt_template}/')[:-1], outputs))]
        #else:
        #    files = get_inputs(client, Bucket, prompt_template)
            
        logger.info('Number of files to process: ' + str(len(files)))
        if len(files) == 0:
            logger.info('No files to process, exiting')
            exit()
        
        analyzer = DocumentProcessor(Bucket, region_name)
        queries = return_prompt_template(prompt_template)[0]
        input_prefix = f'{input_prefix_var}{prompt_template}/'
        output_prefix= f'{output_prefix_var}{prompt_template}/'
        logger.info(f"input_prefix is {input_prefix}")
        logger.info(f"output_prefix is {output_prefix}")
        process_documents(analyzer, files, queries, input_prefix, output_prefix)
        


        results = []
        low_conf = []


        #if args.all_results:
        #    files = get_inputs(client, Bucket, prompt_template)
        logger.info(f"Files are {files}")
        for file in files:
    # Check if the file is valid
            if not file:  # This checks for empty strings or None
                logger.warning('Encountered an empty file entry, skipping...')
                continue
            
            try:
                # file_name = file.split('/')[-1]  # Extract just the file name
                file_name = file
                doc = Document(prompt_template)  # Initialize your Document
                data = get_results(file, client, Bucket, prompt_template, output_prefix)  # Get results for the file
                # logger.info(f"data {data}")
                # Ensure data is valid before exporting results
                if data is not None:
                    results.append(doc.export_results(file_name, data))

                    if doc.prompt9 < 60:
                        low_conf.append(doc.file_name)

                    logger.info('Processed ' + file_name)
                    print('Processed ' + file_name)
                else:
                    logger.warning(f'No data returned for file: {file_name}')
            except Exception as e:
                logger.error(f'Error processing file {file_name}: {str(e)}')



        cleaned_results = {}
        for doc in results:
            for key in doc.keys():
                cleaned_results[key] = {}
                # print(doc[key])
                for alias in doc[key].keys():
                    if doc[key][alias] != None:
                        cleaned_results[key][alias] = doc[key][alias]
                    else:
                        cleaned_results[key][alias] = None
        df = pd.DataFrame.from_dict(cleaned_results, orient='index')
        df.reset_index(inplace=True)
        df.rename(columns={'index': 'file'}, inplace=True)
        #print(df)
        
        return(df)

    except Exception as e: 
        logger.info(f"Exception in process_files is{str(e)}") 
    
