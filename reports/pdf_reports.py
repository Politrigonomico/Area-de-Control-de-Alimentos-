"""
Generación de reportes PDF usando ReportLab.
"""
import os
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable,
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


# ── Paleta institucional ────────────────────────────────────────────────────
AZUL_OSCURO  = colors.HexColor("#1a3a5c")
AZUL_MEDIO   = colors.HexColor("#2b6cb0")
AZUL_CLARO   = colors.HexColor("#ebf4ff")
GRIS_TABLA   = colors.HexColor("#f7f9fc")
ROJO_DEUDA   = colors.HexColor("#c0392b")
VERDE_PAGO   = colors.HexColor("#27ae60")
TEXTO_OSCURO = colors.HexColor("#1a202c")

ENCABEZADO  = "Municipalidad de Fighiera — Área de Alimentos"
LOGO_TEXTO  = "SISTEMA DE HABILITACIONES"


def _estilos():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("TituloDoc",
        fontName="Helvetica-Bold", fontSize=15,
        textColor=AZUL_OSCURO, spaceAfter=4, alignment=TA_CENTER))
    styles.add(ParagraphStyle("SubtituloDoc",
        fontName="Helvetica", fontSize=10,
        textColor=AZUL_MEDIO, spaceAfter=2, alignment=TA_CENTER))
    styles.add(ParagraphStyle("Fecha",
        fontName="Helvetica-Oblique", fontSize=8,
        textColor=colors.grey, spaceAfter=10, alignment=TA_RIGHT))
    styles.add(ParagraphStyle("SeccionTitulo",
        fontName="Helvetica-Bold", fontSize=11,
        textColor=AZUL_OSCURO, spaceBefore=14, spaceAfter=4))
    styles.add(ParagraphStyle("CeldaTabla",
        fontName="Helvetica", fontSize=8, textColor=TEXTO_OSCURO, leading=11))
    styles.add(ParagraphStyle("CeldaTablaB",
        fontName="Helvetica-Bold", fontSize=8, textColor=TEXTO_OSCURO, leading=11))
    styles.add(ParagraphStyle("Nota",
        fontName="Helvetica-Oblique", fontSize=8,
        textColor=colors.grey, spaceBefore=6))
    return styles


def _header_footer(canvas, doc):
    """Encabezado y pie de página en cada hoja."""
    canvas.saveState()
    w, h = doc.pagesize

    # Franja superior
    canvas.setFillColor(AZUL_OSCURO)
    canvas.rect(0, h - 1.8*cm, w, 1.8*cm, fill=True, stroke=False)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawCentredString(w / 2, h - 1.1*cm, ENCABEZADO)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(w / 2, h - 1.55*cm, LOGO_TEXTO)

    # Pie de página
    canvas.setFillColor(AZUL_OSCURO)
    canvas.rect(0, 0, w, 0.9*cm, fill=True, stroke=False)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica", 7)
    canvas.drawString(1*cm, 0.32*cm,
        f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    canvas.drawRightString(w - 1*cm, 0.32*cm, f"Pág. {doc.page}")

    canvas.restoreState()


def _estilo_tabla_base(col_widths, header_rows=1):
    return TableStyle([
        # Encabezado
        ("BACKGROUND",    (0, 0), (-1, header_rows - 1), AZUL_OSCURO),
        ("TEXTCOLOR",     (0, 0), (-1, header_rows - 1), colors.white),
        ("FONTNAME",      (0, 0), (-1, header_rows - 1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, header_rows - 1), 8),
        ("ALIGN",         (0, 0), (-1, header_rows - 1), "CENTER"),
        # Cuerpo
        ("FONTNAME",      (0, header_rows), (-1, -1), "Helvetica"),
        ("FONTSIZE",      (0, header_rows), (-1, -1), 8),
        ("ROWBACKGROUNDS",(0, header_rows), (-1, -1), [colors.white, GRIS_TABLA]),
        ("GRID",          (0, 0), (-1, -1), 0.3, colors.HexColor("#d0d7e3")),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("LEFTPADDING",   (0, 0), (-1, -1), 5),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 5),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ])


