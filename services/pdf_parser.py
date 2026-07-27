from PyPDF2 import PdfReader

from utils.logger import get_logger

logger = get_logger(__name__)


def extract_text_from_pdf(file) -> str:
    reader = PdfReader(file)
    complete_text = ""

    for page in reader.pages:
        try:
            page_text = page.extract_text()
            if page_text:
                complete_text += page_text + " "
        except Exception:
            logger.exception("Error while extracting text from a PDF page.")
            continue

    return complete_text.lower()
