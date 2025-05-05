from datetime import datetime, timedelta
from jose import jwt
from passlib.context import CryptContext
import bcrypt

SECRET_KEY = "secret_string"  # Замени на что-то сложное
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except:
        return False



def create_access_token(data: dict, role: str, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire, "role": role})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        # Удаляем 'Bearer ' если есть
        if token.startswith("Bearer "):
            token = token[7:]
            
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")  # Возвращаем email
    except jwt.ExpiredSignatureError:
        print("Token expired")
        return None
    except jwt.JWTError:
        print("Invalid token")
        return None




# def decode_token(token: str):
#     return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


# def decode_access_token(token: str):
#     try:
#         payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
#         return payload.get("sub")
#     except JWTError:
#         return None
