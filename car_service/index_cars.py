import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk

import models

# PostgreSQL veritabanı bağlantısı
DB_URL = os.getenv("DB_URL")
if not DB_URL:
    raise ValueError("DB_URL environment variable is not set")
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Elasticsearch bağlantısı
ES_CLIENT = Elasticsearch(
    ['http://elasticsearch:9200'], 
    basic_auth=('elastic', 'elastic_pass')
)

def get_cars_from_db():
    db = SessionLocal()
    try:
        cars = db.query(models.Car).all()
        return cars
    finally:
        db.close()

def generate_actions(cars):
    """Her araç için Elasticsearch'e gönderilecek eylem (action) oluşturur."""
    for car in cars:
        doc = {
            '_index': 'cars',
            '_id': car.id,
            '_source': {
                'id': car.id,
                'company': car.company,
                'car_name': car.car_name,
                'engine': car.engine,
                'total_speed': car.total_speed,
                'performance_0_100_kmh': car.performance_0_100_kmh,
                'daily_price': car.daily_price,
                'fuel_type': car.fuel_type,
                'seats': car.seats,
                'torque': car.torque,
                'is_available': car.is_available
            }
        }
        yield doc

def main():
    print("PostgreSQL'den araçlar çekiliyor...")
    cars = get_cars_from_db()

    print(f"Toplam {len(cars)} araç bulundu. Elasticsearch'e indeksleniyor...")
    
    # İndeksi kontrol et ve yoksa oluştur
    if not ES_CLIENT.indices.exists(index='cars'):
        ES_CLIENT.indices.create(index='cars')
        print("Yeni 'cars' indeksi oluşturuldu.")
    
    # Toplu (bulk) indeksleme işlemi
    try:
        success, failed = bulk(ES_CLIENT, generate_actions(cars), stats_only=True)
        print(f"İndeksleme tamamlandı. Başarılı: {success}, Başarısız: {failed}")
    except Exception as e:
        print(f"Hata oluştu: {e}")

if __name__ == "__main__":
    main()