import os
from mistralai import Mistral
from dotenv import load_dotenv

load_dotenv()

MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")


def get_mistral_client():
    if not MISTRAL_API_KEY:
        return None
    return Mistral(api_key=MISTRAL_API_KEY)

