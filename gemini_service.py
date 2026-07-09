import os
import json
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from dotenv import load_dotenv
import models

# .env ஃபைலில் உள்ள API key-ஐ லோட் செய்ய
load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set. Please create a .env file and add it.")
genai.configure(api_key=API_KEY)


def process_feedback_with_ai(feedback_id: int, text: str, db):
    feedback = None # Initialize feedback to None for safer error handling
    try:
        # 1. Database-ல் இருந்து pending-ல் உள்ள feedback-ஐ எடுப்பது
        feedback = db.query(models.Feedback).filter(models.Feedback.id == feedback_id).first()
        if not feedback:
            return

        # 2. Gemini API-க்கு அனுப்ப வேண்டிய Prompt (கட்டளை)
        # Use response_mime_type to enforce JSON output
        # Assignment requirement-படி AI category, sentiment, summary ஆகியவற்றைத் தர வேண்டும்
        model = genai.GenerativeModel(
            'gemini-1.5-flash',
            generation_config=genai.types.GenerationConfig(response_mime_type="application/json"))
        prompt = f"""
        Analyze the following user feedback and provide the output strictly as a JSON object.
        Do not include markdown tags like ```json.
        Feedback: "{text}"
        
        Format required:
        {{
            "category": "choose one: bug, feature_request, complaint, praise",
            "sentiment": "choose one: positive, neutral, negative",
            "summary": "A short one-line summary of the feedback"
        }}
        """
        
        # 3. Gemini API-ஐ கால் செய்வது
        response = model.generate_content(prompt, request_options={'timeout': 60}) # Add a 60-second timeout

        # AI கொடுத்த பதிலை JSON ஆக மாற்றுவது
        result = json.loads(response.text)

        # Validate the AI's response to ensure it matches our enums
        category = result.get("category")
        sentiment = result.get("sentiment")

        if category not in models.CategoryEnum.__members__:
            raise ValueError(f"Invalid category '{category}' received from AI.")
        
        if sentiment not in models.SentimentEnum.__members__:
            raise ValueError(f"Invalid sentiment '{sentiment}' received from AI.")

        # 4. Database-ல் AI கொடுத்த விவரங்களை Update செய்வது
        feedback.category = category
        feedback.sentiment = sentiment
        feedback.summary = result.get("summary")
        feedback.status = models.StatusEnum.done # AI வேலை முடிந்தது என status-ஐ மாற்றுவது
        db.commit()

    except (google_exceptions.GoogleAPICallError, json.JSONDecodeError, ValueError) as e:
        # AI API-ல் ஏதாவது எர்ரர் வந்தால், அதை catch செய்து failed என மாற்றுவது
        # இது Assignment-ல் முக்கியமாக எதிர்பார்க்கப்படும் "Error state" handling ஆகும்
        if feedback:
            feedback.status = models.StatusEnum.failed
            feedback.error_message = str(e)
            db.commit()
    except Exception as e:
        # Catch any other unexpected errors
        if feedback:
            feedback.status = models.StatusEnum.failed
            feedback.error_message = f"An unexpected error occurred: {str(e)}"
            db.commit()
    finally:
        # கடைசியாக DB connection-ஐ close செய்வது
        db.close()