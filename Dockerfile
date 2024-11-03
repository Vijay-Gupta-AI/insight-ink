##############################################
# Section for Heroku MAIN-OCR app 
FROM python:3.10.11-buster
WORKDIR /OCR_API

COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install -r requirements.txt -vvv
COPY . .
EXPOSE 5000
CMD ["python","-m", "src.main"]

# ##############################################

# # Use a base image compatible with your RQ worker and dependencies
# ##############################################
# #Section for Heroku OCR-WORKER app 
# FROM python:3.10.11-buster

# # Set the working directory inside the container
# WORKDIR /worker

# # Copy the requirements file (if needed)
# COPY requirements.txt .

# # Install any dependencies (if needed)
# RUN pip install --upgrade pip
# RUN pip install -r requirements.txt

# # Copy your RQ worker script and other necessary files
# COPY . .
# CMD ["python","src.run-worker.py"]
# ###############################################
