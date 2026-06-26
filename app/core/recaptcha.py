import httpx
from fastapi import HTTPException

from app.core.config import (
    settings,  # adjust import to wherever your settings/env config lives
)

RECAPTCHA_VERIFY_URL = "https://www.google.com/recaptcha/api/siteverify"
RECAPTCHA_MIN_SCORE = 0.5


def verify_recaptcha(token: str | None, expected_action: str) -> None:
    if not token:
        raise HTTPException(status_code=400, detail="reCAPTCHA token missing")

    with httpx.Client(timeout=5.0) as client:
        try:
            resp = client.post(
                RECAPTCHA_VERIFY_URL,
                data={
                    "secret": settings.RECAPTCHA_SECRET_KEY,
                    "response": token,
                },
            )
            result = resp.json()
        except httpx.HTTPError as e:
            raise HTTPException(
                status_code=502, detail="reCAPTCHA verification unavailable"
            ) from e

    if not result.get("success"):
        raise HTTPException(status_code=400, detail="reCAPTCHA verification failed")

    if result.get("action") != expected_action:
        raise HTTPException(status_code=400, detail="reCAPTCHA action mismatch")

    if result.get("score", 0) < RECAPTCHA_MIN_SCORE:
        raise HTTPException(
            status_code=400, detail="reCAPTCHA score too low, possible bot"
        )
