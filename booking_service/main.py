import sys
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import date, datetime
from contextlib import asynccontextmanager
import asyncio
from kafka import KafkaProducer, KafkaConsumer
import json
import uuid
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# Projenizin ana dizinine erişim yolu ekler
sys.path.append('..')
from database import models, database, engine

# Veritabanı tablolarını oluşturma
models.Base.metadata.create_all(bind=engine)

# Kafka producer ayarları
producer = KafkaProducer(
    bootstrap_servers='kafka:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

# Kafka consumer'ı arka planda çalıştıracak asenkron fonksiyon
async def consume_bookings():
    consumer = KafkaConsumer(
        'booking-requests',
        bootstrap_servers='kafka:9092',
        auto_offset_reset='earliest',
        enable_auto_commit=True,
        group_id='booking-group-1',
        value_deserializer=lambda x: json.loads(x.decode('utf-8'))
    )

    for message in consumer:
        booking_details = message.value
        print(f"\n--- Yeni rezervasyon isteği alındı: {booking_details['request_id']} ---")
    
        db = next(database.get_db())
        
        try:
            new_start = datetime.strptime(booking_details.get("start_date"), "%Y-%m-%d").date()
            new_end = datetime.strptime(booking_details.get("end_date"), "%Y-%m-%d").date()
            car_id = booking_details.get("car_id")
            request_id = booking_details.get("request_id")

            # Rezervasyon çakışması kontrolü
            existing_booking = db.query(models.Booking).filter(
                models.Booking.car_id == car_id,
                models.Booking.start_date < new_end,
                models.Booking.end_date > new_start
            ).first()

            if existing_booking:
                db.query(models.BookingStatus).filter_by(request_id=request_id).update({"status": models.BookingStatusEnum.failed})
                db.commit()
                print(f"HATA: {request_id} - Araba müsait değil.")
                
            else:
                new_booking = models.Booking(
                    user_id=booking_details.get("user_id"),
                    car_id=car_id,
                    start_date=new_start,
                    end_date=new_end,
                    request_id=request_id
                )
                db.add(new_booking)
                db.query(models.BookingStatus).filter_by(request_id=request_id).update({"status": models.BookingStatusEnum.confirmed})
                db.commit()
                print(f"BAŞARILI: {request_id} - Rezervasyon onaylandı.")
                
        except Exception as e:
            print(f"Veritabanı işlemi sırasında hata oluştu: {e}")
            db.rollback()
        finally:
            db.close()

# FastAPI uygulamasının yaşam döngüsü yönetimi
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Booking Consumer başlatılıyor...")
    consumer_task = asyncio.create_task(consume_bookings())
    yield
    print("Booking Consumer durduruluyor...")
    consumer_task.cancel()
    await consumer_task

app = FastAPI(lifespan=lifespan)

# CORS ayarları
origins = [
    "http://localhost",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Frontend'den gelecek verinin yapısını tanımla
class BookingRequest(BaseModel):
    user_id: int
    car_id: int
    start_date: date
    end_date: date

@app.get("/")
def read_root():
    return {"message": "Booking Service ayakta!"}

# Yeni rezervasyon endpoint'i (Kafka üretici rolü)
@app.post("/api/v1/booking/reserve")
def reserve_car(request: BookingRequest, db: Session = Depends(database.get_db)):
    request_id = str(uuid.uuid4())
    booking_details = {
        "user_id": request.user_id,
        "car_id": request.car_id,
        "start_date": request.start_date.isoformat(),
        "end_date": request.end_date.isoformat(),
        "request_id": request_id
    }
    
    # İlk olarak "beklemede" (pending) durumunu veritabanına kaydet
    initial_status = models.BookingStatus(request_id=request_id, status=models.BookingStatusEnum.pending)
    db.add(initial_status)
    db.commit()
    db.refresh(initial_status)
    
    # İsteği Kafka'ya gönder
    producer.send('booking-requests', booking_details)
    
    return {"message": "Rezervasyon isteğiniz işleme alındı.", "request_id": request_id}

# Rezervasyon durumunu kontrol eden API uç noktası
@app.get("/api/v1/booking/status/{request_id}")
def get_booking_status(request_id: str, db: Session = Depends(database.get_db)):
    status_record = db.query(models.BookingStatus).filter_by(request_id=request_id).first()
    
    if not status_record:
        raise HTTPException(status_code=404, detail="Durum kaydı bulunamadı.")
    
    return {"status": status_record.status}