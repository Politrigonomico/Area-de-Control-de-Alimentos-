"""
Generación de reportes PDF optimizados.
"""
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Table, TableStyle, Paragraph,
    Spacer, HRFlowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

AZUL_OSCURO  = colors.HexColor("#1a3a5c")
AZUL_MEDIO   = colors.HexColor("#2b6cb0")
GRIS_TABLA   = colors.HexColor("#f7f9fc")

def _estilos():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle("TituloDoc", fontName="Helvetica-Bold", fontSize=15, textColor=AZUL_OSCURO, alignment=TA_CENTER))
    styles.add(ParagraphStyle("CellNormal", fontName="Helvetica", fontSize=8, leading=10, alignment=TA_LEFT))
    styles.add(ParagraphStyle("CellBold", fontName="Helvetica-Bold", fontSize=8, leading=10, alignment=TA_LEFT))
    styles.add(ParagraphStyle("CellSmall", fontName="Helvetica", fontSize=7, leading=9, alignment=TA_CENTER))
    return styles

def _header(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(1.0*cm, A4[1] - 1.5*cm, "Municipalidad de Fighiera — Área de Alimentos")
    canvas.restoreState()

def _header_landscape(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(1.0*cm, landscape(A4)[1] - 1.5*cm, "Municipalidad de Fighiera — Área de Alimentos")
    canvas.restoreState()

# --- REPORTE 1: PADRÓN DE ESTABLECIMIENTOS ---
def reporte_establecimientos(session, output_path, solo_activos=True):
    from database.models import Establecimiento
    doc = SimpleDocTemplate(output_path, pagesize=A4, leftMargin=1.0*cm, rightMargin=1.0*cm, topMargin=2.5*cm)
    styles = _estilos(); story = []
    
    story.append(Paragraph("Padrón de Establecimientos", styles["TituloDoc"]))
    story.append(Spacer(1, 0.5*cm))

    q = session.query(Establecimiento)
    if solo_activos: q = q.filter(Establecimiento.baja == False)
    estabs = q.order_by(Establecimiento.codigo_establecimiento).all()

    headers = ["Código", "Nombre", "Domicilio", "Rubro", "Estado", "Monto", "Venc. Cert."]
    # Ancho total: 1.5+4.5+3.8+3.2+2.2+2.0+1.8 = 19.0 cm
    col_w   = [1.5*cm, 4.5*cm, 3.8*cm, 3.2*cm, 2.2*cm, 2.0*cm, 1.8*cm]

    data = [headers]
    for e in estabs:
        rubro = e.rubro_rel.nombre if e.rubro_rel else "—"
        cert = e.fecha_certificado.strftime("%d/%m/%Y") if e.fecha_certificado else "—"
        data.append([
            e.codigo_establecimiento or "—",
            Paragraph((e.nombre_establecimiento or "").title(), styles["CellBold"]),
            Paragraph((e.domicilio_establecimiento or "").title(), styles["CellNormal"]),
            Paragraph(rubro, styles["CellSmall"]),
            Paragraph(e.estado_tramite or "—", styles["CellSmall"]),
            f"${e.monto_total:,.2f}",
            cert
        ])

    t = Table(data, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), AZUL_OSCURO),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, GRIS_TABLA]),
        ("TOPPADDING", (0,0), (-1,-1), 5),
        ("BOTTOMPADDING", (0,0), (-1,-1), 5),
    ]))
    story.append(t)
    doc.build(story, onFirstPage=_header, onLaterPages=_header)

# --- REPORTE 2: ESTADO DE DEUDAS ---
def reporte_deudas(session, output_path, anio=None, solo_impagas=False):
    from database.models import Deuda
    doc = SimpleDocTemplate(output_path, pagesize=A4, leftMargin=1.0*cm, rightMargin=1.0*cm, topMargin=2.5*cm)
    styles = _estilos(); story = []

    story.append(Paragraph("Estado General de Deudas", styles["TituloDoc"]))
    story.append(Spacer(1, 0.5*cm))

    q = session.query(Deuda)
    if anio: q = q.filter(Deuda.anio == anio)
    if solo_impagas: q = q.filter(Deuda.pago == False)
    deudas = q.order_by(Deuda.anio.desc(), Deuda.periodo.desc(), Deuda.codigo_establecimiento).all()

    headers = ["Estab.", "Nombre Local", "Año", "Per.", "Vencimiento", "Importe", "Pagado", "Saldo"]
    col_w   = [1.6*cm, 5.6*cm, 1.2*cm, 1.2*cm, 2*cm, 2.5*cm, 1.9*cm, 3.0*cm]

    data = [headers]
    for d in deudas:
        nombre = (d.establecimiento.nombre_establecimiento or "—").title() if d.establecimiento else "—"
        venc = d.vencimiento.strftime("%d/%m/%Y") if d.vencimiento else "—"
        estado = "SÍ" if d.pago else "NO"
        data.append([
            d.codigo_establecimiento or "—",
            Paragraph(nombre, styles["CellNormal"]),
            str(d.anio or ""),
            str(d.periodo or ""),
            venc,
            f"${d.importe:,.2f}" if d.importe else "$0.00",
            estado,
            f"${float(d.saldo):,.2f}"
        ])

    t = Table(data, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), AZUL_OSCURO),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, GRIS_TABLA]),
    ]))
    story.append(t)
    doc.build(story, onFirstPage=_header, onLaterPages=_header)

