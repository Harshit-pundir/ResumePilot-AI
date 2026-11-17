import io
import sys
import types
import unittest
from unittest.mock import patch

from services import pdf_parser


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
