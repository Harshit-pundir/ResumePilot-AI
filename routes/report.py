from io import BytesIO

from flask import Blueprint, send_file

import extensions
from services.pdf_report_service import build_pdf_report

report_bp = Blueprint("report", __name__)


@report_bp.route("/download-report")
def download_report():
    if not extensions.latest_report:
        return {"error": "No report available."}, 400
    buffer = BytesIO()
    build_pdf_report(buffer, extensions.latest_report)
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name="ResumePilot_Report.pdf", mimetype="application/pdf")
