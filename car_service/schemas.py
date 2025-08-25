from pydantic import BaseModel

class CarBase(BaseModel):
    brand: str
    model: str
    year: int
    price_per_day: float
    image_url:str

class CarCreate(CarBase):
    is_available: bool = True

class Car(CarBase):
    id: int
    is_available: bool

    class Config:
        orm_mode = True

class BookingBase(BaseModel):
    user_id: int
    car_id: int
    start_date: str
    end_date: str

class Booking(BookingBase):
    id: int

    class Config:
        orm_mode = True