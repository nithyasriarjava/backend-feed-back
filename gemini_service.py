import os
import json
from dotenv import load_dotenv
from groq import Groq
import models

# Load environment variables
load_dotenv()

API_KEY = os.getenv("GROQ_API_KEY")

if not API_KEY:
    raise ValueError("GROQ_API_KEY environment variable not set.")

client = Groq(api_key=API_KEY)


def process_feedback_with_ai(feedback_id: int, text: str, db):
    feedback = None

    try:
        # Get feedback from database
        feedback = db.query(models.Feedback).filter(
            models.Feedback.id == feedback_id
        ).first()

        if not feedback:
            return

        prompt = f"""
You are an AI Feedback Classifier.

Analyze the feedback and return ONLY valid JSON.

Do NOT return markdown.
Do NOT return explanation.
Do NOT return extra text.

Feedback:
{text}

Return exactly this JSON:

{{
  "category":"bug",
  "sentiment":"positive",
  "summary":"one line summary"
}}

Category must be one of:
bug
feature_request
complaint
praise

Sentiment must be one of:
positive
neutral
negative
"""

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )

        ai_text = response.choices[0].message.content.strip()

        print("========== GROQ RESPONSE ==========")
        print(ai_text)
        print("===================================")

        result = json.loads(ai_text)

        category = result.get("category", "").strip().lower()
        sentiment = result.get("sentiment", "").strip().lower()
        summary = result.get("summary", "").strip()

        category = category.replace(" ", "_")

        valid_categories = [
            "bug",
            "feature_request",
            "complaint",
            "praise"
        ]

        valid_sentiments = [
            "positive",
            "neutral",
            "negative"
        ]

        if category not in valid_categories:
            raise ValueError(f"Invalid category received: {category}")

        if sentiment not in valid_sentiments:
            raise ValueError(f"Invalid sentiment received: {sentiment}")

        feedback.category = models.CategoryEnum(category)
        feedback.sentiment = models.SentimentEnum(sentiment)
        feedback.summary = summary
        feedback.status = models.StatusEnum.done
        feedback.error_message = None

        db.commit()
        db.refresh(feedback)

        print("Feedback Updated Successfully")

    except Exception as e:

        print("AI ERROR:", str(e))

        if feedback:
            feedback.status = models.StatusEnum.failed
            feedback.error_message = str(e)
            db.commit()

    finally:
        db.close()