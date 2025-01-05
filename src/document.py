import boto3
import json
import re
import os
from src.models import return_prompt_template,format_date,replace_attributes
from src.logger import logger
import logging


class Document:

    def __init__(self, prompt_template):
        
        #change path and file name for API version
        self.file_name = None
        self.valid = False

        self.queries, self.func = return_prompt_template(prompt_template)
        
        self.prompt1 = str()
        self.prompt2 = str()
        self.prompt3 = str()
        self.prompt4 = str()
        self.prompt5 = str()
        self.prompt6 = str()
        self.prompt7 = bool()
        self.prompt8 = str()
        self.raw = None
        self.prompt9 = float()
        self.prompt11 = prompt_template
        self.errorMessage = str()
        self.prompt10 = str()


        self.keys = ['prompt1','prompt2','prompt3','prompt4','prompt5','prompt6','prompt7','prompt8','prompt9','prompt10','prompt11']

    def _check_valid(self):

        # determines if the document is a valid PDF

        if self.file_name.endswith('.pdf'):
            return True
        else:
            return False
            

    def _extract_query(self, queries_blocks, query_results, alias):
        # 
        result = {}
        answer_ids = [] 
        answers = []
        for query in queries_blocks:
            if query['Query']['Alias'] == alias:
                if 'Relationships' in query.keys():
                    if query['Relationships'] == None:
                        continue
                    for relationship in query['Relationships']:
                        if relationship['Type'] == 'ANSWER':
                            for id in relationship['Ids']:
                                answer_ids.append(id)
                        else:
                            continue
                else:
                    continue

            else:
                continue
        
        for query_result in query_results:
            
            for id in answer_ids:
                if query_result['Id'] == id:
                    answers.append(query_result)
                else:
                    continue

        answers = sorted(answers, key=lambda k: k['Confidence'], reverse=True)
        

        result[alias] = answers
        return result

    def _get_primary_page(self):
        query_aliases = [i['Alias'] for i in self.queries['Queries']]
        queries_blocks = []
        query_results = []


        try:
            for i in self.raw['Blocks']:
                if i['BlockType'] == 'QUERY':
                    queries_blocks.append(i)
                elif i['BlockType'] == 'QUERY_RESULT':
                    query_results.append(i)
        except Exception as e:
            print(e)
        
        
        
        # check if data point is in queries
        results = {}
        for query in query_aliases:
            if query in [i['Query']['Alias'] for i in queries_blocks]:
                results = results | self._extract_query(queries_blocks, query_results, query)


        # assuming all info is on one page, take results from highest confidence page
        page_counts = []
        for alias in results:
            for answer in results[alias]:
                page_counts.append(answer['Page'])
        if page_counts != []:
            self.page = max(set(page_counts), key=page_counts.count)
        else:
            self.page = 1
        return self.page

    def _extract_results(self):
        self.file_name = self.file_name
        self.valid = self._check_valid()

        if not self.valid:
            return


        # Pass in json file name (Textract output) and queries dict
        query_aliases = [i['Alias'] for i in self.queries['Queries']]
        queries_blocks = []
        query_results = []


        try:
            for i in self.raw['Blocks']:
                if i['BlockType'] == 'QUERY':
                    queries_blocks.append(i)
                elif i['BlockType'] == 'QUERY_RESULT':
                    query_results.append(i)
        except Exception as e:
            print(e)
        
        
        
        # check if data point is in queries
        results = {}
        for query in query_aliases:
            if query in [i['Query']['Alias'] for i in queries_blocks]:
                results = results | self._extract_query(queries_blocks, query_results, query)
            else:
                results[query] = []

        # assuming all info is on one page, take results from highest confidence page
        self._get_primary_page()
        

        # then make the results from that page the first in the list
        for alias in results:
            for answer in results[alias]:
                if answer['Page'] == self.page:
                    results[alias].remove(answer)
                    results[alias].insert(0, answer)
                else:
                    continue
        
        
        # now get the text value of each item
        out = {} 
        for alias in results:
            if len(results[alias]) > 0:
                out[alias] = results[alias][0]['Text']
            else:
                out[alias] = None


        '''
        
        Below calls the custom function for each prompt_template to extract and apply the key information to the document object

        '''

        self.func(self, out, results)
        


    def _get_signature(self):
        signature = False
        confidence = 0
        for block in self.raw['Blocks']:
            if block['BlockType'] == 'SIGNATURE':
                signature = True
                confidence = block['Confidence']
            else:
                continue
        return (signature, confidence)
    
    
    
    def export_results(self, file_name, data):
        logger = logging.getLogger(__name__)
        self.raw = data
        #Heroku Param
        ADDL_PARAM = os.environ['ADDL_PARAM']
        #Docker Param
        # ADDL_PARAM = os.environ.get('ADDL_PARAM')
        attribute_replacements = {}
        pairs = ADDL_PARAM.split(',')
        
        for pair in pairs:
            attribute, replacement = pair.split(':')
            
            attribute_replacements[attribute] = replacement
            
            
        
        self.file_name = file_name
        
        self._extract_results()
        logger.info(self._extract_results())
        if not self.valid:
            output = {self.file_name: {'prompt11': self.prompt11, 'prompt9': None, 'errorMessage': 'Not a PDF', 'prompt10': None,'prompt1': None,\
                                    'prompt2' : None, 'prompt3' : None, 'prompt4' : None, 'prompt5' : None, 'prompt6' : None, 'prompt7' : None,\
                                        'prompt8' : None }}

        elif self.prompt9 < 60:
            output = {self.file_name: {'prompt11': self.prompt11, 'prompt9': self.prompt9, 'errorMessage': 'Low confidence, different document format?', 'prompt10': self.prompt10, 'prompt1': self.prompt1,\
                                    'prompt2': self.prompt2, 'prompt3': self.prompt3, 'prompt4': self.prompt4, 'prompt5': self.prompt5,\
                                        'prompt6': self.prompt6, 'prompt7': self.prompt7, 'prompt8': self.prompt8\
                                        }}
        else:
            output = {self.file_name: {'prompt11': self.prompt11, 'prompt9': self.prompt9, 'errorMessage': None, 'prompt10': self.prompt10, 'prompt1': self.prompt1,\
                                    'prompt2': self.prompt2, 'prompt3': self.prompt3, 'prompt4': self.prompt4, 'prompt5': self.prompt5,\
                                        'prompt6': self.prompt6, 'prompt7': self.prompt7, 'prompt8': self.prompt8
                                    }}
        return output



    