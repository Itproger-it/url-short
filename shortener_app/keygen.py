# shortener_app/keygen.py

import secrets
import string

from sqlalchemy.orm import Session

from .service import crud

def create_random_key(length: int = 5) -> str:
    chars = string.ascii_uppercase + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


async def create_unique_random_key(db: Session) -> str:
    key = create_random_key()
    while True:
        if not await crud.get_db_url_by_key(db, key):
            break
        else: key = create_random_key()
    return key