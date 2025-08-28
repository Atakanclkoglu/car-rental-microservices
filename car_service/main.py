import os
from fastapi import FastAPI, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from pydantic import BaseModel
import redis
import json

import models, schemas, database
from fastapi.middleware.cors import CORSMiddleware
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError

# --- Redis ve Elasticsearch Bağlantıları için Çevre Değişkenleri ---
ELASTIC_SEARCH_HOST = os.getenv("ELASTIC_SEARCH_HOST", "elasticsearch")
ELASTIC_SEARCH_PORT = os.getenv("ELASTIC_SEARCH_PORT", "9200")
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")

# --- Veritabanı ve Elasticsearch Bağlantıları ---
DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise ValueError("DB_URL environment variable is not set")
engine = database.engine
SessionLocal = database.SessionLocal

# Elasticsearch bağlantısı
ES_CLIENT = Elasticsearch(
    [f'http://{ELASTIC_SEARCH_HOST}:{ELASTIC_SEARCH_PORT}'],
    basic_auth=('elastic', 'elastic_pass')
)

# Redis bağlantısı
try:
    redis_client = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT, db=0, decode_responses=True)
    redis_client.ping()
    print("Redis'e başarıyla bağlanıldı.")
except redis.exceptions.ConnectionError as e:
    print(f"Redis bağlantı hatası: {e}. Uygulama Redis önbelleği olmadan çalışacak.")
    redis_client = None

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
    
    # Yeni araba eklendiğinde önbelleği temizle
    if redis_client:
        redis_client.delete("all_cars")

    return db_car

# Araçları listeleme ve filtreleme uç noktası (Elasticsearch ile güncellendi)
@app.get("/cars/", response_model=List[Car])
def get_filtered_cars(
    db: Session = Depends(database.get_db),
    car_name: Optional[str] = Query(None),
    min_price: Optional[int] = None,
    max_price: Optional[int] = None
):
    # Önbellek anahtarını belirle
    cache_key = "all_cars"
    
    # Eğer sorguda filtre yoksa doğrudan Redis'ten veriyi kontrol et
    if redis_client and not any([car_name, min_price, max_price]):
        cached_data = redis_client.get(cache_key)
        if cached_data:
            print("Veri Redis önbelleğinden döndürüldü.")
            return json.loads(cached_data)

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
            }
        )

        # Eğer hiçbir filtre yoksa, tüm verileri getir
        if not car_name and not min_price and not max_price:
            query_body["query"] = {"match_all": {}}
        
        res = ES_CLIENT.search(index="cars", body=query_body, size=10000)
        
        car_ids = [hit['_source']['id'] for hit in res['hits']['hits']]
        
        # PostgreSQL'den orijinal verileri çek
        cars = db.query(models.Car).filter(models.Car.id.in_(car_ids)).all()
        
        # Elasticsearch'teki sıralamayı koru
        car_dict = {car.id: car for car in cars}
        ordered_cars = [car_dict[id] for id in car_ids if id in car_dict]

        # Eğer sorguda filtre yoksa veriyi Redis'e yaz
        if redis_client and not any([car_name, min_price, max_price]):
            redis_client.setex(cache_key, 3600, json.dumps([Car.from_orm(car).model_dump() for car in ordered_cars]))
            print("Veri Redis önbelleğine yazıldı.")
        
        return ordered_cars

    except NotFoundError:
        return []
    except Exception as e:
        print(f"Arama hatası: {e}")
        # Hata durumunda Elasticsearch'e bağlanmadan direkt veritabanından çekme
        cars = db.query(models.Car).all()
        return cars

# Belirli bir aracı getirme uç noktası (READ)
@app.get("/cars/{car_id}", response_model=schemas.Car)
def get_car(car_id: int, db: Session = Depends(database.get_db)):
    cache_key = f"car:{car_id}"
    if redis_client:
        cached_data = redis_client.get(cache_key)
        if cached_data:
            print("Veri Redis önbelleğinden döndürüldü.")
            return Car.model_validate_json(cached_data)

    db_car = db.query(models.Car).filter(models.Car.id == car_id).first()
    if db_car is None:
        raise HTTPException(status_code=404, detail="Car not found")
        
    if redis_client:
        redis_client.setex(cache_key, 3600, Car.from_orm(db_car).model_dump_json())
    
    return db_car

# Araç silme uç noktası (DELETE)
@app.delete("/cars/{car_id}", response_model=schemas.Car)
def delete_car(car_id: int, db: Session = Depends(database.get_db)):
    db_car = db.query(models.Car).filter(models.Car.id == car_id).first()
    if db_car is None:
        raise HTTPException(status_code=404, detail="Car not found")
    
    db.delete(db_car)
    db.commit()

    # Silme işleminden sonra ilgili önbellekleri temizle
    if redis_client:
        redis_client.delete(f"car:{car_id}")
        redis_client.delete("all_cars")

    return db_car