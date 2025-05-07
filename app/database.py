from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base




SQLALCHEMY_DATABASE_URL = "postgresql://neondb_owner:npg_iN6YPZt1AVFO@ep-patient-thunder-a42wemnt-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    echo=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    try:
        with engine.connect() as conn:
            print("Подключение к PostgreSQL успешно установлено")
    except Exception as e:
        print(f"Ошибка подключения к PostgreSQL: {e}")
