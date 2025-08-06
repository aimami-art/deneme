# 🧠 AI Satış Stratejisi Projesi

## 📋 Proje Açıklaması

Web tabanlı yapay zeka destekli satış stratejisi geliştirme platformu. Satıcıların ürün bilgilerini girerek AI tarafından oluşturulan veri temelli satış stratejileri alabilecekleri ve satış sonuçlarını değerlendirip yeni stratejiler alabilecekleri kapsamlı bir sistem.

## 🏗️ Sistem Mimarisi

### Ana Modüller:
- **MarketAnalyzer**: Pazar ve rekabet analizi
- **CustomerSegmenter**: Hedef kitle analizi ve segmentasyon
- **PricingAdvisor**: Fiyatlandırma ve promosyon stratejisi
- **MessagingGenerator**: İçerik ve mesajlaşma stratejisi
- **StrategyBuilder**: Merkezi strateji motoru
- **RAG & EmbeddingEngine**: Vektör tabanlı strateji arama
- **MCP Communication Layer**: Model Context Protocol entegrasyonu
- **Google A2A Agent Network**: Agent-to-Agent iletişim sistemi

## 🛠️ Teknoloji Stack

### Backend:
- **FastAPI**: Web framework
- **PostgreSQL**: Ana veritabanı
- **Redis**: Cache ve session yönetimi
- **SQLAlchemy**: ORM
- **Alembic**: Database migration

### AI & ML:
- **Google Gemini 2.5 Pro**: Ana LLM
- **LangChain**: AI framework
- **LangGraph**: Agent orchestration
- **Pinecone**: Vector database
- **SentenceTransformers**: Embedding

### Frontend:
- **HTML5/CSS3/JavaScript**: Modern web teknolojileri
- **Responsive Design**: Mobil uyumlu tasarım

## 🚀 Kurulum ve Çalıştırma

### Ön Gereksinimler:
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- Git

### 1. Projeyi Klonlayın:
```bash
git clone <repository-url>
cd yarismaci
```

### 2. Virtual Environment Oluşturun:
```bash
python -m venv venv
```

### 3. Virtual Environment'ı Aktifleştirin:

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

### 4. Bağımlılıkları Yükleyin:
```bash
pip install -r requirements.txt
```

### 5. Environment Dosyasını Oluşturun:
```bash
cp .env.example .env
```

`.env` dosyasını düzenleyerek API anahtarlarınızı ekleyin:
```env
# API Keys
GEMINI_API_KEY=your-gemini-api-key
SERPAPI_KEY=your-serpapi-key
PINECONE_API_KEY=your-pinecone-api-key
PINECONE_ENVIRONMENT=your-pinecone-environment

# Database
DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_satis_db

# Redis
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-super-secret-key-change-this-in-production
```

### 6. Veritabanını Hazırlayın:

**PostgreSQL'de veritabanı oluşturun:**
```sql
CREATE DATABASE ai_satis_db;
```

**Alembic migration'ları çalıştırın:**
```bash
alembic upgrade head
```

### 7. Uygulamayı Başlatın:
```bash
uvicorn app.main:app --reload
```

Uygulama http://localhost:8000 adresinde çalışacaktır.

## 🐳 Docker ile Çalıştırma

### Docker Compose ile:
```bash
docker-compose up -d
```

Bu komut PostgreSQL, Redis ve FastAPI uygulamasını otomatik olarak başlatır.

## 📊 API Dokümantasyonu

Uygulama çalıştıktan sonra aşağıdaki adreslerde API dokümantasyonuna erişebilirsiniz:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🧪 Test Etme

```bash
pytest
```

## 📁 Proje Yapısı

```
yarismaci/
├── app/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints/
│   ├── core/
│   │   ├── config.py
│   │   └── database.py
│   ├── models/
│   │   ├── user.py
│   │   ├── product.py
│   │   └── strategy.py
│   ├── schemas/
│   │   └── auth.py
│   ├── services/
│   │   └── auth_service.py
│   ├── static/
│   │   ├── css/
│   │   └── js/
│   ├── templates/
│   │   └── index.html
│   └── main.py
├── alembic/
├── requirements.txt
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── README.md
```

## 🔧 Geliştirme

### Code Formatting:
```bash
black app/
isort app/
```

### Migration Oluşturma:
```bash
alembic revision --autogenerate -m "Migration açıklaması"
alembic upgrade head
```

## 📈 Özellikler

### ✅ Tamamlanan:
- [x] Temel proje yapısı
- [x] FastAPI backend konfigürasyonu
- [x] PostgreSQL veritabanı modelleri
- [x] JWT authentication sistemi
- [x] Docker konfigürasyonu
- [x] Temel frontend (HTML/CSS/JS)
- [x] API dokümantasyonu

### 🔄 Devam Eden:
- [ ] AI modüllerinin implementasyonu
- [ ] MCP protokol entegrasyonu
- [ ] Google A2A agent sistemi
- [ ] Pinecone vector database entegrasyonu
- [ ] Frontend dashboard geliştirme

### 📋 Planlanan:
- [ ] Gemini API entegrasyonu
- [ ] SerpAPI entegrasyonu
- [ ] Google Trends analizi
- [ ] Strateji üretim motoru
- [ ] Performans takip sistemi

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/AmazingFeature`)
3. Değişikliklerinizi commit edin (`git commit -m 'Add some AmazingFeature'`)
4. Branch'inizi push edin (`git push origin feature/AmazingFeature`)
5. Pull Request oluşturun

## 📄 Lisans

Bu proje MIT lisansı altında lisanslanmıştır.

## 📞 İletişim

Proje hakkında sorularınız için issue açabilirsiniz.

---

*Bu proje, küçük ve orta ölçekli işletmelerin rekabet gücünü artırmak için AI destekli, veriye dayalı satış stratejileri sunan erişilebilir bir platform olarak geliştirilmektedir.*


