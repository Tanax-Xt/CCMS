from typing import Final

from decouple import config

DEBUG: Final[bool] = config("DEBUG", default=False, cast=bool)
DATABASE_URL: Final[str] = config("DATABASE_URL", default="sqlite:///db.sqlite3")
