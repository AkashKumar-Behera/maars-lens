"""
MAARS Lens: Multi-format Inspection Report Export Service
Generates:
1. PDF (ReportLab with Devanagari Hindi font support and QR code verification link)
2. DOCX (python-docx)
3. XLSX (openpyxl)
"""
import os
import hashlib
import json
import uuid
import datetime
from io import BytesIO
from typing import Any, Dict, Optional, List

# ReportLab imports
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget

# Try registering Hindi / Devanagari font (Windows Nirmala or system Noto Sans)
HINDI_FONT_NAME = "Helvetica"
HINDI_BOLD_FONT_NAME = "Helvetica-Bold"

for candidate_path in [
    "C:/Windows/Fonts/Nirmala.ttc",
    "C:/Windows/Fonts/nirmala.ttf",
    "C:/Windows/Fonts/Mangal.ttf",
    "/usr/share/fonts/truetype/noto/NotoSansDevanagari-Regular.ttf",
]:
    if os.path.exists(candidate_path):
        try:
            if candidate_path.endswith(".ttc"):
                pdfmetrics.registerFont(TTFont("HindiFont", candidate_path, subfontIndex=0))
            else:
                pdfmetrics.registerFont(TTFont("HindiFont", candidate_path))
            HINDI_FONT_NAME = "HindiFont"
            HINDI_BOLD_FONT_NAME = "HindiFont"
            break
        except Exception:
            pass


def _canonicalize_value(val: Any) -> Any:
    """Recursively converts values to JSON-serializable canonical types."""
    if isinstance(val, (uuid.UUID,)):
        return str(val)
    elif isinstance(val, (datetime.datetime, datetime.date)):
        return val.isoformat()
    elif isinstance(val, dict):
        return {str(k): _canonicalize_value(v) for k, v in sorted(val.items())}
    elif isinstance(val, (list, tuple, set)):
        return [_canonicalize_value(item) for item in val]
    elif isinstance(val, (float, int, str, bool)) or val is None:
        return val
    else:
        return str(val)


