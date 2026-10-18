"""
Reports routes — generate and download evidence reports.
"""
import json
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.session import get_db
from app.database.models import MediaAnalysis, Report, AnalysisStatus
from app.schemas.schemas import ReportResponse
from app.core.security import get_current_user
from app.services.report_service import report_service

router = APIRouter()


@router.post("/{analysis_id}/generate", response_model=ReportResponse, status_code=201)
async def generate_report(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Generate an AI-powered evidence report for a completed analysis."""
    result = await db.execute(
        select(MediaAnalysis).where(
            MediaAnalysis.id == analysis_id,
            MediaAnalysis.user_id == current_user.id,
            MediaAnalysis.deleted_at.is_(None),
        )
    )
    analysis = result.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    if analysis.status != AnalysisStatus.COMPLETE:
        raise HTTPException(status_code=400, detail="Analysis not yet complete")

    # Check if report already exists
    existing = await db.execute(select(Report).where(Report.analysis_id == analysis_id))
    report = existing.scalar_one_or_none()
    if report:
        return report

    report = await report_service.generate(db, analysis, current_user)
    return report


@router.get("/{analysis_id}", response_model=ReportResponse)
async def get_report(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Retrieve existing report for an analysis."""
    result = await db.execute(
        select(Report).where(
            Report.analysis_id == analysis_id,
            Report.user_id == current_user.id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found. Generate it first.")
    return report


@router.get("/{analysis_id}/download/json")
async def download_report_json(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Download report as JSON."""
    result = await db.execute(
        select(Report).where(
            Report.analysis_id == analysis_id,
            Report.user_id == current_user.id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    content = json.dumps(report.report_json or {}, indent=2)
    return Response(
        content=content,
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="privacy-eye-report-{analysis_id[:8]}.json"'},
    )


@router.get("/{analysis_id}/download/html")
async def download_report_html(
    analysis_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Download or view report as a print-ready HTML forensic certificate."""
    result = await db.execute(
        select(Report).where(
            Report.analysis_id == analysis_id,
            Report.user_id == current_user.id,
        )
    )
    report = result.scalar_one_or_none()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    analysis_res = await db.execute(
        select(MediaAnalysis).where(MediaAnalysis.id == analysis_id)
    )
    analysis = analysis_res.scalar_one_or_none()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    html_content = report_service.generate_html_certificate(report, analysis)
    return Response(
        content=html_content,
        media_type="text/html",
        headers={"Content-Disposition": f'inline; filename="privacy-eye-certificate-{analysis_id[:8]}.html"'},
    )

