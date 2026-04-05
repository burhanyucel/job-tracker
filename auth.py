from datetime import datetime, timedelta
from jose import JWTError, jwt
import bcrypt
import os

SECRET_KEY = os.getenv("SECRET_KEY", "gizli-anahtar-789")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

def sifreyi_hashle(sifre: str):
    return bcrypt.hashpw(sifre.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def sifreyi_dogrula(sifre: str, hash: str):
    return bcrypt.checkpw(sifre.encode("utf-8"), hash.encode("utf-8"))

def token_olustur(data: dict):
    kopya = data.copy()
    bitis = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    kopya.update({"exp": bitis})
    return jwt.encode(kopya, SECRET_KEY, algorithm=ALGORITHM)

def tokeni_coz(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None