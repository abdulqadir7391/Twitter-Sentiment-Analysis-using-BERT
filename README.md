# Twitter Sentiment Analysis (BERT)

## Setup
1. Clone this repo.
2. Copy `.env.example` to `.env` and fill in environment variables.
3. Install dependencies:
pip install -r requirements.txt

4. If using local MongoDB, ensure it is running. Or set MONGO_URI to your Atlas URI.
## Run collector (polling)
python collector.py


## Streamlit dashboard
streamlit run streamlit_app.py


## FastAPI backend
uvicorn api:app --reload --port 8000


## Generate daily report manually
python report.py
