"""
Documentos institucionales PDF — Área de Alimentos, Comuna de Fighiera
Replica exacta de los formularios originales del sistema viejo.

Documentos:
  1. Acta de Auditoría
  2. Recibo de Pago de Inicio de Trámite
  3. Recibo de Tasa de Inscripción Área de Alimentos
  4. Detalle de Deuda / Recibo con intereses
"""
from datetime import datetime
import locale

# Intentar configurar locale español; si falla usar mapeo manual
_DIAS_ES   = ["lunes","martes","miércoles","jueves","viernes","sábado","domingo"]
_MESES_ES  = ["enero","febrero","marzo","abril","mayo","junio",
               "julio","agosto","septiembre","octubre","noviembre","diciembre"]

def _fecha_larga_es(dt=None):
    if dt is None:
        dt = datetime.now()
    dia_nombre = _DIAS_ES[dt.weekday()]
    mes_nombre = _MESES_ES[dt.month - 1]
    return f"{dia_nombre}, {dt.day} de {mes_nombre} de {dt.year}"
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether,
)
from reportlab.pdfgen import canvas as pdfcanvas
from reportlab.lib.utils import ImageReader

# ── Constantes institucionales ───────────────────────────────────────────────
INSTITUCION   = "Comuna de Fighiera"
AREA          = "Área de Alimentos"
DIRECCION     = "Rivadavia Nº 895  -  Fighiera  -  2126  -  Santa Fe"
TELEFONO      = "Teléfono: (03402) 470731"
EMAIL         = "e-mail: assalfighiera@yahoo.com.ar"
TASA_MENSUAL  = 3  # % mensual de interés por mora

# Logo institucional
import os as _os_logo
LOGO_PATH = _os_logo.path.join(_os_logo.path.dirname(_os_logo.path.abspath(__file__)), "logo_comuna.png")

# Carpeta donde se guardan todos los PDFs generados automáticamente
import os as _os
PDF_DIR = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))),
                        "pdfs_generados")
_os.makedirs(PDF_DIR, exist_ok=True)

def _auto_path(nombre_archivo: str) -> str:
    """Genera ruta automática dentro de pdfs_generados/."""
    return _os.path.join(PDF_DIR, nombre_archivo)

def abrir_pdf(path: str):
    """Abre el PDF con el visor del sistema sin diálogo de guardado."""
    import subprocess, sys
    if sys.platform.startswith("win"):
        _os.startfile(path)
    elif sys.platform.startswith("darwin"):
        subprocess.Popen(["open", path])
    else:
        subprocess.Popen(["xdg-open", path])

# ── Colores ──────────────────────────────────────────────────────────────────
AZUL      = colors.HexColor("#1a3a5c")
AZUL_CLARO= colors.HexColor("#dce8f5")
NEGRO     = colors.black
GRIS      = colors.HexColor("#555555")
GRIS_FILA = colors.HexColor("#f2f2f2")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _fmt_fecha(dt):
    if not dt:
        return ""
    return dt.strftime("%d/%m/%Y")

def _fmt_moneda(v):
    if v is None:
        return "$ 0,00"
    return f"$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

def _meses_mora(vencimiento: datetime) -> int:
    hoy = datetime.now()
    if hoy <= vencimiento:
        return 0
    return (hoy.year - vencimiento.year) * 12 + (hoy.month - vencimiento.month)

def _calcular_interes(importe: float, vencimiento: datetime):
    """Calcula intereses desde la fecha de vencimiento original (verificado con docs reales)."""
    meses = _meses_mora(vencimiento)
    int_acum = meses * TASA_MENSUAL
    actualizado = importe * (1 + int_acum / 100)
    return meses, int_acum, actualizado

def _cabecera_institucional(story, titulo: str, styles):
    """Bloque de encabezado común a todos los documentos — con logo."""
    from reportlab.platypus import Image as RLImage

    # Columna izquierda: logo + datos institucionales
    col_izq = []

    # Logo (si existe el archivo)
    if _os_logo.path.exists(LOGO_PATH):
        # 212x238px original — mostramos a 1.4cm de alto proporcional
        logo_h = 1.4 * cm
        logo_w = logo_h * (212 / 238)
        logo_img = RLImage(LOGO_PATH, width=logo_w, height=logo_h)
        # Combinar logo e institución en una tabla interna
        inst_txt = Paragraph(
            f"<b>{INSTITUCION}</b><br/>"
            f"<font size='10'>{AREA}</font><br/>"
            f"<font size='8'>{DIRECCION}</font><br/>"
            f"<font size='8'>{TELEFONO}</font>",
            ParagraphStyle("hdr", fontName="Helvetica", fontSize=12, leading=16)
        )
        inner = Table([[logo_img, inst_txt]],
                      colWidths=[logo_w + 0.3*cm, 10*cm - logo_w])
        inner.setStyle(TableStyle([
            ("VALIGN",       (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING",  (1,0), (1,0),   6),
            ("RIGHTPADDING", (0,0), (-1,-1), 0),
            ("TOPPADDING",   (0,0), (-1,-1), 0),
            ("BOTTOMPADDING",(0,0), (-1,-1), 0),
        ]))
        col_izq_cell = inner
    else:
        col_izq_cell = Paragraph(
            f"<b>{INSTITUCION}</b><br/>"
            f"<font size='10'>{AREA}</font><br/>"
            f"<font size='8'>{DIRECCION}</font><br/>"
            f"<font size='8'>{TELEFONO}</font>",
            ParagraphStyle("hdr", fontName="Helvetica", fontSize=12, leading=16)
        )

    header_data = [[
        col_izq_cell,
        Paragraph(
            f"<b>{titulo}</b>",
            ParagraphStyle("tit", fontName="Helvetica-Bold", fontSize=14,
                           leading=18, alignment=TA_RIGHT, textColor=AZUL)
        ),
    ]]
    t = Table(header_data, colWidths=[11*cm, 7*cm])
    t.setStyle(TableStyle([
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
        ("BOTTOMPADDING", (0,0), (-1,-1), 6),
    ]))
    story.append(t)
    story.append(HRFlowable(width="100%", thickness=1.5, color=AZUL, spaceAfter=8))

def _pie_pagina(canvas_obj, doc):
    canvas_obj.saveState()
    w, h = A4
    canvas_obj.setFillColor(GRIS)
    canvas_obj.setFont("Helvetica-Oblique", 7)
    canvas_obj.drawCentredString(w/2, 1.2*cm, EMAIL)
    canvas_obj.restoreState()

def _campo(label, valor, bold_valor=True):
    """Línea de campo: 'Label: **Valor**'"""
    peso = "b" if bold_valor else ""
    return Paragraph(
        f"{label}: <{peso}>{valor}</{peso}>" if peso else f"{label}: {valor}",
        ParagraphStyle("campo", fontName="Helvetica", fontSize=10, leading=15)
    )

def _seccion(titulo):
    return Paragraph(
        titulo,
        ParagraphStyle("sec", fontName="Helvetica", fontSize=9,
                       alignment=TA_CENTER, textColor=GRIS,
                       spaceBefore=10, spaceAfter=2)
    )

def _caja_texto(texto, altura=2.2*cm):
    """Rectángulo con texto, simula los cuadros del formulario original."""
    data = [[Paragraph(texto or "",
                       ParagraphStyle("caja", fontName="Helvetica",
                                      fontSize=9, leading=13))]]
    t = Table(data, colWidths=[18*cm], rowHeights=[altura])
    t.setStyle(TableStyle([
        ("BOX",           (0,0), (-1,-1), 0.5, NEGRO),
        ("LEFTPADDING",   (0,0), (-1,-1), 6),
        ("RIGHTPADDING",  (0,0), (-1,-1), 6),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ("VALIGN",        (0,0), (-1,-1), "TOP"),
    ]))
    return t


# ════════════════════════════════════════════════════════════════════════════
# DOCUMENTO 1: ACTA DE AUDITORÍA
# ════════════════════════════════════════════════════════════════════════════

def doc_acta_auditoria(session, output_path: str, auditoria_id: int):
    from database.models import Auditoria, Establecimiento

    a = session.query(Auditoria).get(auditoria_id)
    if not a:
        raise ValueError(f"Auditoría {auditoria_id} no encontrada.")

    e = session.query(Establecimiento).get(a.codigo_establecimiento) if a.codigo_establecimiento else None
    inscripto = e.inscripto if e else None

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm,
    )
    styles = {}
    story  = []

    _cabecera_institucional(story, "Acta de Auditoría", styles)

    # Fila: Código Establecimiento | Código Auditoría | Fecha Auditoría
    num_str = str(int(a.numero_auditoria)) if a.numero_auditoria else ""
    fila1_data = [[
        Paragraph(f"Código Establecimiento: <b>{a.codigo_establecimiento or ''}</b>",
                  ParagraphStyle("f", fontName="Helvetica", fontSize=10)),
        Paragraph(f"Código Auditoría:",
                  ParagraphStyle("f", fontName="Helvetica", fontSize=10)),
        Table([[Paragraph(f"<b>{num_str}</b>",
                          ParagraphStyle("n", fontName="Helvetica-Bold",
                                         fontSize=11, alignment=TA_CENTER))]],
              colWidths=[2.5*cm],
              style=TableStyle([("BOX",(0,0),(-1,-1),1,NEGRO),
                                ("ALIGN",(0,0),(-1,-1),"CENTER")])),
        Paragraph(f"Fecha Auditoría:  <b>{_fmt_fecha(a.fecha_auditoria)}</b>",
                  ParagraphStyle("f", fontName="Helvetica", fontSize=10)),
    ]]
    t = Table(fila1_data, colWidths=[6*cm, 3.5*cm, 3*cm, 5.5*cm])
    t.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                           ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story.append(t)

    # Nombre establecimiento
    nombre_estab = (e.nombre_establecimiento if e else "") or ""
    story.append(_campo("Nombre Establecimiento", nombre_estab.upper()))

    # Domicilio
    domicilio = ""
    num_dom   = ""
    localidad = ""
    cp        = ""
    if e:
        domicilio = (e.domicilio_establecimiento or "").upper()
        num_dom   = (e.numero_establecimiento or "").upper()
        localidad = (e.localidad_establecimiento or "").upper()
        cp        = str(e.codigo_postal or "")

    dom_data = [[
        Paragraph(f"Domicilio: <b>{domicilio}</b>",
                  ParagraphStyle("f", fontName="Helvetica", fontSize=10)),
        Paragraph(f"Nº: <b>{num_dom}</b>",
                  ParagraphStyle("f", fontName="Helvetica", fontSize=10)),
        Paragraph(f"Localidad: <b>{localidad}</b>",
                  ParagraphStyle("f", fontName="Helvetica", fontSize=10)),
        Paragraph(f"C.Postal: <b>{cp}</b>",
                  ParagraphStyle("f", fontName="Helvetica", fontSize=10)),
    ]]
    t2 = Table(dom_data, colWidths=[7*cm, 2.5*cm, 5.5*cm, 3*cm])
    t2.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                            ("BOTTOMPADDING",(0,0),(-1,-1),4)]))
    story.append(t2)

    # Titular
    titular = ""
    if inscripto:
        titular = f"{(inscripto.apellido_razonsocial or '').upper()} {(inscripto.nombres or '').upper()}".strip()
    story.append(_campo("Apellido y Nombres del Titular", titular))
    story.append(Spacer(1, 4))

    # Secciones con cuadros
    for titulo, texto, altura in [
        ("Alcances de la Auditoría",  a.alcances or "",         1.8*cm),
        ("Conformidades",             a.conformidades or "",    2.2*cm),
        ("No Conformidades",          a.no_conformidades or "", 2.2*cm),
        ("Conclusiones",              a.conclusiones or "",     2.2*cm),
        ("Material Adjunto",          a.material_adjunto or "", 1.5*cm),
    ]:
        story.append(_seccion(titulo))
        story.append(_caja_texto(texto, altura))

    # Acta Multifuncion y Anexo Auditoria
    story.append(Spacer(1, 6))
    pie_data = [[
        Paragraph(f"Acta Multifuncion Nº: {'_' * 14}",
                  ParagraphStyle("p", fontName="Helvetica", fontSize=10)),
        Paragraph(f"Anexo Auditoria Nº: {'_' * 16}",
                  ParagraphStyle("p", fontName="Helvetica", fontSize=10)),
    ]]
    story.append(Table(pie_data, colWidths=[9*cm, 9*cm]))

    # Firmas
    story.append(Spacer(1, 0.5*cm))
    firma_data = [[
        Paragraph("." * 35 + "<br/>Firma del Auditado",
                  ParagraphStyle("f", fontName="Helvetica", fontSize=9,
                                 alignment=TA_CENTER)),
        Paragraph("." * 35 + "<br/>Firma del Auditor",
                  ParagraphStyle("f", fontName="Helvetica", fontSize=9,
                                 alignment=TA_CENTER)),
    ]]
    story.append(Table(firma_data, colWidths=[9*cm, 9*cm]))
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph("." * 35 + "<br/>Aclaración",
                            ParagraphStyle("f", fontName="Helvetica", fontSize=9,
                                           alignment=TA_CENTER)))

    doc.build(story, onFirstPage=_pie_pagina, onLaterPages=_pie_pagina)
    return output_path


