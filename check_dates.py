from pymongo import MongoClient
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
DB_NAME = os.getenv("MONGO_DB", "twitter_sentiment")
COLL_NAME = os.getenv("MONGO_COLLECTION", "tweets")

client = MongoClient(MONGO_URI)
db = client[DB_NAME]
coll = db[COLL_NAME]

docs = list(coll.find({}, {"created_at": 1, "_id": 0}))
df = pd.DataFrame(docs)

if not df.empty:
    df["created_at"] = pd.to_datetime(df["created_at"])
    print("Dates available in MongoDB:")
    print(df["created_at"].head(20))
else:
    print("No documents found in MongoDB.")