# --- REPORTE 3: FICHA DE ESTABLECIMIENTO ---
def reporte_ficha_establecimiento(session, output_path, codigo_estab):
    from database.models import Establecimiento
    doc = SimpleDocTemplate(output_path, pagesize=A4, leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=2.5*cm)
    styles = _estilos(); story = []

    e = session.query(Establecimiento).get(codigo_estab)
    if not e: raise ValueError(f"Establecimiento {codigo_estab} no encontrado.")

    story.append(Paragraph(f"Ficha de Establecimiento: {e.codigo_establecimiento}", styles["TituloDoc"]))
    story.append(HRFlowable(width="100%", thickness=1, color=AZUL_MEDIO))
    story.append(Spacer(1, 0.5*cm))

    titular_nom = e.inscripto.nombre_completo if e.inscripto else "—"
    cuit = e.inscripto.numero_identificacion if e.inscripto else "—"
    rubro = e.rubro_rel.nombre if e.rubro_rel else "—"

    info_datos = [
        [Paragraph("<b>Nombre / Razón Social:</b>", styles["CellNormal"]), Paragraph((e.nombre_establecimiento or "").upper(), styles["CellNormal"])],
        [Paragraph("<b>Titular:</b>", styles["CellNormal"]), Paragraph(titular_nom.upper(), styles["CellNormal"])],
        [Paragraph("<b>CUIT Titular:</b>", styles["CellNormal"]), Paragraph(cuit, styles["CellNormal"])],
        [Paragraph("<b>Domicilio Local:</b>", styles["CellNormal"]), Paragraph(f"{e.domicilio_establecimiento or ''} - {e.localidad_establecimiento or ''}", styles["CellNormal"])],
        [Paragraph("<b>Rubro Principal:</b>", styles["CellNormal"]), Paragraph(rubro, styles["CellNormal"])],
        [Paragraph("<b>Estado Trámite:</b>", styles["CellNormal"]), Paragraph(e.estado_tramite or "—", styles["CellBold"])],
    ]

    t_info = Table(info_datos, colWidths=[4*cm, 12*cm])
    t_info.setStyle(TableStyle([("VALIGN", (0,0), (-1,-1), "TOP")]))
    story.append(t_info)
    story.append(Spacer(1, 0.5*cm))

    story.append(Paragraph("Historial de Deudas", styles["TituloDoc"]))
    if not e.deudas:
        story.append(Paragraph("No registra deudas en el sistema.", styles["CellNormal"]))
    else:
        h_deudas = ["Año", "Per.", "Vencimiento", "Importe Orig.", "Abonado", "Estado", "Saldo"]
        col_w_deudas = [1.2*cm, 1.2*cm, 2.5*cm, 3*cm, 3*cm, 2.5*cm, 3*cm]
        d_data = [h_deudas]

        deudas_ordenadas = sorted(e.deudas, key=lambda x: (x.anio or 0, x.periodo or 0), reverse=True)
        for d in deudas_ordenadas:
            venc = d.vencimiento.strftime("%d/%m/%Y") if d.vencimiento else "—"
            estado = "PAGADO" if d.pago else "IMPAGO"
            d_data.append([
                str(d.anio or ""), str(d.periodo or ""), venc,
                f"${d.importe:,.2f}" if d.importe else "$0.00",
                f"${d.monto_abonado:,.2f}" if d.monto_abonado else "$0.00",
                estado,
                f"${float(d.saldo):,.2f}"
            ])

        t_deudas = Table(d_data, colWidths=col_w_deudas, repeatRows=1)
        t_deudas.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), AZUL_MEDIO),
            ("TEXTCOLOR", (0,0), (-1,0), colors.white),
            ("ALIGN", (0,0), (-1,-1), "CENTER"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, GRIS_TABLA]),
        ]))
        story.append(t_deudas)

    doc.build(story, onFirstPage=_header, onLaterPages=_header)

# --- REPORTE 4: AUDITORÍAS ---
def reporte_auditorias(session, output_path, fecha_desde=None, fecha_hasta=None):
    from database.models import Auditoria
    doc = SimpleDocTemplate(output_path, pagesize=landscape(A4), leftMargin=1*cm, rightMargin=1*cm, topMargin=2.5*cm)
    styles = _estilos(); story = []

    story.append(Paragraph("Registro de Auditorías", styles["TituloDoc"]))
    story.append(Spacer(1, 0.5*cm))

    q = session.query(Auditoria)
    if fecha_desde: q = q.filter(Auditoria.fecha_auditoria >= fecha_desde)
    if fecha_hasta: q = q.filter(Auditoria.fecha_auditoria <= fecha_hasta)
    auditorias = q.order_by(Auditoria.fecha_auditoria.desc()).all()

    headers = ["Nº", "Establecimiento", "Fecha", "Alcances", "Conformidades", "No Conformidades"]
    col_w   = [1.2*cm, 4*cm, 2.2*cm, 6.8*cm, 6.5*cm, 6.8*cm]
    data = [headers]

    for a in auditorias:
        if not a.alcances and not a.conformidades and not a.no_conformidades: continue
        nombre = (a.establecimiento.nombre_establecimiento if a.establecimiento else a.codigo_establecimiento) or "—"
        data.append([
            str(int(a.numero_auditoria)) if a.numero_auditoria else "—",
            Paragraph(nombre.title(), styles["CellBold"]),
            a.fecha_auditoria.strftime("%d/%m/%Y") if a.fecha_auditoria else "—",
            Paragraph(a.alcances or "—", styles["CellNormal"]),
            Paragraph(a.conformidades or "—", styles["CellNormal"]),
            Paragraph(a.no_conformidades or "—", styles["CellNormal"])
        ])

    t = Table(data, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), AZUL_OSCURO),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
        ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, GRIS_TABLA]),
        ("TOPPADDING", (0,0), (-1,-1), 6),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    doc.build(story, onFirstPage=_header_landscape, onLaterPages=_header_landscape)