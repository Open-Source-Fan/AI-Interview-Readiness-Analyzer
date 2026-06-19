"""
report_gen.py — Module 5: PDF Report Generator

Converts a ReadinessReport into a downloadable PDF using reportlab.
Returns bytes so it can be passed directly to st.download_button().

Usage:
    from src.report_gen import generate_pdf
    pdf_bytes = generate_pdf(report)
    st.download_button("Download PDF", pdf_bytes, "report.pdf", "application/pdf")
"""

from __future__ import annotations

import io
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .schemas import ReadinessReport


# ── Colour palette ─────────────────────────────────────────────────────────────

C_DARK    = colors.HexColor("#1e293b")   # headings
C_MID     = colors.HexColor("#475569")   # body text
C_LIGHT   = colors.HexColor("#94a3b8")   # captions
C_GREEN   = colors.HexColor("#16a34a")
C_AMBER   = colors.HexColor("#d97706")
C_RED     = colors.HexColor("#dc2626")
C_BLUE    = colors.HexColor("#2563eb")
C_BG_BLUE = colors.HexColor("#eff6ff")
C_BG_GRN  = colors.HexColor("#f0fdf4")
C_BG_AMB  = colors.HexColor("#fffbeb")
C_BG_RED  = colors.HexColor("#fef2f2")
C_RULE    = colors.HexColor("#e2e8f0")


def _styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "rpt_title", parent=base["Title"],
            fontSize=22, textColor=C_DARK, spaceAfter=4,
            alignment=TA_CENTER,
        ),
        "subtitle": ParagraphStyle(
            "rpt_subtitle", parent=base["Normal"],
            fontSize=11, textColor=C_MID, spaceAfter=16,
            alignment=TA_CENTER,
        ),
        "h1": ParagraphStyle(
            "rpt_h1", parent=base["Heading1"],
            fontSize=14, textColor=C_DARK, spaceBefore=14, spaceAfter=6,
            borderPad=0,
        ),
        "h2": ParagraphStyle(
            "rpt_h2", parent=base["Heading2"],
            fontSize=12, textColor=C_BLUE, spaceBefore=10, spaceAfter=4,
        ),
        "h3": ParagraphStyle(
            "rpt_h3", parent=base["Heading3"],
            fontSize=10, textColor=C_MID, spaceBefore=8, spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "rpt_body", parent=base["Normal"],
            fontSize=9.5, textColor=C_MID, spaceAfter=4, leading=14,
        ),
        "small": ParagraphStyle(
            "rpt_small", parent=base["Normal"],
            fontSize=8.5, textColor=C_LIGHT, spaceAfter=3, leading=12,
        ),
        "bullet": ParagraphStyle(
            "rpt_bullet", parent=base["Normal"],
            fontSize=9.5, textColor=C_MID, spaceAfter=3,
            leftIndent=14, bulletIndent=4, leading=14,
        ),
        "score_big": ParagraphStyle(
            "rpt_score_big", parent=base["Normal"],
            fontSize=28, textColor=C_DARK, alignment=TA_CENTER, spaceAfter=2,
        ),
        "score_label": ParagraphStyle(
            "rpt_score_label", parent=base["Normal"],
            fontSize=10, textColor=C_MID, alignment=TA_CENTER,
        ),
    }


def _tier_colour(score: float) -> colors.Color:
    if score >= 75:
        return C_GREEN
    if score >= 50:
        return C_AMBER
    return C_RED


def _tier_text(score: float) -> str:
    if score >= 75:
        return "Excellent"
    if score >= 50:
        return "Good"
    return "Needs Work"


def _score_table(metrics: list[tuple[str, str]], col_count: int = 3) -> Table:
    """Build a compact N-column metrics grid."""
    # Pad to fill rows evenly
    while len(metrics) % col_count != 0:
        metrics.append(("", ""))

    rows = []
    for i in range(0, len(metrics), col_count):
        chunk = metrics[i:i + col_count]
        label_row = [Paragraph(f"<font size='8' color='#94a3b8'>{l}</font>", getSampleStyleSheet()["Normal"])
                     for l, _ in chunk]
        value_row = [Paragraph(f"<font size='13' color='#1e293b'><b>{v}</b></font>", getSampleStyleSheet()["Normal"])
                     for _, v in chunk]
        rows.append(label_row)
        rows.append(value_row)

    col_w = (A4[0] - 4 * cm) / col_count
    t = Table(rows, colWidths=[col_w] * col_count, hAlign="LEFT")
    t.setStyle(TableStyle([
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
    ]))
    return t


