from sqlalchemy import Column, Integer, String, Boolean, Float
from database import Base
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Car(Base):
    __tablename__ = "cars"
    id = Column(Integer, primary_key=True, index=True)
    brand = Column(String, index=True)
    model = Column(String)
    year = Column(Integer)
    price_per_day = Column(Float)
    image_url = Column(String)
    is_available = Column(Boolean, default=True) # Bu satırı ekle

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    car_id = Column(Integer)
    start_date = Column(String) # Normalde Date olmalı
    end_date = Column(String) # Normalde Date olmalı