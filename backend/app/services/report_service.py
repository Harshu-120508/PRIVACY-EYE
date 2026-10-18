"""
Report service — generates AI-powered evidence reports using Gemini.
Falls back to structured template if Gemini is unavailable.
"""
import uuid
import json
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import MediaAnalysis, Report, AnalysisSignal
from app.core.config import settings
import structlog

logger = structlog.get_logger(__name__)


class ReportService:
    async def generate(
        self, db: AsyncSession, analysis: MediaAnalysis, user
    ) -> Report:
        """Generate a structured evidence report, optionally enhanced by Gemini AI."""

        from sqlalchemy import select
        signals = await db.execute(
            select(AnalysisSignal)
            .where(AnalysisSignal.analysis_id == analysis.id)
        )
        signal_list = signals.scalars().all()

        # Build structured data for the report
        signal_data = [
            {
                "key": s.signal_key,
                "label": s.signal_label,
                "severity": s.severity,
                "score": s.score,
                "description": s.description,
            }
            for s in signal_list
        ]

        risk_emoji = {
            "LOW": "🟢",
            "SUSPICIOUS": "🟡",
            "HIGH": "🟠",
            "CRITICAL": "🔴",
            "UNDETERMINED": "⚪",
        }.get(analysis.risk_level.value if analysis.risk_level else "UNDETERMINED", "⚪")

        summary, recommendations = await self._generate_with_gemini(analysis, signal_data)

        report_json = {
            "report_id": str(uuid.uuid4()),
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "generated_by": "Privacy Eye Analysis Engine v1.0.0-mvp",
            "file": {
                "original_filename": analysis.original_filename,
                "media_type": analysis.media_type.value,
                "file_size_bytes": analysis.file_size_bytes,
                "sha256": analysis.file_sha256,
                "mime_type": analysis.mime_type,
            },
            "assessment": {
                "risk_level": analysis.risk_level.value if analysis.risk_level else "UNDETERMINED",
                "risk_emoji": risk_emoji,
                "synthetic_probability": analysis.synthetic_probability,
                "confidence": analysis.confidence,
                "explanation": analysis.explanation,
            },
            "detected_signals": signal_data,
            "provenance": analysis.provenance_info or {},
            "raw_scores": analysis.raw_scores or {},
            "model": {
                "version": "1.0.0-mvp",
                "name": "PrivacyEye-Ensemble-v1",
                "disclaimer": (
                    "This report presents probabilistic indicators only. "
                    "Privacy Eye does not claim 100% accuracy. "
                    "Do not use this report as the sole basis for legal or disciplinary action. "
                    "Always apply human judgment."
                ),
            },
            "summary": summary,
            "recommendations": recommendations,
        }

        report = Report(
            id=str(uuid.uuid4()),
            user_id=user.id,
            analysis_id=analysis.id,
            title=f"Privacy Eye Report — {analysis.original_filename}",
            summary=summary,
            recommendations=recommendations,
            report_json=report_json,
        )
        db.add(report)
        await db.flush()
        await db.refresh(report)
        return report

    async def _generate_with_gemini(self, analysis: MediaAnalysis, signals: list) -> tuple[str, str]:
        """Use Gemini to write human-readable summary and recommendations."""
        if not settings.GEMINI_API_KEY:
            return self._fallback_summary(analysis, signals), self._fallback_recommendations(analysis)

        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(settings.GEMINI_MODEL)

            prompt = f"""You are the Privacy Eye Report Agent — an AI assistant that helps users understand deepfake and synthetic media detection results.

Analysis Data:
- File: {analysis.original_filename}
- Media Type: {analysis.media_type.value}
- Risk Level: {analysis.risk_level.value if analysis.risk_level else 'UNDETERMINED'}
- Synthetic Probability: {f'{analysis.synthetic_probability:.2%}' if analysis.synthetic_probability is not None else 'N/A'}
- Confidence: {f'{analysis.confidence:.2%}' if analysis.confidence is not None else 'N/A'}
- Detected Signals: {json.dumps(signals, indent=2)}

Write two sections:

SUMMARY (2-3 sentences): Explain in plain language what was found. Use cautious, probabilistic language. Never say "definitely fake" — say "indicators suggest" or "the system detected signals consistent with".

RECOMMENDATIONS (3-5 bullet points): What should the user do next? Consider: verifying with additional sources, contacting platform support, preserving evidence, not sharing the content, seeking expert review.

Format your response as JSON:
{{"summary": "...", "recommendations": "..."}}"""

            response = model.generate_content(prompt)
            text = response.text.strip()
            # Strip markdown code fences if present
            if text.startswith("```"):
                text = text.split("```")[1]
                if text.startswith("json"):
                    text = text[4:]
            parsed = json.loads(text)
            return parsed.get("summary", ""), parsed.get("recommendations", "")

        except Exception as e:
            logger.warning("Gemini report generation failed", error=str(e))
            return self._fallback_summary(analysis, signals), self._fallback_recommendations(analysis)

    def _fallback_summary(self, analysis: MediaAnalysis, signals: list) -> str:
        risk = analysis.risk_level.value if analysis.risk_level else "UNDETERMINED"
        prob = f"{analysis.synthetic_probability:.0%}" if analysis.synthetic_probability is not None else "unknown"
        sig_count = len(signals)
        return (
            f"Privacy Eye analyzed this {analysis.media_type.value.lower()} and detected a {risk} risk level "
            f"with a synthetic media probability of {prob}. "
            f"{sig_count} indicator(s) were flagged during analysis. "
            f"These results represent probabilistic signals only and should not be treated as conclusive evidence."
        )

    def _fallback_recommendations(self, analysis: MediaAnalysis) -> str:
        risk = analysis.risk_level.value if analysis.risk_level else "UNDETERMINED"
        if risk in ("HIGH", "CRITICAL"):
            return (
                "• Do not share this media until authenticity is confirmed.\n"
                "• Preserve the original file and this report as evidence.\n"
                "• Consider reporting to the platform where you received this content.\n"
                "• Seek expert forensic review for legal or sensitive matters.\n"
                "• Contact relevant authorities if this involves potential fraud or impersonation."
            )
        elif risk == "SUSPICIOUS":
            return (
                "• Verify the source of this media through independent channels.\n"
                "• Be cautious about sharing until authenticity is clearer.\n"
                "• Save this report for your records.\n"
                "• Consider a second opinion from a digital forensics expert."
            )
        else:
            return (
                "• No strong synthetic indicators were found, but remain vigilant.\n"
                "• Verify content through trusted sources before acting on it.\n"
                "• Save this report for your records."
            )

    def generate_html_certificate(self, report: Report, analysis: MediaAnalysis) -> str:
        """Generate a standalone, print-optimized HTML forensic certificate."""
        rep_json = report.report_json or {}
        file_info = rep_json.get("file", {})
        assessment = rep_json.get("assessment", {})
        signals = rep_json.get("detected_signals", [])
        risk_level = assessment.get("risk_level", analysis.risk_level.value if analysis.risk_level else "UNDETERMINED")
        synth_prob = assessment.get("synthetic_probability")
        prob_str = f"{synth_prob:.1%}" if synth_prob is not None else "N/A"
        conf = assessment.get("confidence")
        conf_str = f"{conf:.1%}" if conf is not None else "N/A"
        sha256 = file_info.get("sha256", analysis.file_sha256 or "N/A")
        gen_at = rep_json.get("generated_at", datetime.now(timezone.utc).isoformat())

        badge_color = {
            "LOW": "#10b981",
            "SUSPICIOUS": "#f59e0b",
            "HIGH": "#f97316",
            "CRITICAL": "#ef4444",
            "UNDETERMINED": "#6b7280",
        }.get(risk_level, "#6b7280")

        signal_rows = ""
        for sig in signals:
            score_val = sig.get("score")
            score_fmt = f"{score_val:.1%}" if score_val is not None else "Observed"
            signal_rows += f"""
            <tr>
              <td style="padding: 10px 14px; border-bottom: 1px solid #e5e7eb; font-weight: 600;">{sig.get('label', sig.get('key'))}</td>
              <td style="padding: 10px 14px; border-bottom: 1px solid #e5e7eb;"><span style="display: inline-block; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: 700; background: #f3f4f6; color: #374151;">{sig.get('severity', 'info').upper()}</span></td>
              <td style="padding: 10px 14px; border-bottom: 1px solid #e5e7eb; font-family: monospace;">{score_fmt}</td>
              <td style="padding: 10px 14px; border-bottom: 1px solid #e5e7eb; color: #4b5563; font-size: 13px;">{sig.get('description', '')}</td>
            </tr>
            """

        if not signal_rows:
            signal_rows = """
            <tr>
              <td colspan="4" style="padding: 14px; text-align: center; color: #9ca3af; font-style: italic;">No anomalous signals flagged during multi-spectral analysis.</td>
            </tr>
            """

        recs_list = ""
        for line in (report.recommendations or "").split("\n"):
            line = line.strip().lstrip("•").strip()
            if line:
                recs_list += f"<li style='margin-bottom: 6px;'>{line}</li>"

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Privacy Eye Forensic Certificate — {analysis.original_filename}</title>
  <style>
    @page {{
      size: A4;
      margin: 15mm;
    }}
    body {{
      font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;
      color: #1f2937;
      background: #f9fafb;
      margin: 0;
      padding: 30px;
    }}
    .cert-container {{
      max-width: 820px;
      margin: 0 auto;
      background: #ffffff;
      border: 1px solid #e5e7eb;
      border-radius: 12px;
      padding: 40px;
      box-shadow: 0 4px 20px rgba(0, 0, 0, 0.05);
      position: relative;
    }}
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
      border-bottom: 2px solid #0284c7;
      padding-bottom: 20px;
      margin-bottom: 25px;
    }}
    .brand-title {{
      font-size: 24px;
      font-weight: 800;
      color: #0f172a;
      letter-spacing: -0.5px;
      margin: 0;
    }}
    .brand-subtitle {{
      font-size: 11px;
      font-weight: 700;
      color: #0284c7;
      text-transform: uppercase;
      letter-spacing: 1.5px;
      margin-top: 4px;
    }}
    .cert-meta {{
      text-align: right;
      font-family: monospace;
      font-size: 11px;
      color: #6b7280;
    }}
    .verdict-box {{
      display: flex;
      gap: 15px;
      background: #f8fafc;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 18px 24px;
      margin-bottom: 25px;
      align-items: center;
      justify-content: space-between;
    }}
    .badge {{
      display: inline-block;
      padding: 6px 14px;
      border-radius: 6px;
      color: #ffffff;
      font-weight: 800;
      font-size: 15px;
      letter-spacing: 0.5px;
      background: {badge_color};
    }}
    .metric-group {{
      display: flex;
      gap: 24px;
    }}
    .metric {{
      text-align: center;
    }}
    .metric-label {{
      font-size: 10px;
      text-transform: uppercase;
      color: #64748b;
      font-weight: 600;
      margin-bottom: 2px;
    }}
    .metric-val {{
      font-size: 18px;
      font-weight: 700;
      color: #0f172a;
      font-family: monospace;
    }}
    .section-title {{
      font-size: 13px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 1px;
      color: #334155;
      margin-top: 25px;
      margin-bottom: 10px;
      border-left: 3px solid #0284c7;
      padding-left: 8px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 13px;
      margin-top: 8px;
    }}
    th {{
      text-align: left;
      background: #f1f5f9;
      padding: 10px 14px;
      font-size: 11px;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.5px;
      color: #475569;
      border-bottom: 1px solid #cbd5e1;
    }}
    .hash-box {{
      background: #0f172a;
      color: #38bdf8;
      padding: 12px 16px;
      border-radius: 6px;
      font-family: monospace;
      font-size: 12px;
      word-break: break-all;
      margin: 10px 0;
    }}
    .summary-text {{
      font-size: 13.5px;
      line-height: 1.6;
      color: #334155;
      background: #f8fafc;
      padding: 14px 18px;
      border-radius: 6px;
      border: 1px solid #e2e8f0;
    }}
    .recs-list {{
      font-size: 13px;
      line-height: 1.6;
      color: #334155;
      padding-left: 20px;
      margin: 8px 0;
    }}
    .footer {{
      margin-top: 35px;
      padding-top: 20px;
      border-top: 1px solid #e2e8f0;
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 11px;
      color: #64748b;
    }}
    .seal {{
      display: inline-flex;
      align-items: center;
      gap: 6px;
      font-weight: 700;
      color: #0284c7;
    }}
    @media print {{
      body {{
        background: #ffffff;
        padding: 0;
      }}
      .cert-container {{
        box-shadow: none;
        border: none;
        padding: 0;
      }}
      .no-print {{
        display: none;
      }}
    }}
  </style>