def generate_pdf(report: ReadinessReport) -> bytes:
    """
    Generate a readiness report PDF and return the bytes.
    Safe to call from Streamlit — no file I/O, pure in-memory.
    """
    buf = io.BytesIO()
    s   = _styles()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Interview Readiness Report",
        author="AI Interview Readiness Analyzer",
    )

    story = []
    rule  = HRFlowable(width="100%", thickness=1, color=C_RULE, spaceAfter=8, spaceBefore=4)

    # ── Cover ─────────────────────────────────────────────────────────────────
    story.append(Paragraph("🎯 Interview Readiness Report", s["title"]))
    story.append(Paragraph(
        f"Role: <b>{report.role}</b> &nbsp;·&nbsp; "
        f"Generated: {datetime.now().strftime('%d %b %Y')}",
        s["subtitle"],
    ))
    story.append(rule)

    # ── Overall score ─────────────────────────────────────────────────────────
    tier_c   = _tier_colour(report.overall_score)
    tier_txt = _tier_text(report.overall_score)

    score_data = [[
        Paragraph(f"<font color='{tier_c.hexval()}'><b>{report.overall_score:.0f}</b></font>",
                  s["score_big"]),
        Paragraph(
            f"<b>{tier_txt}</b><br/><font size='9' color='#475569'>"
            f"out of 100</font>",
            s["score_label"],
        ),
    ]]
    score_tbl = Table(score_data, colWidths=[3 * cm, 10 * cm], hAlign="LEFT")
    score_tbl.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(score_tbl)
    story.append(Spacer(1, 10))

    # ── Strengths & gaps ──────────────────────────────────────────────────────
    col_data = [
        [
            Paragraph("<b>✅ Strengths</b>", s["h2"]),
            Paragraph("<b>⚠️ Areas to Improve</b>", s["h2"]),
        ],
        [
            "\n".join(f"• {s_}" for s_ in report.top_strengths),
            "\n".join(f"• {g}" for g in report.top_gaps),
        ],
    ]
    # Render strengths/gaps as separate paragraphs
    half = (A4[0] - 4 * cm) / 2

    str_paras = [Paragraph("<b>✅ Strengths</b>", s["h2"])]
    for st_ in report.top_strengths:
        str_paras.append(Paragraph(f"• {st_}", s["bullet"]))

    gap_paras = [Paragraph("<b>⚠️ Areas to Improve</b>", s["h2"])]
    for g in report.top_gaps:
        gap_paras.append(Paragraph(f"• {g}", s["bullet"]))

    sg_tbl = Table([[str_paras, gap_paras]], colWidths=[half, half], hAlign="LEFT")
    sg_tbl.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",  (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(sg_tbl)
    story.append(rule)

    # ── Per-question breakdown ─────────────────────────────────────────────────
    story.append(Paragraph("📋 Per-Question Breakdown", s["h1"]))

    for i, ev in enumerate(report.evaluations):
        q_short = ev.qa_pair.question.text[:90] + ("..." if len(ev.qa_pair.question.text) > 90 else "")
        tier_c2  = _tier_colour(ev.composite_score)
        tier_t2  = _tier_text(ev.composite_score)

        story.append(Paragraph(
            f"<b>Q{i+1}:</b> {q_short}",
            s["h2"],
        ))
        story.append(Paragraph(
            f"<font color='{tier_c2.hexval()}'><b>Score: {ev.composite_score:.0f}/100 — {tier_t2}</b></font>",
            s["body"],
        ))
        story.append(Spacer(1, 4))

        # Answer excerpt
        ans_excerpt = ev.qa_pair.answer[:300] + ("..." if len(ev.qa_pair.answer) > 300 else "")
        story.append(Paragraph(f"<i>Your answer:</i> {ans_excerpt}", s["small"]))
        story.append(Spacer(1, 6))

        # ── AI Interviewer section ─────────────────────────────────────────
        if ev.llm_eval_score:
            llm = ev.llm_eval_score
            story.append(Paragraph("🤖 AI Interviewer Assessment", s["h3"]))
            metrics = [
                ("Technical Depth",    f"{llm.technical_depth:.1f}/10"),
                ("Reasoning Quality",  f"{llm.reasoning_quality:.1f}/10"),
                ("Problem Solving",    f"{llm.problem_solving:.1f}/10"),
                ("Trade-off Thinking", f"{llm.trade_off_thinking:.1f}/10"),
                ("Answer Maturity",    f"{llm.answer_maturity:.1f}/10"),
                ("Overall LLM Score",  f"{llm.overall_llm_score:.1f}/10"),
            ]
            story.append(_score_table(metrics, col_count=3))
            story.append(Spacer(1, 4))

            for label, text in [
                ("Technical",  llm.technical_feedback),
                ("Reasoning",  llm.reasoning_feedback),
                ("Trade-offs", llm.trade_off_feedback),
                ("Maturity",   llm.maturity_feedback),
            ]:
                if text:
                    story.append(Paragraph(f"<b>{label}:</b> {text}", s["small"]))

            if llm.interviewer_summary:
                story.append(Paragraph(
                    f"<i>Interviewer notes:</i> {llm.interviewer_summary}", s["small"]
                ))

            if llm.follow_up_questions:
                story.append(Paragraph("<b>Follow-up questions:</b>", s["small"]))
                for fq in llm.follow_up_questions:
                    story.append(Paragraph(f"• {fq}", s["small"]))

            story.append(Spacer(1, 6))

        # ── Rule-based section ─────────────────────────────────────────────
        if ev.rule_based_score:
            rb = ev.rule_based_score
            story.append(Paragraph("📊 Objective Metrics", s["h3"]))
            rb_metrics = [
                ("Ownership",      f"{rb.ownership_score:.1f}/10"),
                ("Impact",         f"{rb.impact_score:.1f}/10"),
                ("Skill Coverage", f"{rb.skill_coverage_pct:.0f}%"),
                ("STAR Structure", f"{rb.star_structure_score:.1f}/10"),
                ("Answer Length",  f"{rb.word_count_score:.1f}/10"),
            ]
            story.append(_score_table(rb_metrics, col_count=3))
            story.append(Spacer(1, 4))

            for fb in [rb.ownership_feedback, rb.impact_feedback,
                       rb.skill_feedback, rb.star_feedback, rb.completeness_feedback]:
                if fb:
                    story.append(Paragraph(f"• {fb}", s["small"]))

            story.append(Spacer(1, 4))

        # ── Communication section ──────────────────────────────────────────
        comm = ev.communication
        story.append(Paragraph("🗣️ Communication Analysis", s["h3"]))
        comm_metrics = [
            ("Comm Score",    f"{comm.score:.1f}/10"),
            ("Reading Ease",  f"{comm.reading_ease:.0f}/100"),
            ("Filler Words",  str(comm.filler_word_count)),
            ("Word Count",    str(comm.word_count)),
        ]
        story.append(_score_table(comm_metrics, col_count=4))
        story.append(Spacer(1, 4))

        # ── Improvement tips ───────────────────────────────────────────────
        if ev.improvement_tips:
            story.append(Paragraph("<b>Improvement tips:</b>", s["body"]))
            for tip in ev.improvement_tips:
                story.append(Paragraph(f"• {tip}", s["bullet"]))

        story.append(rule)

    # ── Recommendations ────────────────────────────────────────────────────────
    story.append(Paragraph("🎯 Recommended Next Steps", s["h1"]))
    for j, rec in enumerate(report.practice_recommendations, 1):
        story.append(Paragraph(f"{j}. {rec}", s["bullet"]))

    story.append(Spacer(1, 16))
    story.append(Paragraph(
        f"Generated by AI Interview Readiness Analyzer · {datetime.now().strftime('%d %B %Y')}",
        s["small"],
    ))

    doc.build(story)
    return buf.getvalue()
