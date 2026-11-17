from io import BytesIO
import re
from typing import Any

from PyPDF2 import PdfReader

from utils.logger import get_logger

logger = get_logger(__name__)

# Short text layers are common in scanned PDFs (for example, a page number or
# hidden OCR artifact) and should not suppress the image OCR fallback.
MIN_TEXT_CHARACTERS = 80
OCR_RENDER_DPI = 250
OCR_CONTRAST_FACTOR = 1.5
OCR_PAGE_SEGMENTATION_MODE = 3


class PDFTextExtractionError(Exception):
    """Raised when neither the PDF text layer nor OCR yields usable text."""


def _extract_selectable_text(file: Any) -> str:
    """Read each selectable PDF page and return its nonempty text."""
    reader = PdfReader(file)
    page_texts = []
    for page in reader.pages:
        try:
            page_text = page.extract_text() or ""
            if page_text.strip():
                page_texts.append(page_text.strip())
        except Exception:
            logger.exception("Error while extracting text from a PDF page.")
    return "\n".join(page_texts)


def _prepare_image(image: Any) -> Any:
    """Convert an OCR page image to a higher-contrast grayscale image."""
    from PIL import ImageEnhance, ImageOps

    image = ImageOps.grayscale(image)
    image = ImageOps.autocontrast(image)
    return ImageEnhance.Contrast(image).enhance(OCR_CONTRAST_FACTOR)


def _correct_rotation(image: Any, pytesseract: Any) -> Any:
    """Rotate an image when Tesseract can determine its page orientation."""
    try:
        orientation = pytesseract.image_to_osd(image, output_type=pytesseract.Output.DICT)
        rotation = int(orientation.get("rotate", 0)) % 360
        if rotation:
            return image.rotate(-rotation, expand=True)
    except Exception:
        # OSD often cannot determine orientation on sparse resume pages. OCR
        # itself can still work, so orientation detection is best effort.
        logger.debug("Could not determine scanned PDF page orientation.", exc_info=True)
    return image


def _extract_ocr_page(page: Any, matrix: Any, image_module: Any, pytesseract: Any) -> str:
    """Render and recognize one PDF page, returning its stripped OCR text."""
    pixmap = page.get_pixmap(matrix=matrix, alpha=False)
    image = image_module.open(BytesIO(pixmap.tobytes("png")))
    image = _correct_rotation(_prepare_image(image), pytesseract)
    text = pytesseract.image_to_string(
        image,
        config=f"--psm {OCR_PAGE_SEGMENTATION_MODE}",
    )
    return (text or "").strip()


def _extract_ocr_text(file: Any) -> str:
    """OCR every PDF page and return recognized text in page order."""
    try:
        import fitz
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise PDFTextExtractionError(
            "This PDF appears to be scanned, but OCR dependencies are unavailable. "
            "Install the Python requirements and the Tesseract OCR application."
        ) from exc

    try:
        if hasattr(file, "seek"):
            file.seek(0)
        pdf_bytes = file.read()
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
        scale = OCR_RENDER_DPI / 72
        matrix = fitz.Matrix(scale, scale)
        page_texts = []
        for page_number, page in enumerate(document, start=1):
            page_text = _extract_ocr_page(page, matrix, Image, pytesseract)
            page_texts.append(page_text)
            logger.info("OCR processed PDF page %s.", page_number)
        document.close()
        readable_pages = [page_text for page_text in page_texts if page_text]
        return "\n".join(readable_pages)
    except pytesseract.TesseractNotFoundError as exc:
        raise PDFTextExtractionError(
            "Tesseract OCR is not installed or is not on PATH. Install Tesseract "
            "and configure its executable path before analyzing scanned PDFs."
        ) from exc
    except PDFTextExtractionError:
        raise
    except Exception as exc:
        logger.exception("OCR failed while extracting text from the PDF.")
        raise PDFTextExtractionError(
            "Unable to extract text from this PDF. Check that it is a valid PDF "
            "and that Tesseract OCR is installed correctly."
        ) from exc


def _has_usable_text(text: str) -> bool:
    """Return whether text has at least the configured non-whitespace length."""
    character_count = len(re.sub(r"\s", "", text))
    return character_count >= MIN_TEXT_CHARACTERS


def extract_text_from_pdf(file: Any) -> str:
    """Extract and lowercase PDF text, using OCR when selectable text is short."""
    try:
        text = _extract_selectable_text(file)
    except Exception:
        logger.exception("Selectable PDF text extraction failed; trying OCR.")
        text = ""

    if _has_usable_text(text):
        return text.lower()

    logger.info("PDF text layer is empty or too short; using OCR fallback.")
    ocr_text = _extract_ocr_text(file)
    if not ocr_text.strip():
        raise PDFTextExtractionError(
            "No readable text was found in this PDF. Try a clearer scan or a PDF "
            "with selectable text."
        )
    return ocr_text.lower()
