import os
import time
import sys
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError

DB_URL = os.getenv("SQLALCHEMY_DATABASE_URL")
max_tries = 30

for i in range(max_tries):
    try:
        engine = create_engine(DB_URL)
        with engine.connect():
            print("Successfully connected to database!")
            sys.exit(0)
    except OperationalError as e:
        if i == max_tries - 1:
            print(f"Failed to connect to DB after {max_tries} attempts: {e}", file=sys.stderr)
            sys.exit(1)
        time.sleep(1)