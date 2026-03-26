## 🎯 Project Goals

- **Real-time Detection**: Identify suicide ideation and emotional distress from Reddit posts
- **Privacy-First**: Encrypt, hash, and anonymize all sensitive data
- **Compliance**: GDPR, HIPAA, and Reddit ToS adherence
- **Scalability**: Async processing for 1M+ posts
- **Interpretability**: Explainable ML predictions for clinical use

---

## 🏗️ Architecture

```
MindGuard AI Pipeline:
┌─────────────────────────────────────────┐
│  Reddit Data Layer (PRAW)               │
│  - Real-time post streaming             │
│  - Rate limit compliance (60 req/min)   │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Data Preprocessing                     │
│  - Medical-grade text cleaning          │
│  - Preserve emotional context           │
│  - Quality validation                   │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Privacy Layer                          │
│  - Hash IDs (SHA-256)                   │
│  - Encrypt at rest (AES-256)            │
│  - Audit logging                        │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  ML Model Layer                         │
│  - RoBERTa-CNN hybrid                   │
│  - Risk classification                  │
│  - Explainability scores                │
└────────────┬────────────────────────────┘
             │
             ▼
┌─────────────────────────────────────────┐
│  Streamlit Dashboard                    │
│  - Real-time risk visualization         │
│  - Intervention recommendations         │
│  - Compliance reporting                 │
└─────────────────────────────────────────┘
```

---

## 🚀 Complete Workflow: From Data to Insights

```
┌─────────────────────────────────────────────────────────────────────┐
│                    MindGuard AI - End-to-End Pipeline               │
└─────────────────────────────────────────────────────────────────────┘

Step 1: DATA COLLECTION (Reddit Scraping)
├─ scrape_medical_data.py
├─ Input: Reddit subreddits (mentalhealth, depression, anxiety)
├─ Output: medical_raw_data_YYYYMMDD.csv
└─ Features: Rate limiting, privacy hashing, quality validation

           ▼

Step 2: MODEL INFERENCE (RoBERTa-CNN)
├─ models/inference.py
├─ Input: Cleaned text from scraped posts
├─ Pre-trained Model: [Your custom model path]
├─ Output: Risk scores (0-1), Risk category (LOW/MEDIUM/HIGH/CRITICAL)
└─ Features: Batch processing, confidence scores, feature attribution

           ▼

Step 3: MONITORING & LOGGING (W&B)
├─ monitoring/wandb_logger.py
├─ Logged Metrics: Risk distribution, model accuracy, prediction latency
├─ Dashboard: Real-time model performance, data drift detection
└─ Features: Version tracking, hyperparameter logging, experiment comparison

           ▼

Step 4: VISUALIZATION & INSIGHTS (Streamlit)
├─ dashboard/streamlit_app.py
├─ Displays: Risk heatmaps, case trends, intervention recommendations
├─ Features: Real-time updates, multi-user support, export capabilities
└─ Output: Interactive reports for clinical review
```

### Quick Start - Full Pipeline

```bash
# 1. Configure credentials
cp .env.example .env
nano .env  # Add Reddit API credentials

# 2. Generate OAuth token
python get_refresh_token.py

# 3. Add your pre-trained model
# Place your model at: models/pretrained_model.pth
# Update MODEL_PATH in config.py

# 4. Configure W&B (optional but recommended)
wandb login  # Sign up at https://wandb.ai

# 5. Run complete pipeline (scrape → infer → log → visualize)
python main_pipeline.py

# 6. View results in Streamlit dashboard (new terminal)
streamlit run dashboard/streamlit_app.py
```

---

## 📁 Project Structure

```
mindguard-ai/
├── Data Layer
│   ├── config.py                    # Configuration management
│   ├── cleaner.py                   # Medical-grade text preprocessing
│   ├── scrape_medical_data.py       # Reddit data collection (Step 1)
│   ├── utils.py                     # Logging, retry logic, rate limiting
│   └── get_refresh_token.py         # OAuth token management
│
├── Model Layer
│   ├── models/
│   │   ├── pretrained_model.pth    # Your pre-trained RoBERTa-CNN model
│   │   ├── inference.py            # Model loading & inference (Step 2)
│   │   └── __init__.py
│   └── models.py                    # Pydantic data schemas
│
├── Monitoring & Logging
│   ├── monitoring/
│   │   ├── wandb_logger.py         # W&B integration (Step 3)
│   │   └── __init__.py
│   └── audit_logs/                 # Compliance logs
│
├── Visualization & Dashboard
│   ├── dashboard/
│   │   ├── streamlit_app.py        # Streamlit dashboard (Step 4)
│   │   ├── pages/
│   │   │   ├── risk_analysis.py
│   │   │   ├── model_performance.py
│   │   │   └── trends.py
│   │   └── __init__.py
│   └── data/                        # Cached predictions
│
├── Orchestration
│   ├── main_pipeline.py            # End-to-end orchestration
│   └── validate.py                 # Validation script
│
├── Configuration & Documentation
│   ├── .env.example                 # Environment template
│   ├── requirements.txt             # Python dependencies
│   ├── README.md                    # This file
│   ├── CODE_REVIEW.md              # Code analysis
│   ├── IMPLEMENTATION_SUMMARY.md   # Implementation details
│   └── .gitignore                   # Git ignore rules
```

