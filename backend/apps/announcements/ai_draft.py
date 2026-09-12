import json

from django.conf import settings
from google import genai


class AINotConfigured(Exception):
    pass


def generate_announcement_draft(note: str) -> dict:
    key = settings.GEMINI_API_KEY
    if not key or key == "gemini_api_key_not_configured":
        raise AINotConfigured("AI not configured")

    client = genai.Client(api_key=key)
    prompt = (
        "You write union local callouts. Given a leadership note, return JSON "
        "with keys title (max 255 chars), body, push_preview (max 120 chars). "
        "Do not send or approve anything; this is a draft for a human to edit.\n\n"
        f"Leadership note:\n{note}"
    )
    response = client.models.generate_content(
        model=settings.GEMINI_MODEL,
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )
    data = json.loads(response.text)
    return {
        "title": str(data.get("title", "")).strip()[:255],
        "body": str(data.get("body", "")).strip(),
        "push_preview": str(data.get("push_preview", "")).strip()[:120],
    }
