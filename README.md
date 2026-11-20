# KahveCell

KahveCell, operatör abonelerinin abonelik haklarıyla anlaşmalı kahve dükkânlarından sipariş verebildiği dijital platformdur.

## Teknoloji yığını

- Backend: Python 3.12, FastAPI, SQLAlchemy, SQLite
- Frontend: React, TypeScript, Vite
- Harita: Leaflet, React Leaflet

Backend ve frontend ayrı projelerdir; frontend backend'e HTTP API üzerinden bağlanır.

## Proje yapısı

```text
backend/app/api/v1/       Sürüm kontrollü FastAPI endpoint'leri
backend/app/core/         Ortam ayarları ve ortak hata yanıtları
backend/app/db/           SQLAlchemy engine, session ve Base
backend/app/models/       Veritabanı modelleri (faz 3'te eklenecek)
backend/app/repositories/ Veritabanı erişim katmanı
backend/app/schemas/      İstek ve yanıt şemaları
backend/app/services/     İş kuralları
backend/tests/            Backend testleri
frontend/src/api/         Backend API istemcisi
frontend/src/components/  Tekrar kullanılabilir arayüz bileşenleri
frontend/src/features/    İşlev bazlı arayüz parçaları
frontend/src/pages/       Sayfa bileşenleri
frontend/src/types/       Ortak TypeScript tipleri
README.md                 Kurulum yönergeleri ve ilerleme günlüğü
```

## Gereksinimler

- Python 3.12
- Node.js LTS ve npm

## Backend'i çalıştırma

Komutları depo kök klasöründe çalıştırın.

### Windows PowerShell

```powershell
py -3.12 -m venv backend/.venv
backend\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
Copy-Item backend/.env.example backend/.env
backend\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --reload
```

### macOS / Linux

```bash
python3 -m venv backend/.venv
backend/.venv/bin/python -m pip install -r backend/requirements.txt
cp backend/.env.example backend/.env
backend/.venv/bin/python -m uvicorn backend.app.main:app --reload
```

API sağlık kontrolü: <http://127.0.0.1:8000/api/v1/health>
Swagger arayüzü: <http://127.0.0.1:8000/docs>

## Frontend'i çalıştırma

Yeni bir terminal açıp depo kök klasöründen çalıştırın:

```bash
cd frontend
npm install
npm run dev
```

Vite geliştirme sunucusu varsayılan olarak <http://localhost:5173> adresinde açılır.
Frontend API adresi `frontend/.env` içindeki `VITE_API_BASE_URL` ile değiştirilebilir; örnek değer için `frontend/.env.example` dosyasına bakın.

## Testler

Depo kökünden:

```bash
backend/.venv/Scripts/python.exe -m pytest backend/tests
```

macOS / Linux:

```bash
backend/.venv/bin/python -m pytest backend/tests
```

## İlerleme günlüğü

- Faz 1 tamamlandı: Ürün kapsamı ve teknoloji tercihleri belirlendi.
- Faz 2 tamamlandı: Backend ve frontend bağımsız scaffold'lara ayrıldı; FastAPI ayarları, API v1, standart başarı/hata yanıtları, SQLite session dependency'si ve React API client kuruldu.
- Faz 2 doğrulaması: Frontend health ekranı backend endpoint'ine bağlanır; backend testleri, frontend lint ve production build kontrolleri geçer.
- Henüz tamamlanmadı: Kimlik doğrulama, abonelikler, dükkân keşfi, harita ekranı, sipariş akışı ve QR teslimatı.
- Sıradaki faz: Veritabanı modelleri, migration ve seed verileri.