# ── Reporte 1: Padrón de Establecimientos ───────────────────────────────────

def reporte_establecimientos(session, output_path: str, solo_activos=True):
    from database.models import Establecimiento, Rubro

    doc = SimpleDocTemplate(
        output_path, pagesize=landscape(A4),
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=2.5*cm, bottomMargin=1.5*cm,
    )
    styles = _estilos()
    story  = []

    story.append(Paragraph("Padrón de Establecimientos", styles["TituloDoc"]))
    filtro = "Solo activos" if solo_activos else "Todos (incluye bajas)"
    story.append(Paragraph(filtro, styles["SubtituloDoc"]))
    story.append(Paragraph(datetime.now().strftime("%d/%m/%Y"), styles["Fecha"]))
    story.append(HRFlowable(width="100%", thickness=1, color=AZUL_MEDIO))
    story.append(Spacer(1, 0.3*cm))

    q = session.query(Establecimiento)
    if solo_activos:
        q = q.filter(Establecimiento.baja == False)
    q = q.order_by(Establecimiento.codigo_establecimiento)
    establecimientos = q.all()

    headers = ["Código", "Nombre", "Domicilio", "Rubro", "Estado", "Monto Total", "Certificado"]
    col_w   = [2*cm, 6*cm, 5*cm, 4*cm, 2.5*cm, 2.5*cm, 2.8*cm]

    data = [headers]
    for e in establecimientos:
        rubro_nombre = e.rubro_rel.nombre if e.rubro_rel else "—"
        domicilio = f"{e.domicilio_establecimiento or ''} {e.numero_establecimiento or ''}".strip()
        cert = e.fecha_certificado.strftime("%d/%m/%Y") if e.fecha_certificado else "—"
        data.append([
            e.codigo_establecimiento,
            (e.nombre_establecimiento or "—").title()[:45],
            domicilio[:40] or "—",
            rubro_nombre[:35],
            e.estado_tramite or "—",
            f"$ {e.monto_total:,.2f}",
            cert,
        ])

    t = Table(data, colWidths=col_w, repeatRows=1)
    t.setStyle(_estilo_tabla_base(col_w))
    story.append(t)
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"Total registros: {len(establecimientos)}", styles["Nota"]))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return output_path


# ── Reporte 2: Estado de Deudas ─────────────────────────────────────────────

