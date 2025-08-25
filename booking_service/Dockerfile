#Resmi python imajını al
FROM python:3.11-slim

#Çalışma dizinini ayarla
WORKDIR /app

# Gereksinimleri kopyala ve yükle
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodunu kopyala
COPY . .

# PostgreSQL portu varsayılan olarak 5432'dir, ama biz veritabanına sadece bu service'ten erişeceğiz.
# Django development server 8000 portunu kullanır.
EXPOSE 8001

# Geliştirme sunucusunu çalıştır
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]