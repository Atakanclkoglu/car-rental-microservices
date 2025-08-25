# booking_service/models.py

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from database import Base

class Booking(Base):
    __tablename__ = "bookings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)  # Kullanıcı servisi ile ilişki
    car_id = Column(Integer)    # Araba servisi ile ilişki
    start_date = Column(String)
    end_date = Column(String)
    status = Column(String, default="pending") # Örnek: "pending", "confirmed", "cancelled"