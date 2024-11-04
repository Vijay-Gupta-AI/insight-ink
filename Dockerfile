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
