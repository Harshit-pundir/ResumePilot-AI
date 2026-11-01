from datetime import datetime , timedelta , timezone
import jwt
from config import JWT_SECRET
from pwdlib import PasswordHash
from utils.constants import EXPIRE_MINUTES

if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is not present in .env")


hasher = PasswordHash.recommended()

def hash_password(password : str) -> str:
    return hasher.hash(password)

def verify_password(password : str ,hashed_password : str) -> bool:
    return hasher.verify(password,hashed_password)

def create_token(user_id):
    expiry = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES)
    return jwt.encode({"sub" : user_id , "exp" : expiry} , JWT_SECRET , algorithm="HS256")

def read_token(token):
    try:
        data = jwt.decode(token,JWT_SECRET,algorithms=["HS256"])
        return data["sub"]
    except jwt.PyJWTError:
        return None