def compute_report_hash(inspection_data: Dict[str, Any]) -> str:
    """Computes canonical deterministic SHA-256 report hash."""
    canonical_data = _canonicalize_value(inspection_data)
    if isinstance(canonical_data, dict):
        canonical_data.pop("report_hash", None)
        canonical_data.pop("signature_hash_at_finalization", None)

    serialized = json.dumps(canonical_data, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"sha256:{digest}"


def generate_report_pdf(inspection_data: Dict[str, Any]) -> bytes:
    """
    Generates a structured, tamper-evident PDF report with:
    - Hindi font support
    - Verification QR code
    - Numeral font height guideline table with disclaimer
    - Statutory footer with disclaimer
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName=HINDI_BOLD_FONT_NAME,
        fontSize=16,
        leading=20,
        textColor=colors.HexColor("#1e293b"),
        spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName=HINDI_FONT_NAME,
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#64748b"),
        spaceAfter=10,
    )
    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName=HINDI_BOLD_FONT_NAME,
        fontSize=11,
        leading=15,
        textColor=colors.HexColor("#0f172a"),
        spaceBefore=8,
        spaceAfter=4,
    )
    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName=HINDI_FONT_NAME,
        fontSize=8.5,
        leading=11,
    )
    bold_cell_style = ParagraphStyle(
        "BoldTableCell",
        parent=styles["Normal"],
        fontName=HINDI_BOLD_FONT_NAME,
        fontSize=8.5,
        leading=11,
    )
    footer_style = ParagraphStyle(
        "DisclaimerFooter",
        parent=styles["Normal"],
        fontName=HINDI_FONT_NAME,
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748b"),
    )

    elements = []

    # 1. Header
    elements.append(Paragraph("MAARS LENS — STATUTORY INSPECTION REPORT / निरीक्षण रिपोर्ट", title_style))
    elements.append(Paragraph("Legal Metrology (Packaged Commodities) Rules, 2011 — Prototype Compliance Verification", subtitle_style))

    # 2. Metadata Table + QR Code
    insp_id = str(inspection_data.get("id") or inspection_data.get("inspection_id") or "N/A")
    officer_id = str(inspection_data.get("officer_id") or "N/A")
    product_name = str(inspection_data.get("product_name") or "Unknown Product")
    brand_name = str(inspection_data.get("brand_name") or "Unknown Brand")
    final_compliance = str(inspection_data.get("final_compliance") or inspection_data.get("compliance_status") or "PENDING").upper()
    report_hash = str(inspection_data.get("report_hash") or compute_report_hash(inspection_data))

    meta_data = [
        [Paragraph("Inspection ID", bold_cell_style), Paragraph(insp_id, cell_style)],
        [Paragraph("Officer ID", bold_cell_style), Paragraph(officer_id, cell_style)],
        [Paragraph("Product Name", bold_cell_style), Paragraph(product_name, cell_style)],
        [Paragraph("Brand Name", bold_cell_style), Paragraph(brand_name, cell_style)],
        [Paragraph("Final Compliance", bold_cell_style), Paragraph(final_compliance, bold_cell_style)],
        [Paragraph("Report Hash (SHA-256)", bold_cell_style), Paragraph(report_hash, cell_style)],
    ]

    meta_table = Table(meta_data, colWidths=[130, 310])
    meta_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ])
    )

    # QR Code linking to verification endpoint
    verify_url = f"https://maars-lens.gov.in/verify/{insp_id}?hash={report_hash[:16]}"
    qr_widget = QrCodeWidget(verify_url)
    qr_widget.barWidth = 70
    qr_widget.barHeight = 70
    qr_widget.qrVersion = 1
    qr_drawing = Drawing(75, 75)
    qr_drawing.add(qr_widget)

    # Place meta table and QR code side-by-side
    header_table = Table([[meta_table, qr_drawing]], colWidths=[450, 85])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
    ]))
    elements.append(header_table)
    elements.append(Spacer(1, 10))

    # 3. Audit Results Table
    elements.append(Paragraph("Statutory Rule Audit Evaluations", section_heading))
    audit_results = inspection_data.get("audit_results") or []

    audit_headers = [
        Paragraph("Rule Code", bold_cell_style),
        Paragraph("Statutory Ref", bold_cell_style),
        Paragraph("Automated", bold_cell_style),
        Paragraph("Manual Review", bold_cell_style),
        Paragraph("Effective", bold_cell_style),
    ]
    audit_table_data = [audit_headers]

    if audit_results:
        for res in audit_results:
            if isinstance(res, dict):
                rule_code = str(res.get("rule_code", "N/A"))
                stat_ref = str(res.get("statutory_reference", "N/A"))
                auto_res = str(res.get("automated_result", "N/A"))
                man_res = str(res.get("manual_review_result") or "—")
                eff_res = str(res.get("effective_result", "N/A"))
            else:
                rule_code = getattr(res, "rule_code", "N/A")
                stat_ref = getattr(res, "statutory_reference", "N/A")
                auto_res = getattr(res, "automated_result", "N/A")
                man_res = getattr(res, "manual_review_result", "—") or "—"
                eff_res = getattr(res, "effective_result", "N/A")

            audit_table_data.append([
                Paragraph(rule_code, cell_style),
                Paragraph(stat_ref[:35], cell_style),
                Paragraph(str(auto_res), cell_style),
                Paragraph(str(man_res), cell_style),
                Paragraph(str(eff_res), bold_cell_style),
            ])
    else:
        audit_table_data.append([
            Paragraph("No rule evaluations recorded.", cell_style),
            Paragraph("—", cell_style),
            Paragraph("—", cell_style),
            Paragraph("—", cell_style),
            Paragraph("—", cell_style),
        ])

    audit_table = Table(audit_table_data, colWidths=[110, 155, 85, 95, 85])
    audit_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e2e8f0")),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ])
    )
    elements.append(audit_table)
    elements.append(Spacer(1, 10))

    # 4. Required Font Height Comparison Table (Rule 7 Guidance)
    elements.append(Paragraph("Required Minimum Numeral Height Table (Rule 7 Reference)", section_heading))
    font_table_data = [
        [
            Paragraph("Net Quantity Band (Weight / Volume)", bold_cell_style),
            Paragraph("Minimum Height (Normal)", bold_cell_style),
            Paragraph("Blown/Molded/Perforated", bold_cell_style),
        ],
        [Paragraph("Up to 50 g / ml", cell_style), Paragraph("1.0 mm", cell_style), Paragraph("2.0 mm", cell_style)],
        [Paragraph("50 g / ml to 200 g / ml", cell_style), Paragraph("2.0 mm", cell_style), Paragraph("4.0 mm", cell_style)],
        [Paragraph("200 g / ml to 1000 g / ml (1 kg / 1 L)", cell_style), Paragraph("4.0 mm", cell_style), Paragraph("6.0 mm", cell_style)],
        [Paragraph("More than 1000 g / ml (1 kg / 1 L)", cell_style), Paragraph("6.0 mm", cell_style), Paragraph("6.0 mm", cell_style)],
    ]
    font_table = Table(font_table_data, colWidths=[240, 145, 145])
    font_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ])
    )
    elements.append(font_table)
    elements.append(Spacer(1, 6))
    elements.append(Paragraph("<i>Note: Font height measurement from camera images is an estimate and requires physical gauge verification before legal proceedings.</i>", footer_style))
    elements.append(Spacer(1, 10))

    # 5. Tamper Evidence Seal & Legal Verification Footer
    elements.append(Paragraph("Tamper-Evidence & Finalization Seal", section_heading))
    seal_text = (
        f"Cryptographic SHA-256 seal: <b>{report_hash}</b>. "
        f"Scan the QR code to verify certificate authenticity on the enforcement portal.<br/>"
        f"<b>Thresholds and rule codes shown are subject to legal verification (legal_verified=false) "
        f"under the Legal Metrology Act, 2009 and Packaged Commodities Rules, 2011.</b>"
    )
    elements.append(Paragraph(seal_text, footer_style))

    doc.build(elements)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes


def generate_report_docx(inspection_data: Dict[str, Any]) -> bytes:
    """Generates a structured Word DOCX report matching the PDF report content."""
    import docx
    from docx.shared import Inches, Pt, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = docx.Document()

    # Title
    p_title = doc.add_paragraph()
    p_title.paragraph_format.space_after = Pt(2)
    run_title = p_title.add_run("MAARS LENS — STATUTORY INSPECTION REPORT")
    run_title.font.name = "Calibri"
    run_title.font.size = Pt(16)
    run_title.bold = True
    run_title.font.color.rgb = RGBColor(30, 41, 59)

    p_sub = doc.add_paragraph()
    p_sub.paragraph_format.space_after = Pt(12)
    run_sub = p_sub.add_run("Legal Metrology (Packaged Commodities) Rules, 2011 — Prototype Compliance Verification")
    run_sub.font.name = "Calibri"
    run_sub.font.size = Pt(9)
    run_sub.font.color.rgb = RGBColor(100, 116, 139)

    # Metadata Table
    insp_id = str(inspection_data.get("id") or inspection_data.get("inspection_id") or "N/A")
    officer_id = str(inspection_data.get("officer_id") or "N/A")
    product_name = str(inspection_data.get("product_name") or "Unknown Product")
    brand_name = str(inspection_data.get("brand_name") or "Unknown Brand")
    final_compliance = str(inspection_data.get("final_compliance") or inspection_data.get("compliance_status") or "PENDING").upper()
    report_hash = str(inspection_data.get("report_hash") or compute_report_hash(inspection_data))

    meta_table = doc.add_table(rows=6, cols=2)
    meta_table.style = 'Light Shading'
    meta_items = [
        ("Inspection ID", insp_id),
        ("Officer ID", officer_id),
        ("Product Name", product_name),
        ("Brand Name", brand_name),
        ("Final Compliance", final_compliance),
        ("Report Hash (SHA-256)", report_hash),
    ]
    for idx, (lbl, val) in enumerate(meta_items):
        meta_table.cell(idx, 0).paragraphs[0].text = lbl
        meta_table.cell(idx, 1).paragraphs[0].text = val

    doc.add_paragraph().paragraph_format.space_after = Pt(6)

    # Audit Results
    h_audit = doc.add_heading("Statutory Rule Audit Evaluations", level=2)
    audit_results = inspection_data.get("audit_results") or []

    ar_table = doc.add_table(rows=len(audit_results) + 1, cols=5)
    ar_table.style = 'Light Shading Accent 1'
    headers = ["Rule Code", "Statutory Reference", "Automated Result", "Manual Review", "Effective Result"]
    for c_idx, h in enumerate(headers):
        ar_table.cell(0, c_idx).paragraphs[0].text = h

    for r_idx, ar in enumerate(audit_results):
        row = r_idx + 1
        if isinstance(ar, dict):
            ar_table.cell(row, 0).paragraphs[0].text = str(ar.get("rule_code", "N/A"))
            ar_table.cell(row, 1).paragraphs[0].text = str(ar.get("statutory_reference", "N/A"))
            ar_table.cell(row, 2).paragraphs[0].text = str(ar.get("automated_result", "N/A"))
            ar_table.cell(row, 3).paragraphs[0].text = str(ar.get("manual_review_result") or "—")
            ar_table.cell(row, 4).paragraphs[0].text = str(ar.get("effective_result", "N/A"))
        else:
            ar_table.cell(row, 0).paragraphs[0].text = str(getattr(ar, "rule_code", "N/A"))
            ar_table.cell(row, 1).paragraphs[0].text = str(getattr(ar, "statutory_reference", "N/A"))
            ar_table.cell(row, 2).paragraphs[0].text = str(getattr(ar, "automated_result", "N/A"))
            ar_table.cell(row, 3).paragraphs[0].text = str(getattr(ar, "manual_review_result", "—") or "—")
            ar_table.cell(row, 4).paragraphs[0].text = str(getattr(ar, "effective_result", "N/A"))

    doc.add_paragraph().paragraph_format.space_after = Pt(12)

    # Footer notice
    p_foot = doc.add_paragraph()
    r_foot = p_foot.add_run(
        f"Cryptographic SHA-256 seal: {report_hash}.\n"
        f"Thresholds and rule codes shown are subject to legal verification (legal_verified=false) "
        f"under the Legal Metrology Act, 2009 and Packaged Commodities Rules, 2011.\n"
        f"Font height measurement from camera images is an estimate and requires physical gauge verification."
    )
    r_foot.font.size = Pt(8.5)
    r_foot.font.italic = True
    r_foot.font.color.rgb = RGBColor(100, 116, 139)

    out = BytesIO()
    doc.save(out)
    return out.getvalue()


def generate_report_xlsx(inspection_data: Dict[str, Any]) -> bytes:
    """Generates an Excel XLSX report matching the inspection report details."""
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Inspection Report"

    # Styles
    title_font = Font(name="Calibri", size=14, bold=True, color="1E293B")
    header_fill = PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid")
    header_font = Font(name="Calibri", size=10, bold=True)
    regular_font = Font(name="Calibri", size=10)
    bold_font = Font(name="Calibri", size=10, bold=True)

    ws["A1"] = "MAARS LENS — STATUTORY INSPECTION REPORT"
    ws["A1"].font = title_font
    ws["A2"] = "Legal Metrology (Packaged Commodities) Rules, 2011 — Prototype Compliance Verification"
    ws["A2"].font = Font(name="Calibri", size=9, italic=True, color="64748B")

    # Metadata
    insp_id = str(inspection_data.get("id") or inspection_data.get("inspection_id") or "N/A")
    officer_id = str(inspection_data.get("officer_id") or "N/A")
    product_name = str(inspection_data.get("product_name") or "Unknown Product")
    brand_name = str(inspection_data.get("brand_name") or "Unknown Brand")
    final_compliance = str(inspection_data.get("final_compliance") or inspection_data.get("compliance_status") or "PENDING").upper()
    report_hash = str(inspection_data.get("report_hash") or compute_report_hash(inspection_data))

    meta = [
        ("Inspection ID", insp_id),
        ("Officer ID", officer_id),
        ("Product Name", product_name),
        ("Brand Name", brand_name),
        ("Final Compliance", final_compliance),
        ("Report Hash", report_hash),
    ]

    for idx, (k, v) in enumerate(meta, start=4):
        ws.cell(row=idx, column=1, value=k).font = bold_font
        ws.cell(row=idx, column=2, value=v).font = regular_font

    # Audit table
    start_row = 11
    ws.cell(row=start_row, column=1, value="Statutory Rule Audit Evaluations").font = title_font

    headers = ["Rule Code", "Statutory Reference", "Automated Result", "Manual Review", "Effective Result"]
    for col_idx, h in enumerate(headers, start=1):
        cell = ws.cell(row=start_row + 1, column=col_idx, value=h)
        cell.fill = header_fill
        cell.font = header_font

    audit_results = inspection_data.get("audit_results") or []
    for r_idx, ar in enumerate(audit_results, start=start_row + 2):
        if isinstance(ar, dict):
            ws.cell(row=r_idx, column=1, value=str(ar.get("rule_code", "N/A"))).font = regular_font
            ws.cell(row=r_idx, column=2, value=str(ar.get("statutory_reference", "N/A"))).font = regular_font
            ws.cell(row=r_idx, column=3, value=str(ar.get("automated_result", "N/A"))).font = regular_font
            ws.cell(row=r_idx, column=4, value=str(ar.get("manual_review_result") or "—")).font = regular_font
            ws.cell(row=r_idx, column=5, value=str(ar.get("effective_result", "N/A"))).font = bold_font
        else:
            ws.cell(row=r_idx, column=1, value=str(getattr(ar, "rule_code", "N/A"))).font = regular_font
            ws.cell(row=r_idx, column=2, value=str(getattr(ar, "statutory_reference", "N/A"))).font = regular_font
            ws.cell(row=r_idx, column=3, value=str(getattr(ar, "automated_result", "N/A"))).font = regular_font
            ws.cell(row=r_idx, column=4, value=str(getattr(ar, "manual_review_result", "—") or "—")).font = regular_font
            ws.cell(row=r_idx, column=5, value=str(getattr(ar, "effective_result", "N/A"))).font = bold_font

    # Column widths
    ws.column_dimensions["A"].width = 24
    ws.column_dimensions["B"].width = 32
    ws.column_dimensions["C"].width = 18
    ws.column_dimensions["D"].width = 18
    ws.column_dimensions["E"].width = 18

    out = BytesIO()
    wb.save(out)
    return out.getvalue()
