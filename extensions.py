import spacy
from supabase import create_client

from config import SUPABASE_KEY, SUPABASE_URL
from utils.logger import get_logger

logger = get_logger(__name__)
latest_report = {}


def initialize_extensions(app):
    try:
        app.extensions["nlp"] = spacy.load("en_core_web_sm")
    except OSError:
        logger.error("spaCy model 'en_core_web_sm' is not installed.")
        raise
    app.extensions["supabase"] = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_supabase(app):
    return app.extensions["supabase"]
