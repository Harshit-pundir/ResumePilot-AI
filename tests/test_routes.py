import io
import json
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from fastapi import Request, UploadFile

from routes import ai, auth, history, home, report, upload


def make_request(path: str = "/") -> Request:
    """Build a small Starlette request for direct route-function tests."""
    return Request({
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": path,
        "raw_path": path.encode(),
        "query_string": b"",
        "headers": [],
        "client": ("127.0.0.1", 8000),
        "server": ("test", 80),
    })


class EmptyQuery:
    """Provide the chainable empty Supabase result used by auth tests."""
    def select(self, _columns):
        return self

    def eq(self, _column, _value):
        return self

    def order(self, _column, desc=False):
        return self

    def execute(self):
        return SimpleNamespace(data=[])


class RouteCharacterizationTests(unittest.TestCase):
    def test_upload_requires_login_and_resume(self):
        request = make_request("/upload")
        with patch.object(upload, "get_current_user", return_value=None):
            unauthorized = upload.upload_resume(request, resume=None)
        self.assertEqual(unauthorized.status_code, 401)
        self.assertEqual(json.loads(unauthorized.body), {"error": "Please log in."})

        with patch.object(upload, "get_current_user", return_value={"id": "user-1"}):
            missing_resume = upload.upload_resume(request, resume=None)
        self.assertEqual(missing_resume.status_code, 400)
        self.assertEqual(json.loads(missing_resume.body), {"error": "Please upload a resume."})

    def test_upload_rejects_unsupported_file_and_surfaces_ocr_dependency_error(self):
        request = make_request("/upload")
        user = {"id": "user-1"}
        unsupported = SimpleNamespace(filename="resume.docx", file=io.BytesIO(b"docx"))
        with patch.object(upload, "get_current_user", return_value=user):
            response = upload.upload_resume(request, resume=unsupported)
        self.assertEqual(response.status_code, 415)
        self.assertIn("upload a PDF", json.loads(response.body)["error"])

        scanned = SimpleNamespace(filename="scanned.pdf", file=io.BytesIO(b"pdf"))
        with patch.object(upload, "get_current_user", return_value=user), patch.object(
            upload, "extract_text_from_pdf", side_effect=upload.PDFTextExtractionError(
                "Tesseract is unavailable; install it or set TESSERACT_CMD."
            ),
        ):
            response = upload.upload_resume(request, resume=scanned)
        self.assertEqual(response.status_code, 422)
        self.assertIn("TESSERACT_CMD", json.loads(response.body)["error"])

    def test_resume_analysis_response_shape(self):
        sections = {
            "summary": "Summary", "skills": "Python", "projects": "Project",
            "education": "Degree", "experience": "Job", "certifications": "",
            "achievements": "",
        }
        contacts = {
            "email": "a@example.com", "phone": None, "linkedin": None,
            "github": None, "portfolio": None,
        }
        with patch.object(upload, "save_resume_history"), patch.object(upload, "build_latest_report"):
            response = upload.process_resume_analysis(
                {"python"}, sections, contacts, SimpleNamespace(filename="resume.pdf"),
                71.43, 20, 58.33, None, "user-1",
            )
        payload = json.loads(response.body)
        self.assertEqual(payload["mode"], "resume_analysis")
        self.assertEqual(payload["resume_skills"], ["python"])
        self.assertEqual(payload["contact_details"], contacts)
        self.assertEqual(
            set(payload),
            {
                "mode", "score", "overall_assessment", "recommendations", "sections",
                "section_score", "contact_score", "completeness_score", "resume_skills",
                "contact_details", "score_breakdown",
            },
        )
        self.assertEqual(payload["score_breakdown"]["components"]["Section Structure"]["weight"], 70)
        self.assertEqual(payload["score_breakdown"]["components"]["Contact Details"]["weight"], 30)

    def test_ai_route_returns_existing_success_and_error_shapes(self):
        request = make_request("/ai-improve")
        with patch.object(ai, "get_current_user", return_value=None):
            unauthorized = ai.ai_improve(request, resume=None)
        self.assertEqual(unauthorized.status_code, 401)
        self.assertEqual(json.loads(unauthorized.body), {"error": "Please log in."})

        user = {"id": "user-1"}
        with patch.object(ai, "get_current_user", return_value=user):
            missing_resume = ai.ai_improve(request, resume=None)
        self.assertEqual(missing_resume.status_code, 400)
        self.assertEqual(json.loads(missing_resume.body), {"error": "Resume not uploaded"})

        resume = UploadFile(filename="resume.pdf", file=io.BytesIO(b"pdf"))
        with patch.object(ai, "get_current_user", return_value=user), \
             patch.object(ai, "extract_text_from_pdf", return_value="resume text"), \
             patch.object(ai, "generate_ai_resume_feedback", return_value="## Feedback"):
            result = ai.ai_improve(request, resume=resume)
        self.assertEqual(result, {"response": "## Feedback", "html": "<h2>Feedback</h2>\n"})

    def test_auth_routes_keep_redirects_and_invalid_input_responses(self):
        logout = auth.logout_user()
        self.assertEqual(logout.status_code, 303)
        self.assertEqual(logout.headers["location"], "/login")
        self.assertIn("access_token", logout.headers["set-cookie"])

        request = make_request("/auth/register")
        with patch.object(auth.templates, "TemplateResponse", return_value="register-page") as render:
            result = auth.register_user(request, "bad-email", "long-enough", "long-enough")
        self.assertEqual(result, "register-page")
        self.assertEqual(render.call_args.kwargs["status_code"], 400)

        with patch.object(auth, "supabase", SimpleNamespace(table=lambda _name: EmptyQuery())), \
             patch.object(auth.templates, "TemplateResponse", return_value="login-page") as render:
            result = auth.login_user(request, "missing@example.com", "password")
        self.assertEqual(result, "login-page")
        self.assertEqual(render.call_args.kwargs["status_code"], 401)

    def test_history_and_admin_access_checks(self):
        request = make_request("/api/history")
        with patch.object(history, "get_current_user", return_value=None):
            result = history.history_api(request)
        self.assertEqual(result.status_code, 401)
        self.assertEqual(json.loads(result.body), {"error": "Please log in."})

        with patch.object(history, "get_current_user", return_value={"id": "user-1", "role": "user"}):
            denied = history.admin_history(request)
        self.assertEqual(denied.status_code, 403)

    def test_report_route_returns_login_and_no_report_errors(self):
        request = make_request("/download-report")
        with patch.object(report, "get_current_user", return_value=None):
            unauthorized = report.download_report(request)
        self.assertEqual(unauthorized.status_code, 401)

        with patch.object(report, "get_current_user", return_value={"id": "user-1"}), \
             patch.object(report.extensions, "latest_reports", {}):
            missing = report.download_report(request)
        self.assertEqual(missing.status_code, 400)
        self.assertEqual(json.loads(missing.body), {"error": "No report available."})

    def test_home_route_passes_current_user_to_template(self):
        request = make_request()
        user = {"id": "user-1"}
        with patch.object(home, "get_current_user", return_value=user), \
             patch.object(home.templates, "TemplateResponse", return_value="home-page") as render:
            result = home.home(request)
        self.assertEqual(result, "home-page")
        self.assertEqual(render.call_args.args[1], "index.html")
        self.assertEqual(render.call_args.args[2], {"user": user})


if __name__ == "__main__":
    unittest.main()
