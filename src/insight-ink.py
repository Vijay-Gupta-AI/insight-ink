import streamlit as st
import pandas as pd
import numpy as np
import configparser as cf
import os
from PIL import Image
from streamlit_autorefresh import st_autorefresh
import json
from json.decoder import JSONDecodeError
from datetime import datetime
import requests
import warnings
import logging
from datetime import timedelta
#import matplotlib.pyplot as plt
#import seaborn as sns
import altair as alt
import time
warnings.filterwarnings("ignore")
image_favicon = Image.open('./../images/favicon-vj.png')
st.set_page_config(page_title="Insight Ink App",page_icon=image_favicon,layout="wide")
hide_streamlit_style = """
                <style>
                #MainMenu {visibility: hidden;}
                footer {visibility: hidden;}
                </style>            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
image_sidebar = Image.open('./../images/favicon-vj.png')
st.sidebar.image(image_sidebar, width=30)
image = Image.open('./../images/insight-ink.png')
# Function to save updated JSON back to file
def save_json(data, file_path):
    try:
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"Data saved to {file_path}")
    except Exception as e:
        print(f"Error saving JSON: {e}")

def transform_test_output(test_output):
    transformed_output = {}
    for query in test_output["Queries"]:
        transformed_output[query["Alias"]] = query["Text"]
    return transformed_output

def load_json(file_path):
    try:
        print(f"Trying to load JSON from: {file_path}")
        with open(file_path, 'r') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"File not found: {file_path}")
        data = {"abc": 1}  # Default data
    except JSONDecodeError:
        print(f"Error decoding JSON file: {file_path}")
        data = {"abc": 1}  # Default data
    return data
def generate_queries_output(template_name, template):
    # Generate test output corresponding to the activated template values
    test_output = {'Queries': []}
    for key, value in template.items():
        query = {
            'Text': value,
            'Alias': key,
            'Pages': ['*']
        }
        test_output['Queries'].append(query)
    # Write output to a JSON file
    output_file = f'{template_name}_output.json'
    with open(output_file, 'w') as f:
        json.dump(test_output, f, indent=4)
    return test_output

def save_json(data, file_path):
    with open(file_path, 'w') as f:
        json.dump(data, f,indent=4)

def launch_processing(authorization_token, prompt_template_name):
    api_endpoint = f'<your api url>/process-docs/?prompt_template_name={prompt_template_name}'
    headers = {f'authorization': f'{authorization_token}'}
    

    response = requests.post(api_endpoint, headers=headers,)
    return response.json()    

# Function to call the second API and check status
def check_status(authorization_token, output_value,prompt_template_name):
    url = f"<your api url>/job-status/{output_value}?prompt_template_name={prompt_template_name}"  # Replace with the actual URL
    headers = {f'authorization': f'{authorization_token}'}

    response = requests.get(url, headers=headers)
    return response.json()
    
 
def delete_from_s3(authorization_token, prompt_template_name):
    api_endpoint = f'<your api url>/delete-s3-files/?prompt_template_name={prompt_template_name}'
    headers = {f'authorization': f'{authorization_token}'}
    

    response = requests.post(api_endpoint, headers=headers)
    return response.json()  

def upload_api(prompt_template_name: str, authorization_header: str, pdf_files: list) -> requests.Response:
    """
    Uploads a list of PDF files to the specified API endpoint with authorization header.

    Args:
        prompt_template_name (str): The name of the prompt_template_name associated with the upload.
        authorization_header (str): The authorization token for API access.
        pdf_files (list): A list of PDF file objects to be uploaded.

    Returns:
        response (requests.Response): The response object returned by the API call.
        
    Raises:
        Exception: If the API request fails or an error occurs during the upload process.
    """
    
    api_endpoint = f'<your api url>/upload-pdfs/?prompt_template_name={prompt_template_name}'

    try:
        # Create a list of tuples for files (name, file, content_type)
        files = [('file_list', (pdf_file.name, pdf_file.read(), 'application/pdf')) for pdf_file in pdf_files]
        logging.info(f"Preparing to upload {len(pdf_files)} files.")

        # Create the headers with the authorization token
        headers = {'Authorization': authorization_header}

        # Display the files being uploaded (for debugging purposes)
        st.write(f"Uploading the following files: {[file[1][0] for file in files]}")

        # Make the API call
        response = requests.post(api_endpoint, headers=headers, files=files)

        # Check if the response indicates a successful upload
        response.raise_for_status()  # Will raise HTTPError for bad responses (4xx, 5xx)

        logging.info("File upload successful.")
        return response

    except requests.exceptions.RequestException as e:
        # Handle network-related errors (e.g., timeout, connection error)
        logging.error(f"Request error during file upload: {e}")
        st.error(f"An error occurred while uploading files: {e}")
        st.stop()

    except Exception as e:
        # Handle any other unexpected exceptions
        logging.error(f"Unexpected error during file upload: {e}")
        st.error(f"An unexpected error occurred during file upload: {e}")
        st.stop()

def get_access_token(api_key: str) -> str:
    """
    Retrieves an access token from the authorization API using the provided API key.

    Args:
        api_key (str): The API key used to authenticate and request the access token.

    Returns:
        str: The access token if the request is successful.
        
    Raises:
        Exception: If the API request fails or the token is not found in the response.
    """
    auth_api_endpoint = '<your api url>/token'

    try:
        # Make the POST request to the API endpoint
        response = requests.post(auth_api_endpoint, data={'secret_key': api_key})

        # Check if the request was successful
        response.raise_for_status()  # Will raise HTTPError for bad responses (4xx, 5xx)

        # Parse the response JSON
        result_json = response.json()

        # Check if the access token is present in the response
        if 'access_token' in result_json:
            logging.info("Access token successfully retrieved.")
            return result_json['access_token']
        else:
            error_msg = "Access token not found in the response."
            logging.error(error_msg)
            st.error(error_msg)
            st.stop()

    except requests.exceptions.RequestException as e:
        # Handle network-related errors (e.g., timeout, connection error)
        logging.error(f"Request error: {e}")
        st.error(f"An error occurred while contacting the API: {e}")
        st.stop()

    except Exception as e:
        # Handle any other exceptions
        logging.error(f"Unexpected error: {e}")
        st.error(f"An unexpected error occurred: {e}")
        st.stop()

page_selection = st.sidebar.selectbox('Select your Action',('Prompt Setup','Extract Data'))
if page_selection=="Extract Data":

    model_selection=st.sidebar.selectbox('Select Your Model',('Amazon Textract','Google Vision','OpenAI','Azure'))
    if model_selection=="Amazon Textract":
        tab1,tab2,tab3 = st.tabs(["step1 -> Authenticate","step2 ->Upload Pdf's","step3 ->Process"])
        with tab1:

            secret_key = st.text_input("Enter the Secret Key:", type="password")
            if st.button("Authenticate"):
                # Call the authorization API to get the access token
                access_token = get_access_token(secret_key)
                st.session_state.access_token = access_token
                st.success("Authentication Successful!")
                st.info(f"Copy the following access token for further steps: `{access_token}`")
        with tab2:
            # Dropdown for selecting a Prompt Template
            prompt_template = ['ST-121-NY', 'CDTFA-230-M-CA']  # Replace with your actual list of states
            selected_pr_template = st.selectbox("Select a Prompt Template:", prompt_template)
            
                # st.write(st.session_state)
                # File Upload
            # Check if the access token is present in the session state
            st.write(f"You have selected {selected_pr_template} Prompt Template")
            if 'access_token' in st.session_state:
                # File upload widget
                uploaded_files = st.file_uploader("Upload multiple files", type=["pdf"], accept_multiple_files=True)

                # Show a "Process" button only after files are uploaded
                if uploaded_files:
                    st.info("Files uploaded, ready to process.")

                    # Process button to trigger the upload API
                    process_button = st.button("Process Files")
                    
                    if process_button:
                        try:
                            # Create authorization header with the obtained access token
                            authorization_token = st.session_state.access_token

                            # Call the API to upload files
                            st.info("Calling API...")

                            # Upload API is called only after clicking "Process Files"
                            response = upload_api(selected_pr_template, authorization_token, uploaded_files)

                            # Check if the response is successful and extract data
                            uploaded_files_list = response.json().get("uploaded_files", [])
                            total_files = response.json().get("total_files", 0)

                            # Display success message with file details
                            if total_files > 0:
                                st.success(f"Files uploaded successfully: {', '.join(uploaded_files_list)}")
                                st.info(f"Total files uploaded: {total_files}")
                            else:
                                st.warning("No files were uploaded. Please try again.")
                        
                        except Exception as e:
                            # Display error message if the API call fails
                            st.error(f"Error occurred during file upload: {e}")

            else:
                st.warning("You need to be generate the Token from the first tab to upload files. Please authenticate first.")
        with tab3:
            # Dropdown for selecting a prompt-template
            prompt_template_1 = ['ST-121-NY', 'CDTFA-230-M-CA']  # Replace with your actual list of states
            selected_prompt_template_1 = st.selectbox("Choose a Prompt Template:", prompt_template_1)
            # Launch processing button
            if st.button("Launch Processing"):
                if 'access_token' in st.session_state:
                    st.info("Launching Processing...")
                    
                    authorization_token = st.session_state.access_token
                    # st.write(authorization_token)
                    # st.write(selected_state_proccess)
                    try:
                        processing_response = launch_processing(authorization_token, selected_prompt_template_1)
                        # st.write(processing_response)
                        if processing_response.get("status_code") == 202:
                            output_value = processing_response.get("output")
                            st.write(output_value)
                            progress_text = st.empty()
                            
                            while True:
                                result_response = check_status(authorization_token, output_value,selected_prompt_template_1)
                                status = result_response.get("status")
                                # st.write(f"Current status: {status}")  # Debugging output
                                if status == "completed":
                                    progress_text.text(f"Completed...")
                                    break
                              
                               
                                else:
                                    progress_text.text("Running...")
                                    time.sleep(10) 

                                

                            if status == "completed":
                                st.success("Processing completed successfully!")

                                # Extract the results and display
                                result = result_response.get("result", {})
                                output_list = result.get("output", [])
                                df = pd.DataFrame([list(d.values())[0] for d in output_list])

                                # Renaming columns for readability
                                column_mapping = {
                                    "file": "File",
                                    "prompt11": "Prompt Template",
                                    "prompt9": "Average Confidence",
                                    "prompt10": "Document Type",
                                    "prompt1": "Authority/Permit Number",
                                    "prompt2": "Seller Name",
                                    "prompt3": "Seller Address",
                                    "prompt4": "Purchaser Name",
                                    "prompt5": "Purchaser Address",
                                    "purchaserCity": "Purchaser City",
                                    "purchaserState": "Purchaser State",
                                    "prompt6": "Version No.",
                                    "prompt7": "Blanket Certificate",
                                    "prompt8": "Date Issued"
                                }
                                df = df.rename(columns=column_mapping)
                                st.write(f"Total Files Processed: {len(output_list)}")
                                st.dataframe(df)

                                # Call delete_from_s3 after processing
                                delete_record = delete_from_s3(authorization_token, selected_prompt_template_1)
                                

                    except Exception as e:
                        st.error(f"API Request Error: {e}")
elif page_selection=="Prompt Setup":
    with st.sidebar:
        st.subheader("Select Options")
        document_type = st.selectbox("Select Document Type", ["Exemption Certificate","Tax Certificates", "Invoices","Purchase Orders"])
        state = st.selectbox("Select State", ["None","AL","AK","AZ","AR","CA","CO","NY","TX","MA","PA"])
        form_type = st.selectbox("Select Form Type", ["None","ST-121-NY","CDTFA-230-M-CA"])
        
        template_name = f"{document_type}-{state}-{form_type}"
    # st.write(template_name)
    
    # Load JSON file
    current_directory = os.getcwd()
   
    file_path = os.path.join(current_directory, 'data.json')

    json_data = load_json(file_path)
        # Initialize session state for holding the template data
    if 'template_data' not in st.session_state:
        st.session_state.template_data = {}
    if 'original_template' not in st.session_state:
        st.session_state.original_template = {}

    if template_name in json_data:
        st.write("Activated Template:", template_name)
        approved_template_options = [template_name]
        if st.button("Generate Query Output"):
            # Generate and display test output
            template = json_data.get(template_name, {})
            test_output = generate_queries_output(template_name, template)
            st.write(test_output)
            

            
    else:
            # Show activate button if template_name is not in data.json
            approved_template_options = list(json_data.keys())
            approved_templates=st.selectbox("Approved Prompt Template", approved_template_options)
            template_name=approved_templates
            if st.button("Activate"):
                
                # Add template_name with default values to data.json
                template_name = f"{document_type}-{state}-{form_type}"
                template = json_data.get(approved_templates, {})
                
                # Iterate through the template keys and update values if edited
                for key, value in template.items():
                    # Generate a unique key for the text input widget
                    input_key = f"text_input_{key}_{template_name}"
                    new_value = st.text_input(key, value, key=input_key)  # Get the edited value
                    template[key] = new_value

                test_output = generate_queries_output(approved_templates, template)
                json_data[template_name]= transform_test_output(test_output)
                save_json(json_data, 'data.json')
                # save_json(json_data, 'data.json')
                
                st.write(f"Template {template_name} activated successfully!")
            


