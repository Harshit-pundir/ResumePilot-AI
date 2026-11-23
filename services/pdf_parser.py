from io import BytesIO
import os
import re
import shutil
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


WINDOWS_TESSERACT_PATHS = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe",
    r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
)


def _resolve_tesseract_command() -> str:
    """Find the Tesseract engine using configuration, PATH, or common locations."""
    configured = os.environ.get("TESSERACT_CMD", "").strip().strip('"')
    if configured:
        configured = os.path.expandvars(os.path.expanduser(configured))
        resolved = configured if os.path.isfile(configured) else shutil.which(configured)
        if resolved:
            return resolved
        raise PDFTextExtractionError(
            f"TESSERACT_CMD points to '{configured}', but that executable was not found. "
            "Set TESSERACT_CMD to the Tesseract executable path."
        )

    executable = shutil.which("tesseract")
    if executable:
        return executable

    if os.name == "nt":
        for candidate in WINDOWS_TESSERACT_PATHS:
            if os.path.isfile(candidate):
                return candidate
    else:
        for candidate in ("/usr/bin/tesseract", "/usr/local/bin/tesseract"):
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate

    raise PDFTextExtractionError(
        "This PDF needs OCR, but the Tesseract OCR engine was not found. Install "
        "Tesseract or set TESSERACT_CMD to its executable path, then try again."
    )


def _configure_tesseract(pytesseract: Any) -> None:
    command = _resolve_tesseract_command()
    controller = getattr(pytesseract, "pytesseract", pytesseract)
    controller.tesseract_cmd = command


def _extract_selectable_text(file: Any) -> str:
    """Read each selectable PDF page and return its nonempty text."""
    if hasattr(file, "seek"):
        file.seek(0)
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

    if hasattr(file, "seek"):
        file.seek(0)
    try:
        pdf_bytes = file.read()
        document = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        logger.exception("Unable to open PDF for OCR.")
        raise PDFTextExtractionError(
            "The uploaded file is not a readable PDF. Upload a valid, uncorrupted PDF and try again."
        ) from exc

    try:
        _configure_tesseract(pytesseract)
        scale = OCR_RENDER_DPI / 72
        matrix = fitz.Matrix(scale, scale)
        page_texts = []
        for page_number, page in enumerate(document, start=1):
            page_text = _extract_ocr_page(page, matrix, Image, pytesseract)
            page_texts.append(page_text)
            logger.info("OCR processed PDF page %s.", page_number)
        readable_pages = [page_text for page_text in page_texts if page_text]
        return "\n".join(readable_pages)
    except PDFTextExtractionError:
        raise
    except Exception as exc:
        tesseract_not_found = getattr(pytesseract, "TesseractNotFoundError", ())
        if tesseract_not_found and isinstance(exc, tesseract_not_found):
            raise PDFTextExtractionError(
                "Tesseract could not start. Install the Tesseract OCR engine or set "
                "TESSERACT_CMD to its executable path, then try again."
            ) from exc
        logger.exception("OCR failed while extracting text from the PDF.")
        raise PDFTextExtractionError(
            "OCR could not read this PDF. Check that its pages are clear and that "
            "Tesseract includes English language data, then try again."
        ) from exc
    finally:
        document.close()


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
