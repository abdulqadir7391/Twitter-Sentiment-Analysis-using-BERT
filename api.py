import os
from fastapi import FastAPI, HTTPException
from db import DBClient
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import json
from bson import ObjectId
from datetime import datetime

class JSONEncoder(json.JSONEncoder):
    """
    Helper to serialize MongoDB ObjectId and datetime objects.
    """
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return json.JSONEncoder.default(self, obj)

app = FastAPI(title="Twitter Sentiment API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"],
)
db = DBClient()

@app.get("/stats")
def stats():
    if not db.connected:
        return JSONResponse({"error": "DB not connected"}, status_code=503)
    total = db.coll.count_documents({})
    pos = db.coll.count_documents({"sentiment": "Positive"})
    neu = db.coll.count_documents({"sentiment": "Neutral"})
    neg = db.coll.count_documents({"sentiment": "Negative"})
    return {"total": total, "positive": pos, "neutral": neu, "negative": neg}

@app.get("/tweets")
def get_tweets(sentiment: str = None, limit: int = 50):
    if not db.connected:
        raise HTTPException(status_code=503, detail="DB not connected")
    query = {}
    if sentiment:
        query["sentiment"] = sentiment
    docs = list(db.coll.find(query).sort("inserted_at", -1).limit(limit))
    return JSONResponse(json.loads(json.dumps(docs, cls=JSONEncoder)))

# Run with: uvicorn api:app --reload --port 8000