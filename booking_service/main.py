import os
import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from database import engine, Base, get_db
from models import Booking
from config import settings

# RabbitMQ için gerekli kütüphaneler
from aio_pika import connect_robust, Message, ExchangeType
import json

# Veritabanı tablolarını oluştur
Base.metadata.create_all(bind=engine)

class BookingRequest(BaseModel):
    car_id: int
    start_date: str
    end_date: str

# RabbitMQ bağlantısı için global değişkenler
rabbitmq_connection = None
rabbitmq_channel = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global rabbitmq_connection, rabbitmq_channel
    print("RabbitMQ'ya bağlanılıyor...")
    try:
        # RabbitMQ'ya bağlan
        rabbitmq_connection = await connect_robust(
            f"amqp://guest:guest@rabbitmq:5672/"
        )
        rabbitmq_channel = await rabbitmq_connection.channel()
        print("RabbitMQ'ya başarıyla bağlanıldı.")
        
        # Kullanılacak değişim noktasını (exchange) oluştur
        exchange = await rabbitmq_channel.declare_exchange(
            "booking_exchange", ExchangeType.FANOUT, durable=True
        )

        yield
    except Exception as e:
        print(f"RabbitMQ bağlantı hatası: {e}")
        raise HTTPException(status_code=500, detail="RabbitMQ bağlantısı kurulamadı.")
    finally:
        # Uygulama kapandığında bağlantıyı kapat
        if rabbitmq_channel:
            await rabbitmq_channel.close()
        if rabbitmq_connection:
            await rabbitmq_connection.close()

app = FastAPI(lifespan=lifespan)

# CORS ayarlarını ekle
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/v1/booking/reserve", status_code=status.HTTP_201_CREATED)
async def reserve_booking(
    booking_request: BookingRequest,
    db: Session = Depends(get_db)
):
    global rabbitmq_channel
    if not rabbitmq_channel:
        raise HTTPException(status_code=500, detail="RabbitMQ kanalı mevcut değil.")

    # Yeni bir rezervasyon kaydı oluştur
    db_booking = Booking(
        car_id=booking_request.car_id,
        start_date=booking_request.start_date,
        end_date=booking_request.end_date,
        status="pending"
    )
    db.add(db_booking)
    db.commit()
    db.refresh(db_booking)

    # Mesajı bir RabbitMQ kuyruğuna gönder
    message_body = {
        "booking_id": db_booking.id,
        "car_id": booking_request.car_id,
        "start_date": booking_request.start_date,
        "end_date": booking_request.end_date
    }
    
    await rabbitmq_channel.default_exchange.publish(
        Message(body=json.dumps(message_body).encode()),
        routing_key=f"booking_{db_booking.id}"
    )

    return {"message": "Booking received and sent to RabbitMQ", "booking_id": db_booking.id}