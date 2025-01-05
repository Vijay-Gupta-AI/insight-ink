import os
import redis
from urllib.parse import urlparse
from rq import Worker, Queue#, Connection
# from rq import async as async_rq
from src.worker import worker_function_process_files
from redis import Redis
import logging
# Configure logging
logging.basicConfig(level=logging.INFO)
ocr_queue = os.environ["OCR_QUEUE"]
listen = [ocr_queue]
#Set redis configuration for the Heroku set up
redis_url = os.environ["REDISCLOUD_URL"]
url_parts = urlparse(redis_url)
redis_host = url_parts.hostname
redis_port = url_parts.port
redis_password = url_parts.password
import sys
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

#Set redis configuration for the Heroku set up
redis_conn = Redis(host=redis_host, port=redis_port, password=redis_password)
#Set redis configuration for the Local set up
# redis_conn = Redis(host='ocr-redis', port=6379, db=0)
if __name__ == '__main__':
    logging.info(f"Starting worker , listening to queues: {listen}")
    # with Connection(redis_conn):
    #     worker = Worker(map(Queue, listen))
    #     worker.work()
    queue = Queue(ocr_queue, connection=redis_conn)
    worker = Worker([queue], connection=redis_conn)
    worker.work()

