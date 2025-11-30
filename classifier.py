# classifier.py
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
import os

MODEL_NAME = os.getenv("SENTIMENT_MODEL", "nlptown/bert-base-multilingual-uncased-sentiment")

class SentimentClassifier:
    def __init__(self, model_name=MODEL_NAME, device=-1):
        # device=-1 uses CPU. Change to 0 for GPU if available and torch installed.
        self.tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast=False)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_name)
        self.pipeline = pipeline("sentiment-analysis", model=self.model, tokenizer=self.tokenizer, device=device)

    def classify(self, text):
        """
        returns: (label_str, mapped_label, score)
        label_str: original like "4 stars"
        mapped_label: Positive/Neutral/Negative
        score: confidence float
        """
        # Ensure text is not empty
        if not text:
            return "N/A", "Neutral", 0.0

        res = self.pipeline(text, truncation=True, max_length=512)[0]
        label = res["label"]  # e.g., "4 stars"
        score = float(res["score"])
        mapped = self.map_label(label)
        return label, mapped, score

    @staticmethod
    def map_label(label):
        # nlptown: "1 star" ... "5 stars"
        if "1" in label or "2" in label:
            return "Negative"
        if "3" in label:
            return "Neutral"
        return "Positive"

# quick test when run directly
if __name__ == "__main__":
    import sys
    sc = SentimentClassifier()
    text = "This is a great day!" if len(sys.argv) < 2 else " ".join(sys.argv[1:])
    print(sc.classify(text))