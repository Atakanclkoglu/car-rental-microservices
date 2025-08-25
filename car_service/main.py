from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
import models, schemas, database
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Frontend'in adresini belirtir, geliştirme için "*" her adrese izin verir
    allow_credentials=True,
    allow_methods=["*"], # Tüm metodlara (GET, POST, vs.) izin ver
    allow_headers=["*"], # Tüm başlıklara izin ver
)


models.Base.metadata.create_all(bind=database.engine)

@app.get("/")
def read_root():
    return {"message": "Welcome to the Car Service API"}

# Araç ekleme uç noktası (CREATE)
@app.post("/cars/", response_model=schemas.Car)
def create_car(car: schemas.CarCreate, db: Session = Depends(database.get_db)):
    db_car = models.Car(**car.dict())
    db.add(db_car)
    db.commit()
    db.refresh(db_car)
    return db_car

# Araçları listeleme uç noktası (READ)
@app.get("/cars/", response_model=list[schemas.Car])
def get_cars(db: Session = Depends(database.get_db)):
    cars = db.query(models.Car).all()
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