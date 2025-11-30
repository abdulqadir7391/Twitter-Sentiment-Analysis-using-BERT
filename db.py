# db.py
import os
import csv
from datetime import datetime
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from dotenv import load_dotenv

# Load .env file
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
DB_NAME = os.getenv("MONGO_DB", "twitter_sentiment")
COLL_NAME = os.getenv("MONGO_COLLECTION", "tweets")
CSV_FALLBACK = os.getenv("CSV_FALLBACK_PATH", "./tweets_fallback.csv")

class DBClient:
    def __init__(self):
        self.client = None
        self.db = None
        self.coll = None
        self.connected = False
        try:
            self.client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
            # force connect check
            self.client.server_info()
            self.db = self.client[DB_NAME]
            self.coll = self.db[COLL_NAME]
            self.connected = True
            print("✅ Connected to MongoDB.")
        except ServerSelectionTimeoutError:
            print("⚠️ MongoDB not reachable. Falling back to CSV file:", CSV_FALLBACK)
            self.connected = False
            self._ensure_csv()
    
    def _ensure_csv(self):
        header = ["tweet_id", "text", "clean_text", "sentiment", "score",
                  "created_at", "lang", "geo", "inserted_at"]
        if not os.path.exists(CSV_FALLBACK):
            with open(CSV_FALLBACK, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(header)

    def insert(self, doc: dict):
        doc["inserted_at"] = datetime.utcnow() # Store as datetime object
        
        # Convert datetime objects to ISO strings for CSV fallback
        csv_doc = doc.copy()
        if csv_doc.get("created_at"):
            csv_doc["created_at"] = csv_doc["created_at"].isoformat()
        if csv_doc.get("inserted_at"):
            csv_doc["inserted_at"] = csv_doc["inserted_at"].isoformat()
        
        if self.connected:
            try:
                # Ensure the created_at field is a datetime object for MongoDB
                if isinstance(doc.get("created_at"), str):
                    doc["created_at"] = datetime.fromisoformat(doc["created_at"])
                
                self.coll.insert_one(doc)
            except Exception as e:
                print("⚠️ Error inserting into MongoDB:", e)
                self._append_csv(csv_doc)
        else:
            self._append_csv(csv_doc)

    def _append_csv(self, doc: dict):
        row = [
            doc.get("tweet_id"), doc.get("text"), doc.get("clean_text"),
            doc.get("sentiment"), doc.get("score"), doc.get("created_at"),
            doc.get("lang"), doc.get("geo"), doc.get("inserted_at")
        ]
        with open(CSV_FALLBACK, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(row)