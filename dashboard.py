import os
import pandas as pd
import streamlit as st
import plotly.express as px
from pymongo import MongoClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ----------------------
# Load Config
# ----------------------
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "twitter_db")
MONGO_COLLECTION = os.getenv("MONGO_COLLECTION", "tweets")
CSV_FALLBACK_PATH = os.getenv("CSV_FALLBACK_PATH", "./tweets_fallback.csv")

# ----------------------
# Load Data Function
# ----------------------
@st.cache_data(ttl=60)  # refresh every 60 seconds
def load_data():
    """Loads data from MongoDB, with a fallback to CSV."""
    try:
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=2000)
        db = client[MONGO_DB]
        collection = db[MONGO_COLLECTION]
        
        # Test connection
        client.server_info()
        
        data = list(collection.find({}, {"_id": 0}))
        if not data:
            raise Exception("MongoDB is empty.")
        
        df = pd.DataFrame(data)
        
        # Convert created_at field
        df["created_at"] = pd.to_datetime(df["created_at"], errors='coerce')
        
        return df
    
    except Exception as e:
        st.warning(f"⚠️ MongoDB not reachable or empty. Falling back to CSV: {e}")
        if os.path.exists(CSV_FALLBACK_PATH):
            df = pd.read_csv(CSV_FALLBACK_PATH)
            if "created_at" in df.columns:
                df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
            return df
        else:
            st.error("No data available. CSV fallback file not found.")
            return pd.DataFrame([])

# ----------------------
# Streamlit UI
# ----------------------
st.set_page_config(page_title="Twitter Sentiment Dashboard", layout="wide")
st.title("📊 Twitter Sentiment Analysis Dashboard")
st.write("Live sentiment analysis of tweets collected using BERT.")

df = load_data()

if df.empty:
    st.warning("⚠️ No data available yet. Please run `collector.py` first.")
else:
    # Sidebar filters
    st.sidebar.header("Filters")
    sentiment_filter = st.sidebar.multiselect(
        "Select Sentiment", 
        options=df["sentiment"].unique(), 
        default=list(df["sentiment"].unique())
    )

    df_filtered = df[df["sentiment"].isin(sentiment_filter)]

    # Metrics
    st.subheader("📈 Overview")
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tweets", len(df_filtered))
    col2.metric("Positive", (df_filtered["sentiment"] == "Positive").sum())
    col3.metric("Negative", (df_filtered["sentiment"] == "Negative").sum())

    # Sentiment distribution
    fig1 = px.pie(df_filtered, names="sentiment", title="Sentiment Distribution")
    st.plotly_chart(fig1, use_container_width=True)

    # Sentiment trend over time
    if "created_at" in df_filtered.columns and not df_filtered["created_at"].isnull().all():
        trend = df_filtered.groupby([pd.Grouper(key="created_at", freq="1H"), "sentiment"]).size().reset_index(name="count")
        fig2 = px.line(trend, x="created_at", y="count", color="sentiment", title="Sentiment Over Time")
        st.plotly_chart(fig2, use_container_width=True)

    # Recent tweets
    st.subheader("📝 Recent Tweets")
    st.dataframe(df_filtered[["created_at", "sentiment", "score", "text"]].sort_values(by="created_at", ascending=False).head(20))