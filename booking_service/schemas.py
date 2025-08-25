# booking_service/schemas.py

from pydantic import BaseModel

class BookingBase(BaseModel):
    user_id: int
    car_id: int
    start_date: str
    end_date: str

class BookingCreate(BookingBase):
    pass

class Booking(BookingBase):
    id: int
    status: str

    class Config:
        orm_mode = True