# ════════════════════════════════════════════════════════════════════════════
# DOCUMENTO 2: RECIBO DE PAGO DE INICIO DE TRÁMITE
# ════════════════════════════════════════════════════════════════════════════

def doc_recibo_transaccion(session, output_path: str, codigos_deuda: list):
    """
    Genera un recibo con ÚNICAMENTE las deudas indicadas por ID.
    Usado para imprimir el recibo de la transacción que se acaba de registrar.
    """
    from database.models import Deuda, Establecimiento

    if not codigos_deuda:
        raise ValueError("No se indicaron deudas para el recibo.")

    # Cargar las deudas indicadas
    deudas = session.query(Deuda).filter(
        Deuda.codigo_deuda.in_(codigos_deuda)
    ).order_by(Deuda.anio, Deuda.periodo).all()

    if not deudas:
        raise ValueError("No se encontraron las deudas indicadas.")

    # Tomar el establecimiento de la primera deuda
    codigo_estab = deudas[0].codigo_establecimiento
    e = session.query(Establecimiento).get(codigo_estab.upper())
    nombre_estab = (e.nombre_establecimiento or "").upper() if e else codigo_estab

    filas = []
    total_a_pagar = 0.0
    for d in deudas:
        if d.vencimiento:
            meses, int_acum, actualizado = _calcular_interes(d.importe, d.vencimiento)
        else:
            meses, int_acum, actualizado = 0, 0, d.importe
        total_a_pagar += actualizado
        filas.append({
            "periodo":    d.periodo,
            "anio":       d.anio,
            "nominal":    d.importe,
            "tiempo":     meses,
            "tasa":       TASA_MENSUAL,
            "int_acum":   int_acum,
            "actualizado":actualizado,
            "medio":      d.medio_pago or "EFECTIVO",
            "fecha_pago": _fmt_fecha(d.fecha_pago),
        })

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    story = []

    _cabecera_institucional(story, "Recibo de Pago\nTransacción", {})
    story.append(Spacer(1, 0.3*cm))

    story.append(Paragraph(
        f"Código Establecimiento: <b>{codigo_estab}</b>",
        ParagraphStyle("f", fontName="Helvetica", fontSize=11)))
    story.append(Paragraph(
        f"Nombre Establecimiento: <b>{nombre_estab}</b>",
        ParagraphStyle("f", fontName="Helvetica", fontSize=11)))
    story.append(Paragraph(
        f"Fecha de emisión: <b>{_fecha_larga_es()}</b>",
        ParagraphStyle("f", fontName="Helvetica", fontSize=10,
                       textColor=colors.HexColor("#555555"))))
    story.append(Spacer(1, 0.4*cm))

    encabezado = [
        Paragraph("<b>Período</b>", ParagraphStyle("th", fontName="Helvetica-Bold",
                  fontSize=9, alignment=TA_CENTER, textColor=colors.white)),
        Paragraph("<b>Año</b>", ParagraphStyle("th", fontName="Helvetica-Bold",
                  fontSize=9, alignment=TA_CENTER, textColor=colors.white)),
        Paragraph("<b>Imp. Nominal</b>", ParagraphStyle("th", fontName="Helvetica-Bold",
                  fontSize=9, alignment=TA_CENTER, textColor=colors.white)),
        Paragraph("<b>Tiempo</b>", ParagraphStyle("th", fontName="Helvetica-Bold",
                  fontSize=9, alignment=TA_CENTER, textColor=colors.white)),
        Paragraph("<b>Tasa</b>", ParagraphStyle("th", fontName="Helvetica-Bold",
                  fontSize=9, alignment=TA_CENTER, textColor=colors.white)),
        Paragraph("<b>Int. Acum.</b>", ParagraphStyle("th", fontName="Helvetica-Bold",
                  fontSize=9, alignment=TA_CENTER, textColor=colors.white)),
        Paragraph("<b>Total</b>", ParagraphStyle("th", fontName="Helvetica-Bold",
                  fontSize=9, alignment=TA_CENTER, textColor=colors.white)),
    ]
    col_w = [2*cm, 1.8*cm, 3*cm, 1.8*cm, 1.8*cm, 2.6*cm, 3.4*cm]

    tabla_data = [encabezado]
    for f in filas:
        tabla_data.append([
            str(f["periodo"] or ""),
            str(f["anio"] or ""),
            _fmt_moneda(f["nominal"]),
            str(f["tiempo"]),
            str(f["tasa"]),
            str(f["int_acum"]),
            _fmt_moneda(f["actualizado"]),
        ])

    from reportlab.lib import colors as _colors
    GRIS_FILA = _colors.HexColor("#f2f2f2")
    t = Table(tabla_data, colWidths=col_w, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0,0), (-1,0), AZUL),
        ("TEXTCOLOR",     (0,0), (-1,0), _colors.white),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,-1), 9),
        ("ALIGN",         (0,0), (-1,0), "CENTER"),
        ("ALIGN",         (0,1), (-1,-1), "CENTER"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [_colors.white, GRIS_FILA]),
        ("GRID",          (0,0), (-1,-1), 0.3, _colors.HexColor("#cccccc")),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ]))
    story.append(t)
    story.append(Spacer(1, 0.4*cm))

    # Medio de pago (del primer registro)
    medio = filas[0]["medio"] if filas else "EFECTIVO"
    story.append(Paragraph(
        f"Medio de pago: <b>{medio}</b>",
        ParagraphStyle("mp", fontName="Helvetica", fontSize=10)))
    story.append(Spacer(1, 0.2*cm))

    # Total
    total_data = [[
        Paragraph("TOTAL ABONADO:",
                  ParagraphStyle("tp", fontName="Helvetica-Bold", fontSize=12,
                                 alignment=TA_RIGHT)),
        Paragraph(f"<b>{_fmt_moneda(total_a_pagar)}</b>",
                  ParagraphStyle("tv", fontName="Helvetica-Bold", fontSize=13,
                                 textColor=AZUL, alignment=TA_RIGHT)),
    ]]
    story.append(Table(total_data, colWidths=[14*cm, 4*cm]))
    story.append(Spacer(1, 0.4*cm))
    story.append(Paragraph(
        f"Fighiera, {_fecha_larga_es()}",
        ParagraphStyle("fecha", fontName="Helvetica", fontSize=10, alignment=TA_RIGHT)))

    doc.build(story, onFirstPage=_pie_pagina, onLaterPages=_pie_pagina)
    return output_path


