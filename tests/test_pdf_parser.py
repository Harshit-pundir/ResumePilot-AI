import io
import os
import shutil
import sys
import tempfile
import types
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from services import pdf_parser


def make_scanned_pdf(page_texts):
    import fitz
    from PIL import Image, ImageDraw, ImageFont

    font_path = next((path for path in (
        r"C:\Windows\Fonts\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ) if os.path.isfile(path)), None)
    font = ImageFont.truetype(font_path, 58) if font_path else ImageFont.load_default(size=58)
    document = fitz.open()
    for text in page_texts:
        image = Image.new("RGB", (1900, 500), "white")
        ImageDraw.Draw(image).text((50, 120), text, fill="black", font=font)
        image_buffer = io.BytesIO()
        image.save(image_buffer, format="PNG")
        page = document.new_page(width=612, height=792)
        page.insert_image(fitz.Rect(24, 24, 588, 220), stream=image_buffer.getvalue())
    return document.tobytes()


def make_text_pdf(text):
    import fitz

    document = fitz.open()
    page = document.new_page()
    page.insert_textbox(fitz.Rect(40, 40, 570, 750), text, fontsize=12)
    return document.tobytes()


HAS_TESSERACT = bool(shutil.which("tesseract") or any(
    os.path.isfile(path) for path in pdf_parser.WINDOWS_TESSERACT_PATHS
))


class SelectablePDFTests(unittest.TestCase):
    def test_selectable_text_uses_existing_parser_without_ocr(self):
        page_text = "resume content " * 10
        reader = types.SimpleNamespace(pages=[types.SimpleNamespace(extract_text=lambda: page_text)])
        with patch.object(pdf_parser, "PdfReader", return_value=reader), patch.object(
            pdf_parser, "_extract_ocr_text"
        ) as ocr:
            result = pdf_parser.extract_text_from_pdf(io.BytesIO(b"pdf"))
        self.assertEqual(result, page_text.lower().strip())
        ocr.assert_not_called()

    def test_real_text_pdf_extracts_without_ocr(self):
        pdf_bytes = make_text_pdf("Python FastAPI SQLAlchemy resume experience " * 8)
        with patch.object(pdf_parser, "_extract_ocr_text") as ocr:
            result = pdf_parser.extract_text_from_pdf(io.BytesIO(pdf_bytes))
        self.assertIn("python fastapi sqlalchemy", result)
        ocr.assert_not_called()

    def test_short_text_layer_uses_ocr_fallback(self):
        reader = types.SimpleNamespace(
            pages=[types.SimpleNamespace(extract_text=lambda: "Short text layer")]
        )
        with patch.object(pdf_parser, "PdfReader", return_value=reader), patch.object(
            pdf_parser, "_extract_ocr_text", return_value="OCR TEXT"
        ) as ocr:
            result = pdf_parser.extract_text_from_pdf(io.BytesIO(b"pdf"))
        self.assertEqual(result, "ocr text")
        ocr.assert_called_once()


class ScannedPDFTests(unittest.TestCase):
    def test_tesseract_cmd_environment_variable_is_used(self):
        with tempfile.NamedTemporaryFile() as executable, patch.dict(
            os.environ, {"TESSERACT_CMD": executable.name}
        ):
            self.assertEqual(pdf_parser._resolve_tesseract_command(), executable.name)

    def test_invalid_tesseract_cmd_reports_configuration_error(self):
        with patch.dict(os.environ, {"TESSERACT_CMD": "missing-tesseract-binary"}):
            with self.assertRaisesRegex(pdf_parser.PDFTextExtractionError, "TESSERACT_CMD"):
                pdf_parser._resolve_tesseract_command()

    @unittest.skipUnless(HAS_TESSERACT, "Tesseract engine not installed")
    def test_real_scanned_pdf_ocr_returns_page_text(self):
        pdf_bytes = make_scanned_pdf(["Python FastAPI resume experience database"])
        result = pdf_parser.extract_text_from_pdf(io.BytesIO(pdf_bytes))
        self.assertIn("python", result)
        self.assertIn("fastapi", result)
        self.assertIn("database", result)

    @unittest.skipUnless(HAS_TESSERACT, "Tesseract engine not installed")
    def test_real_multi_page_scanned_pdf_preserves_all_pages_in_order(self):
        pdf_bytes = make_scanned_pdf([
            "FIRST PAGE PYTHON EXPERIENCE",
            "SECOND PAGE FASTAPI PROJECTS",
        ])
        result = pdf_parser.extract_text_from_pdf(io.BytesIO(pdf_bytes))
        self.assertIn("first page python experience", result)
        self.assertIn("second page fastapi projects", result)
        self.assertLess(result.index("first page"), result.index("second page"))

    def test_corrupted_pdf_returns_actionable_error(self):
        with self.assertRaisesRegex(pdf_parser.PDFTextExtractionError, "valid, uncorrupted PDF"):
            pdf_parser.extract_text_from_pdf(io.BytesIO(b"not a PDF"))

    @unittest.skipUnless(HAS_TESSERACT, "Tesseract engine not installed")
    def test_blank_pdf_reports_no_readable_text(self):
        import fitz

        document = fitz.open()
        document.new_page()
        with self.assertRaisesRegex(pdf_parser.PDFTextExtractionError, "No readable text"):
            pdf_parser.extract_text_from_pdf(io.BytesIO(document.tobytes()))

    @unittest.skipUnless(HAS_TESSERACT, "Tesseract engine not installed")
    def test_real_scanned_pdf_reaches_ats_resume_analysis(self):
        from fastapi import Request
        from routes import upload

        pdf_bytes = make_scanned_pdf([
            "Jordan Rivera Software Engineer",
            "Python FastAPI SQL Git project experience education",
        ])
        request = Request({
            "type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1",
            "method": "POST", "scheme": "http", "path": "/upload",
            "raw_path": b"/upload", "query_string": b"", "headers": [],
            "client": ("127.0.0.1", 8000), "server": ("test", 80),
        })
        resume = SimpleNamespace(filename="scanned-resume.pdf", file=io.BytesIO(pdf_bytes))
        with patch.object(upload, "get_current_user", return_value={"id": "ocr-user"}), \
             patch.object(upload, "save_resume_history"), \
             patch.object(upload, "build_latest_report"):
            response = upload.upload_resume(request, resume=resume)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(__import__("json").loads(response.body)["mode"], "resume_analysis")

    def test_missing_tesseract_has_actionable_error(self):
        scanned_pdf = make_scanned_pdf(["A valid image-only PDF page"])
        with patch.object(
            pdf_parser, "_resolve_tesseract_command",
            side_effect=pdf_parser.PDFTextExtractionError(
                "This PDF needs OCR, but the Tesseract OCR engine was not found. "
                "Install Tesseract or set TESSERACT_CMD to its executable path."
            ),
        ):
            with self.assertRaisesRegex(pdf_parser.PDFTextExtractionError, "set TESSERACT_CMD"):
                pdf_parser._extract_ocr_text(io.BytesIO(scanned_pdf))

    def test_scanned_pdf_ocr_reads_all_pages_in_order(self):
        rendered_pages = [object(), object(), object()]
        fake_page_iter = [types.SimpleNamespace(get_pixmap=lambda **kwargs: types.SimpleNamespace(tobytes=lambda _fmt: b"image")) for _ in rendered_pages]
        fake_doc = types.SimpleNamespace(__iter__=lambda self: iter(fake_page_iter), close=lambda: None)
        # Python special methods are resolved on the class, so define a small iterable document.
        class Document:
            def __iter__(self):
                return iter(fake_page_iter)

            def close(self):
                pass

        fitz = types.ModuleType("fitz")
        fitz.Matrix = lambda *_args: object()
        fitz.open = lambda **_kwargs: Document()

        class FakeImage:
            def rotate(self, *_args, **_kwargs):
                return self

        image_module = types.ModuleType("PIL.Image")
        image_module.open = lambda _stream: FakeImage()
        enhance_module = types.ModuleType("PIL.ImageEnhance")
        enhance_module.Contrast = lambda image: types.SimpleNamespace(enhance=lambda _factor: image)
        ops_module = types.ModuleType("PIL.ImageOps")
        ops_module.grayscale = lambda image: image
        ops_module.autocontrast = lambda image: image
        pil_module = types.ModuleType("PIL")
        pil_module.__path__ = []
        pil_module.Image = image_module

        pytesseract = types.ModuleType("pytesseract")
        pytesseract.Output = types.SimpleNamespace(DICT="dict")
        pytesseract.TesseractNotFoundError = type("TesseractNotFoundError", (Exception,), {})
        ocr_pages = iter(["PAGE ONE", "PAGE TWO", "PAGE THREE"])
        pytesseract.image_to_osd = lambda *_args, **_kwargs: {"rotate": 0}
        pytesseract.image_to_string = lambda *_args, **_kwargs: next(ocr_pages)

        reader = types.SimpleNamespace(pages=[types.SimpleNamespace(extract_text=lambda: "")])
        fake_modules = {
            "fitz": fitz,
            "pytesseract": pytesseract,
            "PIL": pil_module,
            "PIL.Image": image_module,
            "PIL.ImageEnhance": enhance_module,
            "PIL.ImageOps": ops_module,
        }
        with patch.object(pdf_parser, "PdfReader", return_value=reader), patch.dict(sys.modules, fake_modules):
            result = pdf_parser.extract_text_from_pdf(io.BytesIO(b"scanned pdf"))
        self.assertEqual(result, "page one\npage two\npage three")

    def test_ocr_failure_is_reported_instead_of_returning_empty_text(self):
        reader = types.SimpleNamespace(pages=[types.SimpleNamespace(extract_text=lambda: "")])
        with patch.object(pdf_parser, "PdfReader", return_value=reader), patch.object(
            pdf_parser, "_extract_ocr_text", side_effect=pdf_parser.PDFTextExtractionError("Tesseract missing")
        ):
            with self.assertRaisesRegex(pdf_parser.PDFTextExtractionError, "Tesseract missing"):
                pdf_parser.extract_text_from_pdf(io.BytesIO(b"scanned pdf"))

    def test_empty_ocr_result_raises_readable_text_error(self):
        reader = types.SimpleNamespace(pages=[types.SimpleNamespace(extract_text=lambda: "")])
        with patch.object(pdf_parser, "PdfReader", return_value=reader), patch.object(
            pdf_parser, "_extract_ocr_text", return_value=""
        ):
            with self.assertRaisesRegex(pdf_parser.PDFTextExtractionError, "No readable text"):
                pdf_parser.extract_text_from_pdf(io.BytesIO(b"scanned pdf"))


if __name__ == "__main__":
    unittest.main()
