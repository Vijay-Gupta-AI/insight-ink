import boto3
import json


'''
DocumentProcessor class returns a client that is used to initialize a Textract async job
The client is used to start the job but does not retrieve the results
'''

class DocumentProcessor:

    def __init__(self, bucket, region):
        self.bucket = bucket
        self.region_name = region

        self.textract = boto3.client('textract', region_name=self.region_name)

    def startProcessing(self, document, queries,input_prefix,output_prefix):
        
        self.textract.start_document_analysis(
                
                DocumentLocation={'S3Object': {'Bucket': self.bucket, 'Name': input_prefix+document}},
                FeatureTypes=["QUERIES", "SIGNATURES"],
                            QueriesConfig = queries,
                # OutputConfig={'S3Bucket': self.bucket, 'S3Prefix': 'output/NY/' + document.split('/')[-1]})
                OutputConfig={'S3Bucket': self.bucket, 'S3Prefix': output_prefix + document})

