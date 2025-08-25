# booking_service/main.py

from fastapi import FastAPI, HTTPException
from datetime import date
from pydantic import BaseModel
import httpx
from fastapi.middleware.cors import CORSMiddleware # CORSMiddleware'i import et


app = FastAPI()

# CORS ayarları
origins = [
    "http://localhost",
    "http://localhost:3000", # Frontend'inizin çalıştığı adres
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # Tüm metodlara izin ver (GET, POST, vb.)
    allow_headers=["*"], # Tüm başlıklara izin ver
)

# Frontend'den gelecek verinin yapısını tanımla
class BookingRequest(BaseModel):
    car_id: int
    start_date: date
    end_date: date

@app.post("/calculate-price")
async def calculate_booking_price(booking_request: BookingRequest):
    # Başlangıç ve bitiş tarihi arasındaki gün sayısını hesapla
    day_count = (booking_request.end_date - booking_request.start_date).days + 1
    if day_count <= 0:
        raise HTTPException(status_code=400, detail="Geçersiz tarih aralığı. - Lütfen doğru tarih aralığını girin.")
    
    # Car-service'den aracın günlük fiyatını al
    car_service_url = "http://car-service:8001/cars/"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{car_service_url}{booking_request.car_id}")
            response.raise_for_status() 
            car_details = response.json()
            daily_rate = car_details.get("price_per_day")

            if daily_rate is None:
                raise HTTPException(status_code=404, detail="Araba bulunamadı.")
            
    except httpx.HTTPStatusError as exc:
        raise HTTPException(status_code=exc.response.status_code, detail="Car-service'den veri alınamadı.")
    except httpx.RequestError:
        raise HTTPException(status_code=500, detail="Car-service'e bağlanılamadı.")

    # Toplam fiyatı hesapla
    total_price = day_count * daily_rate
    
    return {
        "total_price": total_price,
        "car_id": booking_request.car_id,
        "day_count": day_count
    }