def reporte_deudas(session, output_path: str, anio=None, solo_impagas=False):
    from database.models import Deuda, Establecimiento
    from sqlalchemy import func

    doc = SimpleDocTemplate(
        output_path, pagesize=landscape(A4),
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=2.5*cm, bottomMargin=1.5*cm,
    )
    styles = _estilos()
    story  = []

    titulo_filtro = f"Año {anio}" if anio else "Todos los períodos"
    if solo_impagas:
        titulo_filtro += " — Solo deudas impagas"
    story.append(Paragraph("Estado de Deudas", styles["TituloDoc"]))
    story.append(Paragraph(titulo_filtro, styles["SubtituloDoc"]))
    story.append(Paragraph(datetime.now().strftime("%d/%m/%Y"), styles["Fecha"]))
    story.append(HRFlowable(width="100%", thickness=1, color=AZUL_MEDIO))
    story.append(Spacer(1, 0.3*cm))

    q = session.query(Deuda)
    if anio:
        q = q.filter(Deuda.anio == anio)
    if solo_impagas:
        q = q.filter(Deuda.pago == False)
    q = q.order_by(Deuda.anio, Deuda.periodo, Deuda.codigo_establecimiento)
    deudas = q.all()

    headers = ["Cód. Estab.", "Establecimiento", "Año", "Per.", "Vencimiento", "Importe", "Pagado", "Saldo"]
    col_w   = [2.2*cm, 6*cm, 1.5*cm, 1.2*cm, 3*cm, 2.8*cm, 2.8*cm, 2.8*cm]

    total_importe = 0.0
    total_saldo   = 0.0
    data = [headers]

    for d in deudas:
        nombre = "—"
        if d.establecimiento:
            nombre = (d.establecimiento.nombre_establecimiento or "—").title()[:40]
        venc = d.vencimiento.strftime("%d/%m/%Y") if d.vencimiento else "—"
        saldo = d.saldo
        total_importe += d.importe or 0
        total_saldo   += saldo
        row = [
            d.codigo_establecimiento,
            nombre,
            str(d.anio or ""),
            str(d.periodo or ""),
            venc,
            f"$ {d.importe:,.2f}",
            "✓" if d.pago else "✗",
            f"$ {saldo:,.2f}",
        ]
        data.append(row)

    # Fila de totales
    data.append(["", f"TOTALES ({len(deudas)} registros)", "", "", "",
                  f"$ {total_importe:,.2f}", "", f"$ {total_saldo:,.2f}"])

    t = Table(data, colWidths=col_w, repeatRows=1)
    style = _estilo_tabla_base(col_w)
    # Colorear estado pago
    for i, d in enumerate(deudas, start=1):
        col_pago = 6
        if d.pago:
            style.add("TEXTCOLOR", (col_pago, i), (col_pago, i), VERDE_PAGO)
            style.add("FONTNAME",  (col_pago, i), (col_pago, i), "Helvetica-Bold")
        else:
            style.add("TEXTCOLOR", (col_pago, i), (col_pago, i), ROJO_DEUDA)
            style.add("FONTNAME",  (col_pago, i), (col_pago, i), "Helvetica-Bold")
    # Fila totales
    last = len(data) - 1
    style.add("BACKGROUND", (0, last), (-1, last), AZUL_CLARO)
    style.add("FONTNAME",   (0, last), (-1, last), "Helvetica-Bold")
    t.setStyle(style)

    story.append(t)
    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return output_path


# ── Reporte 3: Ficha individual de establecimiento ──────────────────────────

def reporte_ficha_establecimiento(session, output_path: str, codigo: str):
    from database.models import Establecimiento, Deuda, Auditoria, Sanidad

    e = session.query(Establecimiento).get(codigo.upper())
    if not e:
        raise ValueError(f"Establecimiento '{codigo}' no encontrado.")

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2.5*cm, bottomMargin=1.5*cm,
    )
    styles = _estilos()
    story  = []

    story.append(Paragraph(
        f"Ficha de Establecimiento — {e.codigo_establecimiento}", styles["TituloDoc"]))
    story.append(Paragraph(
        (e.nombre_establecimiento or "").upper(), styles["SubtituloDoc"]))
    story.append(Paragraph(datetime.now().strftime("%d/%m/%Y"), styles["Fecha"]))
    story.append(HRFlowable(width="100%", thickness=1, color=AZUL_MEDIO))
    story.append(Spacer(1, 0.4*cm))

    # Datos generales
    story.append(Paragraph("Datos del establecimiento", styles["SeccionTitulo"]))
    inscripto = e.inscripto
    titular = inscripto.nombre_completo if inscripto else "—"
    rubro = e.rubro_rel.nombre if e.rubro_rel else "—"
    domicilio = f"{e.domicilio_establecimiento or ''} {e.numero_establecimiento or ''}".strip() or "—"
    cert = e.fecha_certificado.strftime("%d/%m/%Y") if e.fecha_certificado else "—"

    datos = [
        ["Titular:", titular, "Estado:", e.estado_tramite or "—"],
        ["Domicilio:", domicilio, "Localidad:", e.localidad_establecimiento or "—"],
        ["Teléfono:", e.telefono_establecimiento or "—", "Cod. Postal:", str(e.codigo_postal or "")],
        ["Rubro:", rubro, "Monto Total:", f"$ {e.monto_total:,.2f}"],
        ["Cert. Inscripción:", cert, "Baja:", "Sí" if e.baja else "No"],
    ]
    tg = Table(datos, colWidths=[3.5*cm, 7*cm, 3*cm, 4*cm])
    tg.setStyle(TableStyle([
        ("FONTNAME",  (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME",  (2, 0), (2, -1), "Helvetica-Bold"),
        ("FONTSIZE",  (0, 0), (-1, -1), 9),
        ("TEXTCOLOR", (0, 0), (0, -1), AZUL_OSCURO),
        ("TEXTCOLOR", (2, 0), (2, -1), AZUL_OSCURO),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, GRIS_TABLA]),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
    ]))
    story.append(tg)

    # Deudas
    story.append(Paragraph("Historial de Deudas", styles["SeccionTitulo"]))
    deudas = (session.query(Deuda)
              .filter_by(codigo_establecimiento=codigo.upper())
              .order_by(Deuda.anio, Deuda.periodo).all())
    if deudas:
        dh = ["Año", "Per.", "Vencimiento", "Importe", "Estado", "Saldo"]
        dd = [dh]
        for d in deudas:
            venc = d.vencimiento.strftime("%d/%m/%Y") if d.vencimiento else "—"
            dd.append([
                str(d.anio or ""), str(d.periodo or ""), venc,
                f"$ {d.importe:,.2f}",
                "PAGADO" if d.pago else "IMPAGO",
                f"$ {d.saldo:,.2f}",
            ])
        td = Table(dd, colWidths=[1.5*cm, 1.2*cm, 3.2*cm, 3.2*cm, 2.8*cm, 3.2*cm], repeatRows=1)
        st = _estilo_tabla_base([])
        for i, d in enumerate(deudas, 1):
            c = VERDE_PAGO if d.pago else ROJO_DEUDA
            st.add("TEXTCOLOR", (4, i), (4, i), c)
            st.add("FONTNAME",  (4, i), (4, i), "Helvetica-Bold")
        td.setStyle(st)
        story.append(td)
    else:
        story.append(Paragraph("Sin deudas registradas.", styles["Nota"]))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return output_path