---

## 🔒 Security & Privacy

### Data Anonymization

All sensitive data is automatically anonymized:

```python
from cleaner import DataAnonymizer

# Post IDs are hashed
hashed_id = DataAnonymizer.hash_id("abc123def456")
# Output: "7f3c8a2e4b1d9..."

# Full post anonymization
anonymized = DataAnonymizer.anonymize_post({
    "post_id": "abc123",
    "subreddit": "mentalhealth",
    "text": "I'm struggling..."
}, hash_ids=True)
```

### Encryption

```python
from cryptography.fernet import Fernet

# Generate key
key = Fernet.generate_key()

# Encrypt sensitive data
cipher = Fernet(key)
encrypted = cipher.encrypt(b"sensitive data")
```

### Audit Logging

Every data collection event is logged:

```json
{
  "timestamp": "2024-03-25T10:30:45Z",
  "event": "scrape_complete",
  "subreddit": "mentalhealth",
  "posts_collected": 500,
  "valid": 480,
  "filtered": 20
}
```

---

## 📊 Data Quality Validation

The pipeline includes multiple quality checks:

```python
from cleaner import QualityValidator

# Validate post quality
is_valid = QualityValidator.is_valid_post(
    text="I've been struggling with depression for years...",
    min_words=10,
    max_words=5000
)

# Returns: True (480 words, not repetitive)
```

**Filters applied:**
- Minimum 10 words (customizable)
- Maximum 5000 words
- Content must be >30% unique words (prevents spam)
- Excludes [deleted] and [removed] posts

---

## 🛑 Error Handling & Resilience

### Exponential Backoff

Automatic retry with exponential backoff for transient failures:

```python
from utils import retry_with_backoff

@retry_with_backoff(max_retries=5, initial_delay=2.0)
def call_api():
    # Automatically retries with exponential delays
    # Attempt 1: 2s delay
    # Attempt 2: 4s delay
    # Attempt 3: 8s delay
    pass
```

### Rate Limiting

Complies with Reddit's 60 requests/minute limit:

```python
from utils import RateLimiter

limiter = RateLimiter(max_requests=60, window_seconds=60)

for post in posts:
    limiter.wait_if_needed()  # Waits if at limit
    process_post(post)
```

---
## ⚖️ Compliance & Ethics

### GDPR Compliance
- ✅ Data minimization (only necessary fields)
- ✅ Right to be forgotten (auto-purge after 90 days)
- ✅ Explicit consent documentation
- ✅ Data breach notification system

### HIPAA Compliance (if applicable)
- ✅ Encryption at rest (AES-256)
- ✅ Encryption in transit (TLS 1.2+)
- ✅ Access logging
- ✅ Role-based access control

### Ethical Considerations
- ⚠️ **Limitation**: No active intervention (observational only)
- ⚠️ **Disclosure**: Users should be informed of monitoring
- ⚠️ **Bias**: Regular audits for demographic bias needed
- ⚠️ **IRB Review**: Mental health research requires ethical approval

---

## 📋 Compliance Checklist

Before deployment:

- [ ] GDPR: Data minimization documented
- [ ] GDPR: Retention policy enforced
- [ ] HIPAA: Encryption enabled
- [ ] HIPAA: Audit logging verified
- [ ] Reddit ToS: User consent mechanism in place
- [ ] Ethical: IRB review completed
- [ ] Security: Credentials properly managed
- [ ] Security: Rate limits respected
- [ ] Testing: Full test coverage >80%
- [ ] Monitoring: Structured logging validated


## 🙏 Acknowledgments

- **PRAW**: Python Reddit API Wrapper
- **Transformers**: Hugging Face NLP library
- **RoBERTa**: Facebook's improved BERT model
- Reddit community for rich mental health discussions

---

**Last Updated**: March 25, 2024  
**Status**: Data vilidation onging
**Version**: 1.0.0
