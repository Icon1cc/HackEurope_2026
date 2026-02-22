import stripe

from app.core.config import get_settings


def init_stripe() -> None:
    settings = get_settings()
    stripe.api_key = settings.stripe_secret_key
