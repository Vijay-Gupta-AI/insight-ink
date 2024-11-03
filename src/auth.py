# auth.py

from datetime import datetime, timedelta
import jwt
from jwt.exceptions import ExpiredSignatureError, PyJWTError,InvalidTokenError
import dotenv,os
from fastapi import HTTPException, status
#==>For Docker
dotenv.load_dotenv('system.env')
SECRET_KEY = os.environ.get('SECRET_KEY')
API_KEY = os.environ.get('API_KEY')

#==>For Heroku
# SECRET_KEY = os.environ['SECRET_KEY']
# API_KEY = os.environ['API_KEY']
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

def verify_secret_key(form_secret_key: str):
    if form_secret_key == SECRET_KEY:
        return create_access_token(API_KEY)
    else:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid secret key",
            headers={"WWW-Authenticate": "Bearer"},
        )
def create_access_token(api_key: str):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    encoded_jwt = jwt.encode({"exp": expire}, api_key, algorithm=ALGORITHM)
    return encoded_jwt


def verify_access_token(token: str):
    try:
        payload = jwt.decode(token, API_KEY, algorithms=[ALGORITHM], options={"verify_signature": True})
        return payload
    except ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )    