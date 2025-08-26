from sqlalchemy import Column, Integer, String, Boolean, Float
from database import Base
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Car(Base):
    __tablename__ = "cars"
    id = Column(Integer, primary_key=True, index=True)
    company = Column(String, index=True)
    car_name = Column(String)
    engine = Column(String)
    total_speed = Column(String)
    performance_0_100_kmh = Column(String)
    daily_price = Column(Integer)  # JSON'a göre Float yerine Integer
    fuel_type = Column(String)
    seats = Column(String)
    torque = Column(String)
    is_available = Column(Boolean, default=True)

class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    car_id = Column(Integer)
    start_date = Column(String)
    end_date = Column(String)