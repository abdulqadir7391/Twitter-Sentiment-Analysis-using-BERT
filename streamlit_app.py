import streamlit as st
import pandas as pd
import plotly.express as px
import os
from db import DBClient
from datetime import datetime

st.set_page_config(page_title="Twitter Sentiment Dashboard", layout="wide")

@st.cache_data(ttl=60)
def load_data():
    """
    Loads data from MongoDB or falls back to CSV.
    """
    db = DBClient()
    df = pd.DataFrame()
    
    if db.connected:
        try:
            # Fetch up to 1000 latest tweets from MongoDB
            cursor = db.coll.find().sort("inserted_at", -1).limit(1000)
            df = pd.DataFrame(list(cursor))
            if not df.empty:
                # Convert `created_at` field to datetime objects for proper filtering
                df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
        except Exception as e:
            st.error(f"Error reading from MongoDB: {e}")
            df = pd.DataFrame()
    
    # Fallback to CSV if MongoDB is not connected or failed
    if df.empty:
        csv_path = os.getenv("CSV_FALLBACK_PATH", "./tweets_fallback.csv")
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                if "created_at" in df.columns:
                    df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce")
            except Exception as e:
                st.error(f"Error reading from CSV fallback file: {e}")
                df = pd.DataFrame()
    return df

# Load the data
df = load_data()
st.title("Twitter Sentiment Dashboard")
st.markdown("Live-ish view of collected tweets and sentiment.")

if df.empty or df['created_at'].isnull().all():
    st.info("No data available yet or data is not correctly formatted. Please ensure `collector.py` is running and saving data.")
else:
    # Set up filters in the sidebar for better UI
    st.sidebar.header("Filter Data")
    
    # Date range filter
    min_date = df['created_at'].min().date() if not df['created_at'].isnull().all() else datetime.today().date()
    max_date = df['created_at'].max().date() if not df['created_at'].isnull().all() else datetime.today().date()
    
    # Using st.date_input correctly to filter the DataFrame
    date_range_selection = st.sidebar.date_input(
        "Select Date Range", 
        value=[min_date, max_date],
        min_value=min_date, 
        max_value=max_date
    )
    
    # Ensure date_range_selection is a list with two dates
    if len(date_range_selection) == 2:
        start_date, end_date = date_range_selection
        # Filter the dataframe by date
        df = df[(df['created_at'].dt.date >= start_date) & (df['created_at'].dt.date <= end_date)]

    # Sentiment filter
    sentiment_filter = st.sidebar.selectbox(
        "Select Sentiment", 
        options=["All"] + list(df["sentiment"].unique())
    )
    
    # Keyword filter
    keyword = st.sidebar.text_input("Filter by Keyword (in tweet text)")

    # Apply filters to a copy of the DataFrame
    dff = df.copy()
    if sentiment_filter != "All":
        dff = dff[dff["sentiment"] == sentiment_filter]
    
    if keyword:
        dff = dff[dff["text"].str.contains(keyword, case=False, na=False)]

    st.subheader(f"Showing {len(dff)} tweets")
    
    # Chart: Sentiment Distribution Pie Chart
    if not dff.empty:
        fig = px.pie(dff, names="sentiment", title="Sentiment Distribution")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No tweets match the selected filters.")

    # Chart: Sentiment Trend Over Time
    if "created_at" in dff.columns and not dff['created_at'].isnull().all():
        times = dff.groupby(pd.Grouper(key="created_at", freq="1H")).sentiment.value_counts().unstack(fill_value=0)
        if not times.empty:
            fig2 = px.line(times, x=times.index, y=times.columns, title="Sentiment Over Time")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("No time series data available for this range.")
    
    # Display recent tweets in a table
    if not dff.empty:
        st.subheader("Recent Tweets")
        st.dataframe(dff[["created_at", "sentiment", "score", "text"]].sort_values(by="created_at", ascending=False).head(200))