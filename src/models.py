import re
from datetime import datetime
from src.logger import logger
import logging
valid_prompt_template = ['ST-121-NY', 'CDTFA-230-M-CA']

def assign_attr(out, attr_name):                              
    if attr_name in out:
        return out[attr_name]
    else:
        return None

def replace_attributes(input_string, replacements):
        
        
        for attribute, replacement in replacements.items():
            input_string = input_string.replace(attribute, replacement)
        return input_string

def format_date(date_str):
    if not date_str:
        return None

    try:
        # Attempt to parse the date using different formats
        date_formats = [
            "%B %d, %Y",    # April 09, 2029
            "%B %d. %Y",    # April 09. 2029
            "%m.%d.%Y",     # 2.24.2022
            "%m/%d/%Y %I:%M:%S %p",  # 8/25/2021 12:00:00 AM
            "%m/%d/%Y",     # 01/08/2021
            "%d/%m/%Y",     # European style dates
            "%Y-%m-%d",     # ISO format
            "%d-%m-%Y",     # Alternative European style dates
            "%m-%d-%Y",     # Month-Day-Year
            "%m/%d/%y",     # Short year format
            "%d/%m/%y",     # European style short year format
            "%y/%m/%d"      # Short year format with Year first
        ]
        for fmt in date_formats:
            try:
                date_obj = datetime.strptime(date_str, fmt)
                return date_obj.strftime("%m/%d/%Y")
            except ValueError:
                pass  # Try the next format
        
        # If unable to parse, return the original string
        return date_str
    except TypeError:
        # If None or other non-string type is passed, return None
        return None




def return_prompt_template(prompt_template):
    if prompt_template in valid_prompt_template:

            return (extract_queries, extract_results)
        

    else:
        raise ValueError('prompt_template not supported')
    


def extract_results(self, out, results):
    # logger.info(out)
    # logger.info(results)
    for block in self.raw['Blocks']:
        if block['BlockType'] == 'LINE':
            if re.match(r"\((\d+/\d+)\)", block['Text']):
                self.prompt6 = block['Text']
            elif re.match(r"ST[\s-]+", block['Text']):
                self.prompt10 = block['Text'].split(' ')[0]

        else:
            continue
    self.prompt1 = out['prompt1']
    self.prompt2 = out['prompt2']
    self.prompt3 = out['prompt3']
    self.prompt4 = out['prompt4']
    self.prompt5 = out['prompt5']
    # self.prompt6 = out['prompt6']
    self.prompt7 = out['prompt7'] == 'SELECTED'
    self.prompt8 = out['prompt8']
    # List of selected prompts to include in the confidence calculation
    selected_prompts = ['prompt1', 'prompt2', 'prompt3', 'prompt4', 'prompt5', 'prompt7', 'prompt8']
    # Dynamic confidence calculation
    confidence = sum([i[0]['Confidence'] for prompt, i in results.items() if prompt in selected_prompts and len(i) > 0])

    # Ensure no division by zero in the next step
    valid_prompts_count = len([prompt for prompt in selected_prompts if prompt in out])

    # Calculate self.prompt9, ensuring no division by zero
    if valid_prompts_count > 0:
        self.prompt9 = confidence / valid_prompts_count
    else:
        self.prompt9 = 0  # Handle the case where no valid prompts are selected
    # confidence = sum([i[0]['Confidence'] if len(i) > 0 else 0 for i in results.values()])
    # self.prompt9 = confidence/(len(out.keys())+1)



extract_queries = {'Queries': [
            {
                'Text': "What is the seller's or cardholder or vendor name?",
                'Alias': 'prompt2',
                'Pages': [
                    '*',
                ]
            },
            {
                'Text': "What is the seller's address?",
                'Alias': 'prompt3',
                'Pages': [
                    '*',
                ]
            },
            {
                'Text': "What is the purchaser or exempt organization's name?",
                'Alias': 'prompt4',
                'Pages': [
                    '*',
                ]
            },
            {
                'Text': "What is the address of the exempt organization/purchaser?",
                'Alias': 'prompt5',
                'Pages': [
                    '*',
                ]
            },
            {
                'Text': "What is the Authority number or Permit number?",
                'Alias': 'prompt1',
                'Pages': [
                    '*',
                ]
            },
            {
                'Text': "What is the date issued?",
                'Alias': 'prompt8',
                'Pages': [
                    '*',
                ]
            },

            {
                'Text': "What are the numbers underneath ST-121?",
                'Alias': 'prompt6',
                'Pages': [
                    '*',
                ]
            },
            {
                'Text': "Blanket certificate",
                'Alias': 'prompt7',
                'Pages': [
                    '*',
                ]
            }

                ]
            }

