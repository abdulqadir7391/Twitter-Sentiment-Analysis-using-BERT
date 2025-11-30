import os
import time
from datetime import datetime
from dotenv import load_dotenv
import tweepy
from classifier import SentimentClassifier
from db import DBClient
from utils import preprocess_tweet, contains_abusive, send_email_alert
import csv

# Load environment variables
load_dotenv()

BEARER_TOKEN = os.getenv("TWITTER_BEARER_TOKEN")
if not BEARER_TOKEN:
    raise ValueError("Set TWITTER_BEARER_TOKEN in .env")

QUERY = os.getenv("QUERY", "#AI lang:en -is:retweet")
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "150"))
MAX_RESULTS = int(os.getenv("MAX_RESULTS", "50"))  # reduce to avoid rate limits
FALLBACK_CSV = os.getenv("CSV_FALLBACK_PATH", "./tweets_fallback.csv")

def safe_search(client, query, max_results=50):
    """Search tweets safely with rate-limit handling and exponential backoff."""
    retry_wait = 10
    while True:
        try:
            resp = client.search_recent_tweets(
                query=query,
                tweet_fields=["created_at", "lang"],
                max_results=max_results
            )
            return resp
        except tweepy.TooManyRequests:
            print("Rate limit hit. Sleeping 15 minutes...")
            time.sleep(15*60)
        except Exception as e:
            print(f"Search error: {e}. Retrying in {retry_wait} seconds...")
            time.sleep(retry_wait)
            retry_wait = min(retry_wait * 2, 900)  # max 15 min backoff

def build_doc(tweet, clean_text, mapped_label, score):
    """Build MongoDB document or CSV row."""
    # Correction: Store 'created_at' as a datetime object for better querying in MongoDB
    # CSV fallback will handle the conversion back to string.
    created_at_dt = tweet.created_at if hasattr(tweet, "created_at") else None
    
    return {
        "tweet_id": tweet.id,
        "text": tweet.text,
        "clean_text": clean_text,
        "sentiment": mapped_label,
        "score": float(score),
        "created_at": created_at_dt,
        "lang": tweet.lang if hasattr(tweet, "lang") else None,
        "geo": getattr(tweet, "geo", None)
    }

def save_to_csv(doc):
    """Fallback storage if MongoDB fails."""
    file_exists = os.path.isfile(FALLBACK_CSV)
    with open(FALLBACK_CSV, "a", newline="", encoding="utf-8") as csvfile:
        fieldnames = list(doc.keys())
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(doc)

def main_loop():
    client = tweepy.Client(bearer_token=BEARER_TOKEN)
    try:
        db = DBClient()
        print("Connected to MongoDB.")
    except Exception as e:
        print(f"MongoDB not reachable. Falling back to CSV file: {FALLBACK_CSV}")
        db = None
    
    classifier = SentimentClassifier()
    seen_ids = set()  # avoid duplicates in memory
    print(f"Starting Collector with Query: {QUERY}")
    while True:
        resp = safe_search(client, QUERY, max_results=MAX_RESULTS)
        if resp and resp.data:
            for tw in resp.data:
                if tw.id in seen_ids:
                    continue
                seen_ids.add(tw.id)
                clean = preprocess_tweet(tw.text)
                label_raw, mapped, score = classifier.classify(clean)
                doc = build_doc(tw, clean, mapped, score)
                
                # Save to MongoDB or fallback CSV
                if db and db.connected:
                    try:
                        db.insert(doc)
                    except Exception as e:
                        print(f"MongoDB insert failed: {e}, saving to CSV.")
                        save_to_csv(doc)
                else:
                    save_to_csv(doc)
                
                # Print sentiment summary
                print(f"[{doc['created_at']}] {mapped} ({score:.2f}): {tw.text[:200]}")
                
                # Optional email alerts for abusive tweets
                if contains_abusive(tw.text):
                    subject = "ALERT: abusive keyword detected in tweet"
                    body = f"Tweet ID: {tw.id}\nText: {tw.text}\nSentiment: {mapped} ({score:.2f})"
                    send_email_alert(subject, body)
        else:
            print("No tweets in this poll.")
        
        time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main_loop()