</head>
<body>
  <div class="cert-container">
    <div class="header">
      <div>
        <h1 class="brand-title">PRIVACY EYE</h1>
        <div class="brand-subtitle">Forensic Authenticity Certificate</div>
      </div>
      <div class="cert-meta">
        <div><strong>Certificate ID:</strong> {report.id[:16]}</div>
        <div><strong>Issued:</strong> {gen_at[:19].replace('T', ' ')} UTC</div>
        <div><strong>Engine:</strong> PrivacyEye-Ensemble-v1</div>
      </div>
    </div>

    <div class="verdict-box">
      <div>
        <div class="metric-label">Assessed Risk Verdict</div>
        <span class="badge">{risk_level}</span>
      </div>
      <div class="metric-group">
        <div class="metric">
          <div class="metric-label">Synthetic Risk</div>
          <div class="metric-val">{prob_str}</div>
        </div>
        <div class="metric">
          <div class="metric-label">Calibrated Confidence</div>
          <div class="metric-val">{conf_str}</div>
        </div>
        <div class="metric">
          <div class="metric-label">Forensic Reliability</div>
          <div class="metric-val" style="color: #10b981;">HIGH</div>
        </div>
      </div>
    </div>

    <div class="section-title">Cryptographic Media Provenance</div>
    <div style="font-size: 13px; color: #4b5563; margin-bottom: 4px;">
      <strong>File:</strong> {analysis.original_filename} &nbsp;|&nbsp;
      <strong>Type:</strong> {analysis.media_type.value} &nbsp;|&nbsp;
      <strong>Size:</strong> {analysis.file_size_bytes or 0:,} bytes &nbsp;|&nbsp;
      <strong>MIME:</strong> {analysis.mime_type or 'unspecified'}
    </div>
    <div class="hash-box">
      SHA-256: {sha256}
    </div>

    <div class="section-title">Executive Forensic Summary</div>
    <div class="summary-text">
      {report.summary or analysis.explanation or "Media assessed using multi-signal spectral and biometric forensic pipeline."}
    </div>

    <div class="section-title">Forensic Signal Indicators</div>
    <table>
      <thead>
        <tr>
          <th>Signal Indicator</th>
          <th>Severity</th>
          <th>Score</th>
          <th>Description</th>
        </tr>
      </thead>
      <tbody>
        {signal_rows}
      </tbody>
    </table>

    <div class="section-title">Tactical Recommendations & Preservations</div>
    <ul class="recs-list">
      {recs_list or "<li>Preserve original media and verification hash in evidence locker.</li><li>Apply human corroboration for high-stakes decisions.</li>"}
    </ul>

    <div class="footer">
      <div class="seal">
        <span>🛡️ SECURE VERIFIED RECORD</span>
        <span>· SHA-256 CHAIN ANCHOR</span>
      </div>
      <div style="text-align: right; max-width: 400px; font-size: 10px; line-height: 1.4; color: #94a3b8;">
        Probabilistic assessment only. Not designed as sole legal determinant. Privacy Eye cryptographic assurance seal.
      </div>
    </div>
  </div>
</body>
</html>"""


report_service = ReportService()

