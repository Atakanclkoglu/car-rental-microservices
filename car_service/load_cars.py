import json
import psycopg2
import os

# Scriptin bulunduğu klasörden cars.json'u oku
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(BASE_DIR, "cars.json")

with open(json_path, "r", encoding="utf-8") as f:
    cars = json.load(f)

# Postgre bağlantısı
conn = psycopg2.connect(
    dbname="car_db",
    user="car_db_user",
    password="car_db_password",
    host="localhost",   # Windows hostundan bağlanıyoruz
    port=5433           # çünkü compose'ta 5433:5432 yaptın
)
cur = conn.cursor()

# Tabloyu sıfırla
cur.execute("""
DROP TABLE IF EXISTS cars;
CREATE TABLE cars (
    id INT PRIMARY KEY,
    company VARCHAR(100),
    car_name VARCHAR(100),
    engine VARCHAR(100),
    total_speed VARCHAR(50),
    performance_0_100_kmh VARCHAR(50),
    daily_price NUMERIC,
    fuel_type VARCHAR(50),
    seats VARCHAR(10),
    torque VARCHAR(50),
    is_available BOOLEAN
);
""")

# Verileri ekle
for car in cars:
    cur.execute("""
        INSERT INTO cars (id, company, car_name, engine, total_speed, performance_0_100_kmh, daily_price, fuel_type, seats, torque, is_available)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (
        car["id"],
        car["company"],
        car["car_name"],
        car["engine"],
        car["total_speed"],
        car["performance_0_100_kmh"],
        car["daily_price"],
        car["fuel_type"],
        car["seats"],
        car["torque"],
        car["is_available"]
    ))

conn.commit()
cur.close()
conn.close()

print("✅ JSON verileri başarıyla cars tablosuna yüklendi.")