# ── Reporte 4: Auditorías ────────────────────────────────────────────────────

def reporte_auditorias(session, output_path: str):
    from database.models import Auditoria

    doc = SimpleDocTemplate(
        output_path, pagesize=landscape(A4),
        leftMargin=1.5*cm, rightMargin=1.5*cm,
        topMargin=2.5*cm, bottomMargin=1.5*cm,
    )
    styles = _estilos()
    story  = []

    story.append(Paragraph("Registro de Auditorías", styles["TituloDoc"]))
    story.append(Paragraph(datetime.now().strftime("%d/%m/%Y"), styles["Fecha"]))
    story.append(HRFlowable(width="100%", thickness=1, color=AZUL_MEDIO))
    story.append(Spacer(1, 0.3*cm))

    auditorias = (session.query(Auditoria)
                  .order_by(Auditoria.fecha_auditoria.desc()).all())

    headers = ["Nº", "Establecimiento", "Fecha", "Alcances", "Conformidades", "No Conformidades"]
    col_w   = [1.5*cm, 5*cm, 3*cm, 7*cm, 4.5*cm, 6*cm]

    data = [headers]
    for a in auditorias:
        nombre = "—"
        if a.establecimiento:
            nombre = (a.establecimiento.nombre_establecimiento or a.codigo_establecimiento or "—").title()[:40]
        elif a.codigo_establecimiento:
            nombre = a.codigo_establecimiento
        fecha = a.fecha_auditoria.strftime("%d/%m/%Y") if a.fecha_auditoria else "—"
        data.append([
            str(int(a.numero_auditoria)) if a.numero_auditoria else "—",
            nombre,
            fecha,
            (a.alcances or "—")[:80],
            (a.conformidades or "—")[:50],
            (a.no_conformidades or "—")[:80],
        ])

    t = Table(data, colWidths=col_w, repeatRows=1)
    t.setStyle(_estilo_tabla_base(col_w))
    story.append(t)
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(f"Total auditorías: {len(auditorias)}", styles["Nota"]))

    doc.build(story, onFirstPage=_header_footer, onLaterPages=_header_footer)
    return output_path
