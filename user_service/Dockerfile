# Resmi Python 3.10 slim imajını kullan
FROM python:3.10-slim

# Çalışma dizinini ayarla
WORKDIR /app

# Bağımlılıkları kopyala ve kur
# Bu adım, her değişikliği yapışınızda paketin yeniden yüklenmesini engeller
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Proje dosyalarını kopyala
COPY . .

# Ortam değişkenlerini ayarla (opsiyonel ama iyi bir pratik)
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Veritabanı geçişlerini yap (migrations)
# Her build aldığında çalışır.
RUN python manage.py makemigrations
RUN python manage.py migrate

# Sunucuyu çalıştır
EXPOSE 8000
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]