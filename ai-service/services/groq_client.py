import os
import time
import logging
from pathlib import Path
from groq import Groq
from dotenv import load_dotenv


ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=ENV_PATH)

logger = logging.getLogger(__name__)

MODEL_NAME = "llama-3.3-70b-versatile"
MAX_RETRIES = 3
BACKOFF_SECONDS = [1, 2, 4]


def generate_text(prompt: str) -> str:
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ValueError("GROQ_API_KEY is not set")

    client = Groq(api_key=api_key)
    last_error = None

    for attempt in range(MAX_RETRIES):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an AI assistant that writes clear, professional audit responses."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                max_completion_tokens=300
            )

            if not response or not getattr(response, "choices", None):
                raise ValueError("Groq response contained no choices")

            message = response.choices[0].message
            if not message or not getattr(message, "content", None):
                raise ValueError("Groq response contained no message content")

            return message.content.strip()

        except Exception as exc:
            last_error = exc
            logger.exception(
                "Groq request failed on attempt %s/%s",
                attempt + 1,
                MAX_RETRIES
            )

            if attempt < MAX_RETRIES - 1:
                time.sleep(BACKOFF_SECONDS[attempt])

    raise RuntimeError(f"Groq request failed after {MAX_RETRIES} attempts: {last_error}")