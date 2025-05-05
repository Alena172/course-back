from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
import os
import time
from sqlalchemy.exc import OperationalError

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@db/course-back")

def create_engine_with_retry():
    retries = 5
    for i in range(retries):
        try:
            engine = create_engine(
                SQLALCHEMY_DATABASE_URL,
                pool_size=10,
                max_overflow=20,
                pool_timeout=30,
                pool_recycle=3600,
                echo=True
            )
            # Test the connection
            with engine.connect() as conn:
                print("✅ Подключение к PostgreSQL успешно установлено!")
            return engine
        except OperationalError as e:
            if i == retries - 1:
                raise
            wait_time = 2 ** i
            print(f"⚠️ Ошибка подключения к PostgreSQL (попытка {i + 1}/{retries}), повтор через {wait_time} сек...")
            time.sleep(wait_time)

engine = create_engine_with_retry()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()