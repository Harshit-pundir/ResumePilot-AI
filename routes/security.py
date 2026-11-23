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

def create_token(user_id, email=None, role="user"):
    expiry = datetime.now(timezone.utc) + timedelta(minutes=EXPIRE_MINUTES)
    claims = {"sub": user_id, "exp": expiry, "role": role or "user"}
    if email:
        claims["email"] = email
    return jwt.encode(claims, JWT_SECRET, algorithm="HS256")


def read_token_claims(token):
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        return data if data.get("sub") else None
    except jwt.PyJWTError:
        return None


def read_token(token):
    """Backward-compatible helper returning only the authenticated subject."""
    claims = read_token_claims(token)
    return claims.get("sub") if claims else None
