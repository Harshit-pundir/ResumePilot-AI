from io import BytesIO

from fastapi import APIRouter
from fastapi.responses import JSONResponse , StreamingResponse

import extensions
from services.pdf_report_service import build_pdf_report

router = APIRouter()


@router.get("/download-report")
def download_report():
    if not extensions.latest_report:
        return JSONResponse({"error": "No report available."}, 400)
    
    buffer = BytesIO()
    build_pdf_report(buffer, extensions.latest_report)
    buffer.seek(0)

    return StreamingResponse(buffer , media_type="application/pdf" , headers={"Content-Disposition": 'attachment; filename = ResumePilot_report.pdf'},)
