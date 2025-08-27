import os
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from pydantic import BaseModel

import models, schemas, database
from fastapi.middleware.cors import CORSMiddleware
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError


# --- Veritabanı ve Elasticsearch Bağlantıları ---
DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise ValueError("DB_URL environment variable is not set")
engine = database.engine
SessionLocal = database.SessionLocal

# Elasticsearch bağlantısı
ES_CLIENT = Elasticsearch(
    ['http://elasticsearch:9200'], 
    basic_auth=('elastic', 'elastic_pass')
)

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
models.Base.metadata.create_all(bind=engine)

# Pydantic modeli
class Car(BaseModel):
    id: int
    car_name: str
    company: str
    daily_price: float
    engine: str
    fuel_type: str
    description: Optional[str] = None
    
    class Config:
        from_attributes = True

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

# Araçları listeleme ve filtreleme uç noktası (Elasticsearch ile güncellendi)
@app.get("/cars/", response_model=List[Car])
def get_filtered_cars(
    db: Session = Depends(database.get_db),
    car_name: Optional[str] = Query(None),
    min_price: Optional[int] = None,
    max_price: Optional[int] = None
):
    try:
        query_body = {
            "query": {
                "bool": {
                    "must": [],
                    "filter": []
                }
            }
        }
        
        if car_name:
            query_body["query"]["bool"]["must"].append({
                "match": {
                    "company": {
                        "query": car_name,
                        "fuzziness": "AUTO"
                    }
                }
            })
            
        price_range = {}
        if min_price is not None:
            price_range["gte"] = min_price
        if max_price is not None:
            price_range["lte"] = max_price

        if price_range:
            query_body["query"]["bool"]["filter"].append({
                "range": {
                    "daily_price": price_range
                }
            })

        res = ES_CLIENT.search(index="cars", body=query_body, size=10000)
        
        car_ids = [hit['_source']['id'] for hit in res['hits']['hits']]
        
        # PostgreSQL'den orijinal verileri çek (burada sadece id'ler üzerinden çekim yapıyoruz)
        cars = db.query(models.Car).filter(models.Car.id.in_(car_ids)).all()
        
        # Elasticsearch'teki sıralamayı koru
        car_dict = {car.id: car for car in cars}
        ordered_cars = [car_dict[id] for id in car_ids if id in car_dict]

        return ordered_cars

    except NotFoundError:
        return []

    except Exception as e:
        print(f"Arama hatası: {e}")
        raise HTTPException(status_code=500, detail="Arama sırasında bir hata oluştu.")

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