# ════════════════════════════════════════════════════════════════════════════
# DOCUMENTO 3: RECIBO TASA INSCRIPCIÓN ÁREA DE ALIMENTOS
# ════════════════════════════════════════════════════════════════════════════

def doc_recibo_tasa_inscripcion(session, output_path: str, codigo_establecimiento: str):
    from database.models import Establecimiento, Anexo1, Anexo2, Anexo3, Rubro

    e = session.query(Establecimiento).get(codigo_establecimiento.upper())
    if not e:
        raise ValueError(f"Establecimiento {codigo_establecimiento} no encontrado.")

    inscripto = e.inscripto
    rubro_nombre = e.rubro_rel.nombre if e.rubro_rel else ""

    # Resolver nombres de anexos
    def nombre_anexo(model, aid):
        if not aid:
            return ""
        obj = session.query(model).get(aid)
        return obj.nombre if obj else ""

    an1 = nombre_anexo(Anexo1, e.anexo1_id)
    an2 = nombre_anexo(Anexo2, e.anexo2_id)
    an3 = nombre_anexo(Anexo3, e.anexo3_id)

    nro_recibo = int(e.codigo_inscripcion or 0)
    fecha_str  = _fmt_fecha(datetime.now())

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    story = []

    _cabecera_institucional(story, "Recibo Tasa Inscripción\nÁrea de Alimentos", {})
    story.append(Spacer(1, 0.3*cm))

    # Encabezado: Nº, Código, Localidad, Fecha
    enc_data = [[
        Paragraph(f"Nº: <b>{nro_recibo}</b>",
                  ParagraphStyle("f", fontName="Helvetica", fontSize=11)),
        Paragraph(f"Código Establecimiento: <b>{e.codigo_establecimiento}</b>",
                  ParagraphStyle("f", fontName="Helvetica", fontSize=11)),
        Paragraph(f"Localidad: <b>{(e.localidad_establecimiento or 'FIGHIERA').upper()}</b>",
                  ParagraphStyle("f", fontName="Helvetica", fontSize=11)),
    ]]
    story.append(Table(enc_data, colWidths=[4*cm, 8*cm, 6*cm]))
    story.append(HRFlowable(width="100%", thickness=0.5, color=GRIS, spaceAfter=6))

    # Nombre establecimiento
    story.append(_campo("Nombre Establecimiento",
                        (e.nombre_establecimiento or "").upper()))

    # Domicilio
    dom_data = [[
        Paragraph(f"Domicilio: <b>{(e.domicilio_establecimiento or '').upper()}</b>",
                  ParagraphStyle("f", fontName="Helvetica", fontSize=10)),
        Paragraph(f"Localidad: <b>{(e.localidad_establecimiento or '').upper()}</b>",
                  ParagraphStyle("f", fontName="Helvetica", fontSize=10)),
    ]]
    story.append(Table(dom_data, colWidths=[9*cm, 9*cm]))

    # Rubro y anexos con montos
    story.append(Spacer(1, 0.5*cm))
    story.append(HRFlowable(width="100%", thickness=0.3, color=GRIS, spaceAfter=4))

    rubros_data = [
        ["Rubro:", rubro_nombre, "Monto:", _fmt_moneda(e.monto)],
        ["Anexos:", an1 or "—", "Monto:", _fmt_moneda(e.monto1) if an1 else "$ 0,00"],
        ["",        an2 or "",   "Monto:", _fmt_moneda(e.monto2) if an2 else "$ 0,00"],
        ["",        an3 or "",   "Monto:", _fmt_moneda(e.monto3) if an3 else "$ 0,00"],
    ]
    t = Table(rubros_data, colWidths=[2.5*cm, 9.5*cm, 2.5*cm, 3.5*cm])
    t.setStyle(TableStyle([
        ("FONTNAME",  (0,0), (0,-1), "Helvetica-Bold"),
        ("FONTNAME",  (2,0), (2,-1), "Helvetica-Bold"),
        ("FONTNAME",  (3,0), (3,-1), "Helvetica"),
        ("FONTSIZE",  (0,0), (-1,-1), 10),
        ("ALIGN",     (3,0), (3,-1), "RIGHT"),
        ("VALIGN",    (0,0), (-1,-1), "MIDDLE"),
        ("TOPPADDING",    (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    story.append(t)

    story.append(HRFlowable(width="100%", thickness=0.3, color=GRIS, spaceAfter=4))

    # Importe total
    total_data = [[
        Paragraph("Importe Total:",
                  ParagraphStyle("it", fontName="Helvetica-Bold", fontSize=12,
                                 alignment=TA_RIGHT)),
        Paragraph(f"<b>{_fmt_moneda(e.monto_total)}</b>",
                  ParagraphStyle("iv", fontName="Helvetica-Bold", fontSize=14,
                                 textColor=AZUL, alignment=TA_RIGHT)),
    ]]
    story.append(Table(total_data, colWidths=[14*cm, 4*cm]))

    story.append(Spacer(1, 0.8*cm))

    # Fecha y sello
    fecha_lugar_data = [[
        Paragraph(
            f"Fighiera  {_fecha_larga_es()}",
            ParagraphStyle("fl", fontName="Helvetica", fontSize=10)
        ),
        Paragraph("SELLO DE PAGADO",
                  ParagraphStyle("s", fontName="Helvetica-Bold", fontSize=10,
                                 alignment=TA_CENTER, textColor=GRIS)),
    ]]
    sello_t = Table(fecha_lugar_data, colWidths=[9*cm, 9*cm],
                    rowHeights=[3*cm])
    sello_t.setStyle(TableStyle([
        ("VALIGN",       (0,0), (0,0), "TOP"),
        ("VALIGN",       (1,0), (1,0), "BOTTOM"),
        ("BOX",          (1,0), (1,0), 1, GRIS),
        ("BOTTOMPADDING",(1,0), (1,0), 6),
        ("ALIGN",        (1,0), (1,0), "CENTER"),
    ]))
    story.append(sello_t)

    doc.build(story, onFirstPage=_pie_pagina, onLaterPages=_pie_pagina)
    return output_path


# ════════════════════════════════════════════════════════════════════════════
# DOCUMENTO 4: DETALLE DE DEUDA CON INTERESES
# ════════════════════════════════════════════════════════════════════════════

def doc_detalle_deuda(session, output_path: str, codigo_establecimiento: str,
                      solo_impagas=True):
    from database.models import Establecimiento, Deuda

    e = session.query(Establecimiento).get(codigo_establecimiento.upper())
    if not e:
        raise ValueError(f"Establecimiento {codigo_establecimiento} no encontrado.")

    q = session.query(Deuda).filter_by(codigo_establecimiento=codigo_establecimiento.upper())
    if solo_impagas:
        q = q.filter(Deuda.pago == False)
    deudas = q.order_by(Deuda.anio, Deuda.periodo).all()

    # Calcular intereses de cada deuda
    filas = []
    total_a_pagar = 0.0
    for d in deudas:
        if d.vencimiento:
            meses, int_acum, actualizado = _calcular_interes(d.importe, d.vencimiento)
        else:
            meses, int_acum, actualizado = 0, 0, d.importe
        total_a_pagar += actualizado
        filas.append({
            "periodo":    d.periodo,
            "anio":       d.anio,
            "nominal":    d.importe,
            "tiempo":     meses,
            "tasa":       TASA_MENSUAL,
            "int_acum":   int_acum,
            "actualizado":actualizado,
            "pagado":     d.pago,
        })

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    story = []

    _cabecera_institucional(story, "Detalle de Deuda\nRecibo", {})
    story.append(Spacer(1, 0.3*cm))

    # Encabezado del establecimiento
    story.append(Paragraph(
        f"Código Establecimiento: <b>{e.codigo_establecimiento}</b>",
        ParagraphStyle("f", fontName="Helvetica", fontSize=11)))
    story.append(Paragraph(
        f"Nombre Establecimiento: <b>{(e.nombre_establecimiento or '').upper()}</b>",
        ParagraphStyle("f", fontName="Helvetica", fontSize=11)))
    story.append(Spacer(1, 0.4*cm))

    # Tabla de deudas
    encabezado = [
        Paragraph("<b>Período</b>", ParagraphStyle("th", fontName="Helvetica-Bold",
                  fontSize=9, alignment=TA_CENTER, textColor=colors.white)),
        Paragraph("<b>Año</b>", ParagraphStyle("th", fontName="Helvetica-Bold",
                  fontSize=9, alignment=TA_CENTER, textColor=colors.white)),
        Paragraph("<b>Imp. Nominal</b>", ParagraphStyle("th", fontName="Helvetica-Bold",
                  fontSize=9, alignment=TA_CENTER, textColor=colors.white)),
        Paragraph("<b>Tiempo</b>", ParagraphStyle("th", fontName="Helvetica-Bold",
                  fontSize=9, alignment=TA_CENTER, textColor=colors.white)),
        Paragraph("<b>Tasa Interés</b>", ParagraphStyle("th", fontName="Helvetica-Bold",
                  fontSize=9, alignment=TA_CENTER, textColor=colors.white)),
        Paragraph("<b>Int. Acumulado</b>", ParagraphStyle("th", fontName="Helvetica-Bold",
                  fontSize=9, alignment=TA_CENTER, textColor=colors.white)),
        Paragraph("<b>Importe Actualizado</b>", ParagraphStyle("th", fontName="Helvetica-Bold",
                  fontSize=9, alignment=TA_CENTER, textColor=colors.white)),
    ]
    col_w = [2*cm, 1.8*cm, 3*cm, 1.8*cm, 2.5*cm, 3*cm, 3.9*cm]

    tabla_data = [encabezado]
    for f in filas:
        tabla_data.append([
            str(f["periodo"] or ""),
            str(f["anio"] or ""),
            _fmt_moneda(f["nominal"]),
            str(f["tiempo"]),
            str(f["tasa"]),
            str(f["int_acum"]),
            _fmt_moneda(f["actualizado"]),
        ])

    t = Table(tabla_data, colWidths=col_w, repeatRows=1)
    style = TableStyle([
        # Encabezado
        ("BACKGROUND",    (0,0), (-1,0), AZUL),
        ("TEXTCOLOR",     (0,0), (-1,0), colors.white),
        ("FONTNAME",      (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE",      (0,0), (-1,0), 9),
        ("ALIGN",         (0,0), (-1,0), "CENTER"),
        # Cuerpo
        ("FONTNAME",      (0,1), (-1,-1), "Helvetica"),
        ("FONTSIZE",      (0,1), (-1,-1), 9),
        ("ALIGN",         (0,1), (-1,-1), "CENTER"),
        ("ROWBACKGROUNDS",(0,1), (-1,-1), [colors.white, GRIS_FILA]),
        ("GRID",          (0,0), (-1,-1), 0.3, colors.HexColor("#cccccc")),
        ("TOPPADDING",    (0,0), (-1,-1), 4),
        ("BOTTOMPADDING", (0,0), (-1,-1), 4),
    ])
    t.setStyle(style)
    story.append(t)

    # Total a pagar
    story.append(Spacer(1, 0.4*cm))
    total_data = [[
        Paragraph("TOTAL A PAGAR:",
                  ParagraphStyle("tp", fontName="Helvetica-Bold", fontSize=12,
                                 alignment=TA_RIGHT)),
        Paragraph(f"<b>{_fmt_moneda(total_a_pagar)}</b>",
                  ParagraphStyle("tv", fontName="Helvetica-Bold", fontSize=13,
                                 textColor=AZUL, alignment=TA_RIGHT)),
    ]]
    story.append(Table(total_data, colWidths=[14*cm, 4*cm]))

    # Fecha
    story.append(Spacer(1, 0.5*cm))
    story.append(Paragraph(
        f"Fighiera  {_fecha_larga_es()}",
        ParagraphStyle("fecha", fontName="Helvetica", fontSize=10,
                       alignment=TA_RIGHT)
    ))
    story.append(Spacer(1, 0.3*cm))
    story.append(Paragraph(
        f"Página 1 de 1",
        ParagraphStyle("pag", fontName="Helvetica", fontSize=8,
                       textColor=GRIS, alignment=TA_LEFT)
    ))

    doc.build(story, onFirstPage=_pie_pagina, onLaterPages=_pie_pagina)
    return output_path


# ════════════════════════════════════════════════════════════════════════════
# DOCUMENTO 5: CERTIFICADO DE INSCRIPCIÓN
# ════════════════════════════════════════════════════════════════════════════

def doc_certificado_inscripcion(session, output_path: str, codigo_establecimiento: str):
    """
    Replica el Certificado de Inscripción oficial del sistema viejo.
    Incluye datos del establecimiento, titular, rubro/anexos, contacto,
    y espacios para firmas de Audito ASSAL y Presidente Comunal.
    """
    from database.models import Establecimiento, Anexo1, Anexo2, Anexo3

    e = session.query(Establecimiento).get(codigo_establecimiento.upper())
    if not e:
        raise ValueError(f"Establecimiento {codigo_establecimiento} no encontrado.")

    inscripto = e.inscripto
    rubro_nombre = e.rubro_rel.nombre if e.rubro_rel else ""

    def nombre_anexo(model, aid):
        if not aid:
            return None
        obj = session.query(model).get(aid)
        return obj.nombre if obj else None

    an1 = nombre_anexo(Anexo1, e.anexo1_id)
    an2 = nombre_anexo(Anexo2, e.anexo2_id)
    an3 = nombre_anexo(Anexo3, e.anexo3_id)
    anexos_str = ", ".join(a for a in [an1, an2, an3] if a) or "—"

    nro_expediente = inscripto.codigo_inscripcion if inscripto else ""
    fecha_str = datetime.now().strftime("%A, %d de %B de %Y").capitalize()
    localidad_fecha = f"Fighiera  {fecha_str}"

    doc = SimpleDocTemplate(
        output_path, pagesize=A4,
        leftMargin=2.5*cm, rightMargin=2.5*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )
    story = []

    # ── Encabezado institucional ─────────────────────────────────────────────
    _cabecera_institucional(story, "Certificado de Inscripción", {})
    story.append(Spacer(1, 0.3*cm))

    # Expediente Nº (alineado a la derecha, como en el original)
    story.append(Paragraph(
        f"Expediente Nº  <b>{nro_expediente}</b>",
        ParagraphStyle("exp", fontName="Helvetica", fontSize=11,
                       alignment=TA_RIGHT)
    ))
    story.append(Spacer(1, 0.5*cm))

    # ── Datos del establecimiento ────────────────────────────────────────────
    def fila2(lbl1, val1, lbl2, val2, w1=4*cm, w2=7*cm, w3=3*cm, w4=4*cm):
        data = [[
            Paragraph(f"{lbl1}:", ParagraphStyle("l", fontName="Helvetica-Bold", fontSize=10)),
            Paragraph(str(val1 or ""), ParagraphStyle("v", fontName="Helvetica", fontSize=10)),
            Paragraph(f"{lbl2}:", ParagraphStyle("l", fontName="Helvetica-Bold", fontSize=10)),
            Paragraph(str(val2 or ""), ParagraphStyle("v", fontName="Helvetica", fontSize=10)),
        ]]
        t = Table(data, colWidths=[w1, w2, w3, w4])
        t.setStyle(TableStyle([
            ("VALIGN",        (0,0),(-1,-1), "MIDDLE"),
            ("TOPPADDING",    (0,0),(-1,-1), 3),
            ("BOTTOMPADDING", (0,0),(-1,-1), 3),
        ]))
        return t

    def fila1(lbl, val, bold_val=True):
        peso = "b" if bold_val else ""
        return Paragraph(
            f"<b>{lbl}:</b>  <{peso}>{val or ''}</{peso}>",
            ParagraphStyle("f1", fontName="Helvetica", fontSize=10, leading=15,
                           spaceBefore=2, spaceAfter=2)
        )

    story.append(fila1("Código Establecimiento", e.codigo_establecimiento))
    story.append(fila1("Nombre Establecimiento", (e.nombre_establecimiento or "").upper()))

    domicilio_completo = f"{(e.domicilio_establecimiento or '').upper()} {(e.numero_establecimiento or '')}".strip()
    story.append(fila2(
        "Domicilio",  domicilio_completo,
        "Localidad",  (e.localidad_establecimiento or "FIGHIERA").upper(),
        w1=3*cm, w2=8*cm, w3=3*cm, w4=4*cm
    ))

    tel_comercial = (e.telefono_establecimiento or "") if e else ""
    tel_particular = (inscripto.telefono or inscripto.telefono_movil or "") if inscripto else ""
    story.append(fila2(
        "Teléfono Comercial", tel_comercial,
        "Nº", str(e.numero_establecimiento or ""),
        w1=4.5*cm, w2=5.5*cm, w3=1.5*cm, w4=6.5*cm
    ))

    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=0.4, color=GRIS, spaceAfter=6))

    # ── Datos del titular ────────────────────────────────────────────────────
    titular_nombre = ""
    if inscripto:
        titular_nombre = f"{(inscripto.apellido_razonsocial or '').upper()} {(inscripto.nombres or '').upper()}".strip()

    story.append(fila1("Titular", titular_nombre))

    if inscripto:
        story.append(fila2(
            "Tipo Identif.Laboral", (inscripto.tipo_identificacion or "").upper(),
            "Nº",                   (inscripto.numero_identificacion or ""),
            w1=4.5*cm, w2=4.5*cm, w3=1.5*cm, w4=7.5*cm
        ))
        story.append(fila2(
            "Documento",            (inscripto.tipo_documento or "DNI").upper(),
            "Nº",                   (inscripto.numero_documento or ""),
            w1=4.5*cm, w2=4.5*cm, w3=1.5*cm, w4=7.5*cm
        ))
        story.append(fila2(
            "Domicilio",            (inscripto.domicilio or "").upper(),
            "Localidad",            (inscripto.localidad or "").upper(),
            w1=3*cm, w2=8*cm, w3=3*cm, w4=4*cm
        ))
        story.append(fila2(
            "C.Postal",             (inscripto.codigo_postal or ""),
            "Provincia",            (inscripto.provincia or "").upper(),
            w1=3*cm, w2=4*cm, w3=3.5*cm, w4=7.5*cm
        ))
        story.append(fila2(
            "Teléfono Particular",  (inscripto.telefono or ""),
            "Teléfono Móvil",       (inscripto.telefono_movil or ""),
            w1=4.5*cm, w2=5.5*cm, w3=3.5*cm, w4=4.5*cm
        ))
        if inscripto.correo:
            story.append(fila1("E-mail", inscripto.correo, bold_val=False))

    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=0.4, color=GRIS, spaceAfter=6))

    # ── Rubro y Anexos ───────────────────────────────────────────────────────
    story.append(fila1("Rubro", rubro_nombre))
    story.append(fila1("Anexos", anexos_str))

    story.append(Spacer(1, 0.3*cm))
    story.append(HRFlowable(width="100%", thickness=0.4, color=GRIS, spaceAfter=6))

    # ── Observaciones ────────────────────────────────────────────────────────
    story.append(Paragraph(
        "<b>Observaciones</b>",
        ParagraphStyle("ot", fontName="Helvetica-Bold", fontSize=10, spaceAfter=4)
    ))
    obs_texto = (e.observaciones or "") if e else ""
    story.append(_caja_texto(obs_texto, altura=1.8*cm))

    story.append(Spacer(1, 0.5*cm))

    # ── Texto legal ──────────────────────────────────────────────────────────
    story.append(Paragraph(
        "Se extiende el presente Certificado en el Área de Alimentos de la Comuna de Fighiera.",
        ParagraphStyle("legal", fontName="Helvetica-Oblique", fontSize=10,
                       alignment=TA_CENTER, spaceAfter=4)
    ))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(
        localidad_fecha,
        ParagraphStyle("fecha", fontName="Helvetica", fontSize=10,
                       alignment=TA_RIGHT, spaceAfter=12)
    ))

    # ── Firmas ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1.2*cm))
    firmas_data = [[
        Paragraph(
            "." * 32 + "<br/><b>Uriel Casanovas</b><br/>Audito ASSAL",
            ParagraphStyle("firma", fontName="Helvetica", fontSize=9,
                           alignment=TA_CENTER, leading=14)
        ),
        Paragraph(
            "." * 32 + "<br/><b>Rodolfo A. Stangoni</b><br/>Presidente Comunal",
            ParagraphStyle("firma", fontName="Helvetica", fontSize=9,
                           alignment=TA_CENTER, leading=14)
        ),
    ]]
    story.append(Table(firmas_data, colWidths=[9*cm, 9*cm]))

    doc.build(story, onFirstPage=_pie_pagina, onLaterPages=_pie_pagina)
    return output_path
