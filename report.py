import os
import pandas as pd
from db import DBClient
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from datetime import datetime, timedelta
from dotenv import load_dotenv

def generate_daily_report(date=None):
    # Load environment variables from .env file
    load_dotenv()
    
    if date is None:
        # Get today's date instead of yesterday's to match the CSV data
        date = datetime.utcnow().date()
    
    start = datetime.combine(date, datetime.min.time())
    end = datetime.combine(date, datetime.max.time())
    
    db = DBClient()
    df = pd.DataFrame()

    # Attempt to get data from MongoDB first
    if db.connected:
        try:
            cursor = db.coll.find(
                {
                    "created_at": {
                        "$gte": start,
                        "$lte": end
                    }
                },
                {"_id": 0, "created_at": 1, "text": 1, "sentiment": 1}
            )
            df = pd.DataFrame(list(cursor))
            if not df.empty:
                df["created_at"] = pd.to_datetime(df["created_at"])
        except Exception as e:
            print(f"Error querying MongoDB: {e}")
    
    # If MongoDB is not connected or returned no data, try the CSV fallback
    if df.empty:
        print("MongoDB is not connected or has no data. Checking CSV fallback...")
        csv_path = os.getenv("CSV_FALLBACK_PATH", "./tweets_fallback.csv")
        
        if os.path.exists(csv_path):
            try:
                df = pd.read_csv(csv_path)
                df["created_at"] = pd.to_datetime(df["created_at"], errors="coerce", utc=True)
                df = df[(df['created_at'].dt.date >= start.date()) & (df['created_at'].dt.date <= end.date())]
                df = df.dropna(subset=['created_at'])
            except Exception as e:
                print(f"Error reading CSV fallback file: {e}")
                df = pd.DataFrame()
        else:
            print("CSV fallback file not found.")

    if df.empty:
        print(f"No data for {date.isoformat()}. Please check your data source or wait for the collector to run.")
        return

    # sentiment summary
    summary = df["sentiment"].value_counts().to_dict()
    total = len(df)

    # CSV output
    csv_out = f"report_{date.isoformat()}.csv"
    df.to_csv(csv_out, index=False)

    # PDF output
    pdf_out = f"report_{date.isoformat()}.pdf"
    c = canvas.Canvas(pdf_out, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(72, 720, f"Sentiment Report for {date.isoformat()}")
    c.setFont("Helvetica", 12)
    c.drawString(72, 700, f"Total tweets: {total}")
    y = 670
    for k, v in summary.items():
        c.drawString(72, y, f"{k}: {v}")
        y -= 20
    
    c.save()
    print(f"Reports written: {csv_out}, {pdf_out}")

if __name__ == "__main__":
    generate_daily_report()