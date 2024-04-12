from typing import Final

from sqlmodel import create_engine
from sqlalchemy.future.engine import Engine

from app.config import DEBUG, DATABASE_URL

ENGINE: Final[Engine] = create_engine(DATABASE_URL, echo=DEBUG)
