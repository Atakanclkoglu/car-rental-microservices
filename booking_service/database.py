import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# Docker Compose'dan gelen ortam değişkenini okuyun
SQLALCHEMY_DATABASE_URL = os.getenv("DB_URL")

# Eğer ortam değişkeni yoksa veya boşsa hata fırlat (Bu, iyi bir pratik)
if not SQLALCHEMY_DATABASE_URL:
    raise RuntimeError("DB_URL environment variable is not set")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()