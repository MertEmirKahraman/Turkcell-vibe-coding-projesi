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
backend/app/models/       SQLAlchemy kullanıcı, abonelik, dükkân ve sipariş modelleri
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

### Dükkân keşfi API'si

- `GET /api/v1/shops`: Aktif dükkânları listeler. `search` parametresi ad veya adreste arama yapar.
- `GET /api/v1/shops?latitude=39.919870&longitude=32.853241`: Dükkânları kullanıcının konumuna göre en yakından uzağa sıralar.
- `radius_km` parametresiyle yakınlık mesafesi sınırlandırılabilir; örneğin `radius_km=5`.
- `GET /api/v1/shops/{shop_id}`: Dükkân detaylarını ve aktif ürün menüsünü getirir.

### Sipariş API'si

- `POST /api/v1/orders`: Aktif aboneliği olan müşteri için bir kahve siparişi oluşturur ve QR JSON'u döndürür.
- `GET /api/v1/orders/history` ve `GET /api/v1/orders/{order_id}`: Müşterinin siparişlerini takip etmesini sağlar.
- `GET /api/v1/orders/shop`: Dükkân sahibinin kendi dükkânlarına gelen siparişleri listeler.
- `PATCH /api/v1/orders/{order_id}/status`: Siparişi `ACCEPTED`, `PREPARING` ve `READY` durumlarına geçirir.
- `POST /api/v1/orders/{order_id}/verify-qr` QR imzasını denetler; `POST /api/v1/orders/{order_id}/redeem` geçerli QR ile hazır siparişi teslim eder.
- Test dükkân sahibi hesabı `05557654321` numarasıyla OTP (`1234`) üzerinden giriş yapar. Seed verilerini yenilemek için depo kökünde `python -m backend.scripts.seed_data` çalıştırın.

## Frontend'i çalıştırma

Yeni bir PowerShell terminali açıp depo kök klasöründen çalıştırın:

```powershell
cd frontend
npm.cmd install
npm.cmd run dev
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
- Faz 3 tamamlandı: SQLite tabloları ve seed verileri; GSM/OTP ile giriş ve JWT; abonelik planları ve Paycell ödeme simülasyonu; dükkân arama/konum API'leri; kahve hakkı kontrolü, sipariş durumları ve HMAC imzalı QR teslimatı.
- Faz 4 tamamlandı: React + TypeScript + Vite sayfaları, API istemcisi, Leaflet dükkân haritası, müşteri akışları ve dükkân sahibi sipariş paneli/kamera QR tarayıcısı eklendi; arayüz lacivert, mavi ve altın tonlarında premium temayla güncellendi.
- Uçtan uca doğrulama: Müşteri giriş yaptı, abonelik hakkıyla sipariş verdi ve QR aldı; dükkân sahibi siparişi kabul etti, hazırladı ve QR imzasını doğrulayarak teslim etti.
- Kalite kontrolleri: 12 backend testi geçti; frontend production build ve lint başarılı. Kamera kullanılamadığında QR JSON içeriği elle girilebilir.
- Mevcut durum: Temel KahveCell demo akışı tamamlandı ve çalışır durumda. Gerçek SMS/ödeme altyapısı ve canlıya alma ayarları kapsam dışıdır.
