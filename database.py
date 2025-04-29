from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base




SQLALCHEMY_DATABASE_URL = "postgresql://postgres:password@localhost/course-back"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    pool_recycle=3600,
    echo=True  # Для отладки SQL-запросов
)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    try:
        with engine.connect() as conn:
            print("✅ Подключение к PostgreSQL успешно установлено!")
    except Exception as e:
        print(f"❌ Ошибка подключения к PostgreSQL: {e}")
