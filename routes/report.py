from io import BytesIO

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse

import extensions
from deps import get_current_user
from services.pdf_report_service import build_pdf_report

router = APIRouter()


@router.get("/download-report")
def download_report(request: Request):
    user = get_current_user(request)
    if not user:
        return JSONResponse({"error": "Please log in."}, status_code=401)

    report = extensions.latest_reports.get(user["id"])   # sirf is user ki report
    if not report:
        return JSONResponse({"error": "No report available."}, status_code=400)

    buffer = BytesIO()
    build_pdf_report(buffer, report)
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": 'attachment; filename="ResumePilot_Report.pdf"'},
    )