from pydantic import BaseModel

# BaseModel'ler, API'deki veri alışverişini doğrulamak için kullanılır.

class CarBase(BaseModel):
    # Veritabanına kaydedeceğimiz verilerin temel yapısı
    company: str
    car_name: str
    engine: str
    total_speed: str
    performance_0_100_kmh: str
    daily_price: int
    fuel_type: str
    seats: str
    torque: str

class CarCreate(CarBase):
    # Yeni bir araba oluştururken kullanılan model
    is_available: bool = True

class Car(CarBase):
    # Veritabanından gelen veriyi doğrulamak için kullanılan model
    id: int
    is_available: bool

    class Config:
        # ORM'den gelen veriyi bu modele dönüştürmeye yarar
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