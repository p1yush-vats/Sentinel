"""
Reports API Endpoints
"""
import io
import uuid
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.database import get_db
from ..core.security import get_current_user_id, RoleChecker

from ..models.employee import Employee
from ..models.session import Session
from ..models.abnormality import Abnormality
from ..models.leave import Leave
from ..models.appeal import Appeal

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

router = APIRouter()


@router.get("/employee/{employee_id}/dossier")
async def generate_dossier(
    employee_id: str,
    user_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db)
):
    employee = await db.scalar(select(Employee).where(Employee.id == uuid.UUID(employee_id)))
    if not employee:
        raise HTTPException(status_code=404, detail="Employee not found")

    if str(user_id) != str(employee.id) and employee.role not in ['admin', 'super_admin']:
        # Double check if requester is actually an admin
        requester = await db.scalar(select(Employee).where(Employee.id == uuid.UUID(user_id)))
        if not requester or requester.role not in ['admin', 'super_admin']:
            raise HTTPException(status_code=403, detail="Not enough permissions")

    sess_result = await db.execute(
        select(Session)
        .where(Session.employee_id == uuid.UUID(employee_id))
        .order_by(desc(Session.start_time))
        .limit(30)
    )
    sessions = sess_result.scalars().all()

    flag_result = await db.execute(
        select(Abnormality)
        .where(Abnormality.employee_id == uuid.UUID(employee_id))
        .order_by(desc(Abnormality.first_detected_at))
        .limit(20)
    )
    all_flags = flag_result.scalars().all()
    unreviewed_flags = [f for f in all_flags if not f.reviewed]

    leaves_result = await db.execute(
        select(Leave).where(Leave.employee_id == uuid.UUID(employee_id)).order_by(desc(Leave.created_at)).limit(10)
    )
    leaves = leaves_result.scalars().all()
    
    # Calculate Risk Score from sessions (recent 10 completed/partial)
    completed_scores = [s.risk_score for s in sessions if s.status != "active" and s.risk_score is not None][:10]
    total_w, total_s = 0.0, 0.0
    for i, score in enumerate(completed_scores):
        weight = 2.0 if i < 5 else 1.0
        total_s += float(score) * weight
        total_w += weight
    risk_score = round(total_s / total_w, 1) if total_w > 0 else 0.0

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter, rightMargin=40, leftMargin=40, topMargin=40, bottomMargin=40)
    
    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    h2_style = styles["Heading2"]
    normal_style = styles["Normal"]

    story = []
    story.append(Paragraph(f"HR Employee Dossier: {employee.full_name}", title_style))
    story.append(Spacer(1, 12))
    
    profile_data = [
        ["Department:", employee.department or "N/A", "Employee Code:", employee.employee_code or "N/A"],
        ["Email:", employee.email, "Current Risk Score:", f"{risk_score} / 100"],
        ["Role:", employee.role.capitalize(), "Pending Flags:", str(len(unreviewed_flags))],
    ]
    
    t = Table(profile_data, colWidths=[100, 160, 100, 160])
    t.setStyle(TableStyle([
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (2, 0), (2, -1), 'Helvetica-Bold'),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ('BOX', (0, 0), (-1, -1), 0.25, colors.lightgrey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(t)
    story.append(Spacer(1, 24))
    
    story.append(Paragraph("Recent Sessions Log (Last 30 days)", h2_style))
    story.append(Spacer(1, 12))
    
    if not sessions:
        story.append(Paragraph("No recent sessions found.", normal_style))
    else:
        session_data = [["Date", "Work (min)", "Break (min)", "Risk Score", "Status"]]
        for s in sessions:
            date_str = s.start_time.strftime("%Y-%m-%d %H:%M")
            work_m = str(s.total_work_minutes or 0)
            brk_m = str(s.total_break_minutes or 0)
            r_score = str(round(s.risk_score)) if s.risk_score else "0"
            status = s.status.capitalize()
            session_data.append([date_str, work_m, brk_m, r_score, status])

        t2 = Table(session_data, colWidths=[150, 80, 80, 80, 120])
        t2.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f8fafc")),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1"))
        ]))
        story.append(t2)

    story.append(Spacer(1, 24))
    
    # Flags section
    story.append(Paragraph("Recent Abnormalities & Flags", h2_style))
    story.append(Spacer(1, 12))
    if not all_flags:
        story.append(Paragraph("Clean record. No flags detected.", normal_style))
    else:
        flag_data = [["Date", "Severity", "Confidence", "Status", "Review Decision"]]
        for f in all_flags:
            date_str = f.first_detected_at.strftime("%Y-%m-%d %H:%M")
            sev = f.overall_severity
            conf = f"{round((f.confidence_score or 0) * 100, 1)}%"
            status = "Reviewed" if f.reviewed else "Pending"
            dec = f.review_decision or "None"
            flag_data.append([date_str, sev, conf, status, dec])
            
        t3 = Table(flag_data, colWidths=[120, 80, 80, 80, 150])
        t3.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1"))
        ]))
        story.append(t3)

    story.append(Spacer(1, 24))

    # Leaves section
    story.append(Paragraph("Recent Leave Requests", h2_style))
    story.append(Spacer(1, 12))
    if not leaves:
        story.append(Paragraph("No leave applications found.", normal_style))
    else:
        leave_data = [["Applied On", "From - To", "Days", "Type", "Status"]]
        for l in leaves:
            applied = l.created_at.strftime("%Y-%m-%d") if l.created_at else "N/A"
            rng = f"{l.from_date} to {l.to_date}"
            days = str(l.days_requested)
            ltype = l.leave_type
            status = l.status.capitalize()
            leave_data.append([applied, rng, days, ltype, status])
            
        t4 = Table(leave_data, colWidths=[100, 150, 60, 80, 120])
        t4.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1e293b")),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1"))
        ]))
        story.append(t4)

    doc.build(story)
    buffer.seek(0)

    filename = f"dossier_{employee.full_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    return StreamingResponse(
        iter([buffer.getvalue()]), 
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )