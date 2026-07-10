import os
import json
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from dotenv import load_dotenv
import models

# Load environment variables
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set.")

genai.configure(api_key=API_KEY)


def process_feedback_with_ai(feedback_id: int, text: str, db):
    feedback = None

    try:

        feedback = db.query(models.Feedback).filter(
            models.Feedback.id == feedback_id
        ).first()

        if not feedback:
            return

        model = genai.GenerativeModel(
            "gemini-1.5-flash",
            generation_config=genai.types.GenerationConfig(
                response_mime_type="application/json"
            )
        )

        prompt = f"""
You are an AI Feedback Classifier.

Return ONLY valid JSON.

Do NOT return markdown.
Do NOT return explanation.
Do NOT return extra text.

Feedback:
{text}

Return exactly this format:

{{
    "category":"bug | feature_request | complaint | praise",
    "sentiment":"positive | neutral | negative",
    "summary":"one line summary"
}}
"""

        response = model.generate_content(
            prompt,
            request_options={"timeout": 60}
        )

        print("========== GEMINI RESPONSE ==========")
        print(response.text)
        print("=====================================")

        ai_text = response.text.strip()

        ai_text = ai_text.replace("```json", "")
        ai_text = ai_text.replace("```", "")
        ai_text = ai_text.strip()

        result = json.loads(ai_text)

        category = str(result.get("category", "")).strip().lower()
        sentiment = str(result.get("sentiment", "")).strip().lower()
        summary = str(result.get("summary", "")).strip()

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

    except (
        google_exceptions.GoogleAPICallError,
        json.JSONDecodeError,
        ValueError
    ) as e:

        print("AI ERROR:", str(e))

        if feedback:
            feedback.status = models.StatusEnum.failed
            feedback.error_message = f"{type(e).__name__}: {str(e)}"
            db.commit()

    except Exception as e:

        print("UNEXPECTED ERROR:", str(e))

        if feedback:
            feedback.status = models.StatusEnum.failed
            feedback.error_message = f"{type(e).__name__}: {str(e)}"
            db.commit()

    finally:
        db.close()