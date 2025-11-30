# 🧠 Twitter Sentiment Analysis using BERT

This project performs **real-time sentiment analysis on tweets** using a fine-tuned **BERT-based model**.  
The system collects live tweets, analyzes emotional tone, stores results, visualizes trends, and generates automated reports.

---

## 🚀 Features

- 📡 Real-time Twitter data collection
- 🧠 BERT-based sentiment classification
- 🗄 MongoDB storage with CSV fallback mode
- 📊 Interactive dashboard (Streamlit)
- 🔌 FastAPI backend with JSON endpoints
- 🧾 Daily report generator (CSV + PDF)
- 🚨 Email alert system for harmful keywords

---

## 📦 Installation

### 1️⃣ Clone the repository:

```bash
git clone https://github.com/YOUR-USERNAME/Twitter-Sentiment-BERT.git
cd Twitter-Sentiment-BERT

2️⃣ Install dependencies:
pip install -r requirements.txt

3️⃣ Create .env file
Copy the example file:
cp env.example .env

Fill in your:
Twitter API bearer token
MongoDB URI
Email credentials (optional)

▶️ Usage
📡 Run Tweet Collector:
python collector.py

📊 Run Streamlit Dashboard:
streamlit run streamlit_app.py

🔌 Run API Server:
uvicorn api:app --reload --port 8000

🧾 Generate Daily Report:
python report.py

📁 Project Structure
├── api.py                   → FastAPI backend
├── classifier.py            → BERT inference
├── collector.py             → Tweet collection loop
├── dashboard.py             → Visualization logic
├── streamlit_app.py         → Streamlit user dashboard
├── report.py                → PDF/CSV reporting
├── db.py                    → MongoDB/CSV storage handler
├── utils.py                 → Helpers (cleaning, email alerts)
├── requirements.txt         → Dependencies
├── notebooks/              → Optional ML training files
└── .env.example            → Template ENV file

🌍 API Endpoints
Method	Route	Description
GET	/stats	Aggregated sentiment counts
GET	/tweets	Returns recent tweets
GET	/tweets?sentiment=Positive	Filter tweets
🧪 Model

The default classifier uses:
nlptown/bert-base-multilingual-uncased-sentiment
You may swap with any HuggingFace transformer by editing:

MODEL_NAME in classifier.py
