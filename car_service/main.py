from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func # Gerekli import'lar
from typing import List, Optional # Gerekli import'lar

import models, schemas, database
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS ayarları
origins = [
    "http://localhost",
    "http://localhost:3000",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Veritabanı tablolarını oluştur
models.Base.metadata.create_all(bind=database.engine)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Car Service API"}

# Araç ekleme uç noktası (CREATE)
@app.post("/cars/", response_model=schemas.Car)
def create_car(car: schemas.CarCreate, db: Session = Depends(database.get_db)):
    db_car = models.Car(**car.model_dump())
    db.add(db_car)
    db.commit()
    db.refresh(db_car)
    return db_car

# Araçları listeleme ve arama uç noktası (TEK BİR ADRES)
@app.get("/cars/", response_model=List[schemas.Car])
def get_all_cars(db: Session = Depends(database.get_db), q: Optional[str] = None):
    # Eğer bir arama sorgusu varsa (q parametresi boş değilse)
    if q:
        search = f"%{q.lower()}%"
        cars_query = db.query(models.Car).filter(
            or_(
                func.lower(models.Car.car_name).ilike(search),
                func.lower(models.Car.company).ilike(search),
                func.lower(models.Car.engine).ilike(search),
                func.lower(models.Car.fuel_type).ilike(search)
            )
        )
    # Eğer arama sorgusu yoksa, tüm arabaları döndür
    else:
        cars_query = db.query(models.Car)
    
    cars = cars_query.all()
    return cars

# Belirli bir aracı getirme uç noktası (READ)
@app.get("/cars/{car_id}", response_model=schemas.Car)
def get_car(car_id: int, db: Session = Depends(database.get_db)):
    db_car = db.query(models.Car).filter(models.Car.id == car_id).first()
    if db_car is None:
        raise HTTPException(status_code=404, detail="Car not found")
    return db_car

# Araç silme uç noktası (DELETE)
@app.delete("/cars/{car_id}", response_model=schemas.Car)
def delete_car(car_id: int, db: Session = Depends(database.get_db)):
    db_car = db.query(models.Car).filter(models.Car.id == car_id).first()
    if db_car is None:
        raise HTTPException(status_code=404, detail="Car not found")
    db.delete(db_car)
    db.commit()
    return db_car