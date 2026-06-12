"""
Generación de informes en PDF (reportlab).

Diseño en dos capas para poder reutilizarlo en futuros informes (p. ej. un PDF
de los registros de Coordinación):

  - INFRAESTRUCTURA COMÚN: estilos corporativos, cabecera con los logos
    institucionales, pie con fecha/paginación, tabla estilizada y el armador
    `construir_pdf(...)`.
  - INFORME CONCRETO: `generar_pdf_resumen(plan_id, idioma)` arma el cuerpo del
    "Cuadro resumen" reutilizando las consultas existentes y delega en
    `construir_pdf`.

GRÁFICOS: el donut/tarta de estados y las barras por ámbito se dibujan con
`reportlab.graphics` (vectorial), NO con plotly→imagen. Motivo: plotly 6 +
kaleido es incompatible y cuelga la conversión a PNG (ver CLAUDE.md). No
reintroducir kaleido sin revisar esa incompatibilidad. La construcción de cada
gráfico va en try/except: si fallara, el PDF se genera igualmente con un texto
de "(gráfico no disponible)".

Sin estado de Streamlit: recibe `idioma` como argumento.
"""
from datetime import datetime
from io import BytesIO
from pathlib import Path

from reportlab.graphics.charts.barcharts import HorizontalBarChart
from reportlab.graphics.charts.legends import Legend
from reportlab.graphics.charts.piecharts import Pie
from reportlab.graphics.shapes import Drawing
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

import consultas

# Rutas
RAIZ = Path(__file__).resolve().parent.parent
DATOS = RAIZ / "datos"

# Paleta corporativa (coherente con src/tema.py)
VERDE = colors.HexColor("#1F5F3A")
VERDE_CLARO = colors.HexColor("#EAF0EC")
GRIS = colors.HexColor("#8A9690")
AMBAR = colors.HexColor("#C87A1F")
GRIS_BARRA = colors.HexColor("#C5D0C8")
GRIS_TXT = colors.HexColor("#5A6A63")
BORDE = colors.HexColor("#D9E1DD")
CEBRA = colors.HexColor("#F5F7F5")
TEXTO = colors.HexColor("#1F2A26")

ANCHO_UTIL_MM = 174  # A4 (210) - márgenes (18+18)
SEP_BLOQUE = 18 * mm  # ~2 cm de aire antes de cada título de bloque


# ==========================================================================
# INFRAESTRUCTURA COMÚN (reutilizable por otros informes)
# ==========================================================================
def estilos():
    ss = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle("titulo", parent=ss["Title"],
                                 fontName="Helvetica-Bold", fontSize=28,
                                 textColor=VERDE, spaceAfter=0, leading=32),
        "titulo_plan": ParagraphStyle("titulo_plan", parent=ss["Title"],
                                      fontName="Helvetica-Bold", fontSize=18,
                                      textColor=TEXTO, spaceAfter=2, leading=22),
        "subtitulo": ParagraphStyle("subtitulo", parent=ss["Normal"],
                                    fontName="Helvetica", fontSize=10,
                                    textColor=GRIS_TXT, spaceAfter=2),
        "h2": ParagraphStyle("h2", parent=ss["Heading2"],
                             fontName="Helvetica-Bold", fontSize=12,
                             textColor=VERDE, spaceBefore=12, spaceAfter=4),
        "normal": ParagraphStyle("normal", parent=ss["Normal"],
                                 fontName="Helvetica", fontSize=9,
                                 textColor=TEXTO, leading=12),
        "caption": ParagraphStyle("caption", parent=ss["Normal"],
                                  fontName="Helvetica-Oblique", fontSize=8,
                                  textColor=GRIS_TXT),
        "objetivo": ParagraphStyle("objetivo", parent=ss["Normal"],
                                   fontName="Helvetica", fontSize=9,
                                   textColor=GRIS_TXT, leading=12,
                                   backColor=VERDE_CLARO, borderPadding=6,
                                   spaceBefore=4, spaceAfter=4),
        "celda": ParagraphStyle("celda", parent=ss["Normal"],
                                fontName="Helvetica", fontSize=8, leading=10,
                                textColor=TEXTO),
        "celda_cab": ParagraphStyle("celda_cab", parent=ss["Normal"],
                                    fontName="Helvetica-Bold", fontSize=7,
                                    leading=8.5, textColor=colors.white),
    }


def _logo(nombre, alto_mm):
    """Image del logo escalada a una altura fija, manteniendo proporción."""
    img = Image(str(DATOS / nombre))
    ratio = img.imageWidth / float(img.imageHeight)
    img.drawHeight = alto_mm * mm
    img.drawWidth = alto_mm * mm * ratio
    return img


def cabecera_flowables(titulo, est, subtitulo=None):
    """Cabecera reutilizable (página 1): logos GV (izq.) y HAZI (der.) grandes y
    separados a los extremos; ~2 cm; título grande; ~2 cm; subtítulo (nombre del
    plan); línea verde."""
    elems = []
    try:
        gova = _logo("gova.jpg", 22)
        hazi = _logo("hazi.jpg", 16)
        # Columna central flexible -> los logos quedan en extremos opuestos
        # (máxima separación horizontal).
        fila = Table([[gova, "", hazi]],
                     colWidths=[gova.drawWidth, None, hazi.drawWidth])
        fila.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (0, 0), (0, 0), "LEFT"),
            ("ALIGN", (2, 0), (2, 0), "RIGHT"),
            ("LEFTPADDING", (0, 0), (-1, -1), 0),
            ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ("TOPPADDING", (0, 0), (-1, -1), 0),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ]))
        elems.append(fila)
    except Exception:
        pass  # si faltara un logo, seguimos sin cabecera gráfica
    elems.append(Spacer(1, 20 * mm))            # ~2 cm tras los logos
    elems.append(Paragraph(titulo, est["titulo"]))   # "Resumen del Plan" (grande)
    if subtitulo:
        elems.append(Spacer(1, 20 * mm))        # ~2 cm hasta el nombre del plan
        elems.append(Paragraph(subtitulo, est["titulo_plan"]))
    elems.append(HRFlowable(width="100%", thickness=2, color=VERDE,
                            spaceBefore=8, spaceAfter=8))
    return elems


def pie_factory(t, fecha_txt):
    """Devuelve un callback onPage que pinta el pie (fecha + nº de página)."""
    def _pie(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 7)
        canvas.setFillColor(GRIS_TXT)
        canvas.drawString(doc.leftMargin, 10 * mm,
                          f"{t['pdf_generado_el']} {fecha_txt}")
        canvas.drawRightString(A4[0] - doc.rightMargin, 10 * mm,
                               str(canvas.getPageNumber()))
        canvas.restoreState()
    return _pie


def tabla_estilizada(filas, est, anchos=None):
    """Table con cabecera verde, cebra y rejilla suave. `filas[0]` es cabecera."""
    datos = []
    for i, fila in enumerate(filas):
        est_cell = est["celda_cab"] if i == 0 else est["celda"]
        datos.append([c if hasattr(c, "wrap") else Paragraph(str(c), est_cell)
                      for c in fila])
    tabla = Table(datos, colWidths=anchos, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), VERDE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, CEBRA]),
        ("GRID", (0, 0), (-1, -1), 0.4, BORDE),
        ("LINEBELOW", (0, 0), (-1, 0), 1, VERDE),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    return tabla


def construir_pdf(titulo, t, cuerpo, fecha_txt, est, subtitulo=None):
    """Arma el documento A4 retrato con cabecera + cuerpo + pie y devuelve bytes."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=18 * mm, rightMargin=18 * mm,
        topMargin=16 * mm, bottomMargin=18 * mm,
        title=f"{titulo} — {subtitulo}" if subtitulo else titulo,
    )
    elementos = cabecera_flowables(titulo, est, subtitulo) + cuerpo
    pie = pie_factory(t, fecha_txt)
    doc.build(elementos, onFirstPage=pie, onLaterPages=pie)
    return buf.getvalue()


# ==========================================================================
# Helpers de formato
# ==========================================================================
def _num(v):
    import pandas as pd
    v = pd.to_numeric(v, errors="coerce")
    return 0.0 if pd.isna(v) else float(v)


def _euros(v):
    import pandas as pd
    v = pd.to_numeric(v, errors="coerce")
    if pd.isna(v):
        return "—"
    return f"{float(v):,.0f} €".replace(",", ".")


def _fmt_fecha(iso):
    if not iso:
        return "—"
    try:
        return datetime.strptime(str(iso)[:10], "%Y-%m-%d").strftime("%d/%m/%Y")
    except (ValueError, TypeError):
        return str(iso)


def _color_semaforo(pct):
    import pandas as pd
    v = pd.to_numeric(pct, errors="coerce")
    if pd.isna(v):
        return None
    v = float(v)
    if v >= 90:
        return "#1f5f3a"
    if v >= 50:
        return "#c87a1f"
    return "#c0392b"


# ==========================================================================
# Gráficos con reportlab.graphics (vectorial; sin kaleido)
# ==========================================================================
def _dibujo_estados(resumen, etiq):
    """Tarta de distribución por estado + leyenda. None si no hay datos."""
    datos = [
        (etiq["Previsto"], resumen["por_estado"].get("Previsto", 0), GRIS),
        (etiq["En curso"], resumen["por_estado"].get("En curso", 0), AMBAR),
        (etiq["Ejecutado"], resumen["por_estado"].get("Ejecutado", 0), VERDE),
    ]
    datos = [d for d in datos if d[1] > 0]
    if not datos:
        return None
    d = Drawing(ANCHO_UTIL_MM * mm, 46 * mm)
    pie = Pie()
    pie.x = 6 * mm
    pie.y = 3 * mm
    pie.width = 40 * mm
    pie.height = 40 * mm
    pie.data = [v for _, v, _ in datos]
    pie.slices.strokeColor = colors.white
    pie.slices.strokeWidth = 1
    for i, (_, _, c) in enumerate(datos):
        pie.slices[i].fillColor = c
    d.add(pie)
    leg = Legend()
    leg.x = 62 * mm
    leg.y = 38 * mm
    leg.fontName = "Helvetica"
    leg.fontSize = 9
    leg.dxTextSpace = 5
    leg.dy = 7
    leg.deltay = 12
    leg.colorNamePairs = [(c, f"{nombre}: {v}") for nombre, v, c in datos]
    d.add(leg)
    return d


def _fmt_eje_euros(v):
    """Formatea el eje de importes: 'X M€' / 'X k€' / 'N €' (legible)."""
    try:
        v = float(v)
    except (TypeError, ValueError):
        return str(v)
    if abs(v) >= 1_000_000:
        return f"{v / 1_000_000:g} M€"
    if abs(v) >= 1_000:
        return f"{v / 1_000:g} k€"
    return f"{v:g} €"


def _dibujo_barras(df_amb, t):
    """Barras horizontales comprometido vs ejecutado por ámbito. None si no aplica."""
    if df_amb.empty:
        return None
    comp = [_num(x) for x in df_amb["presupuesto_comprometido"]]
    ejec = [_num(x) for x in df_amb["presupuesto_ejecutado"]]
    if sum(comp) + sum(ejec) <= 0:
        return None
    # Nombres completos (sin truncar agresivo); fuente pequeña y mucho ancho de
    # etiqueta para que quepan. Recorte solo si son larguísimos.
    nombres = [(str(n)[:60] if n else "—") for n in df_amb["ambito_nombre"]]
    n = len(nombres)
    alto_mm = 26 + 11 * n
    etiqueta_mm = 92          # ancho reservado a las etiquetas de ámbito
    d = Drawing(ANCHO_UTIL_MM * mm, alto_mm * mm)

    bc = HorizontalBarChart()
    bc.x = etiqueta_mm * mm
    bc.y = 12 * mm
    bc.width = (ANCHO_UTIL_MM - etiqueta_mm - 4) * mm
    bc.height = (alto_mm - 26) * mm
    bc.data = [comp, ejec]
    bc.categoryAxis.categoryNames = nombres
    bc.categoryAxis.labels.fontName = "Helvetica"
    bc.categoryAxis.labels.fontSize = 6
    bc.categoryAxis.labels.boxAnchor = "e"
    bc.categoryAxis.labels.dx = -2
    bc.valueAxis.valueMin = 0
    bc.valueAxis.labels.fontName = "Helvetica"
    bc.valueAxis.labels.fontSize = 6
    bc.valueAxis.labelTextFormat = _fmt_eje_euros
    bc.bars[0].fillColor = GRIS_BARRA
    bc.bars[1].fillColor = VERDE
    bc.barSpacing = 1
    bc.groupSpacing = 5
    d.add(bc)

    # Leyenda alineada con el área de barras (mismo x que el gráfico), arriba.
    leg = Legend()
    leg.x = etiqueta_mm * mm
    leg.y = (alto_mm - 5) * mm
    leg.fontName = "Helvetica"
    leg.fontSize = 8
    leg.alignment = "right"
    leg.columnMaximum = 1          # una entrada por columna -> horizontales
    leg.deltax = 75
    leg.dxTextSpace = 4
    leg.colorNamePairs = [(GRIS_BARRA, t["comprometido"]), (VERDE, t["ejecutado"])]
    d.add(leg)
    return d


def _grafico_o_aviso(fn, args, est, t):
    """Devuelve el Drawing del gráfico, o un Paragraph de aviso/—."""
    try:
        dib = fn(*args)
    except Exception:
        return Paragraph(t["pdf_grafico_no_disp"], est["caption"])
    if dib is None:
        return Paragraph("—", est["caption"])
    return dib


# ==========================================================================
# INFORME CONCRETO: Cuadro resumen
# ==========================================================================
def generar_pdf_resumen(plan_id, idioma):
    """Genera el PDF del 'Cuadro resumen' del plan en el idioma dado. Devuelve
    los bytes del PDF. Reutiliza las consultas de resumen existentes."""
    import pandas as pd
    import i18n

    t = i18n.textos(idioma)
    est = estilos()
    etiq = i18n.etiquetas_estado(t)

    plan = consultas.obtener_plan(plan_id) or {}
    resumen = consultas.resumen_actuaciones(plan_id)
    df_amb = consultas.resumen_por_ambito(plan_id)
    df_kpi = consultas.resumen_indicadores(plan_id)

    def _nombre(item, ce, cu):
        if idioma == "eu" and item.get(cu):
            return item[cu]
        return item.get(ce, "") or ""

    nombre_plan = _nombre(plan, "nombre_es", "nombre_eu") or plan.get("codigo") or "—"
    cuerpo = []

    # ---- Cabecera de contenido: periodo, objetivo, última actualización ----
    pi, pf = plan.get("periodo_inicio"), plan.get("periodo_fin")
    if pi and pf:
        cuerpo.append(Paragraph(f"<b>{pi} – {pf}</b>", est["normal"]))
    elif pi or pf:
        cuerpo.append(Paragraph(f"<b>{pi or pf}</b>", est["normal"]))

    objetivo = _nombre(plan, "descripcion_es", "descripcion_eu")
    if objetivo:
        cuerpo.append(Paragraph(f"<b>{t['objetivo']}:</b> {objetivo}", est["objetivo"]))

    cuerpo.append(Paragraph(
        f"{t['ultima_actualizacion']}: {_fmt_fecha(resumen.get('ultima_fecha_seguimiento'))}",
        est["caption"]))

    # ---- Resumen (métricas) ----
    cuerpo.append(Spacer(1, SEP_BLOQUE))
    cuerpo.append(Paragraph(t["resumen"], est["h2"]))
    pt = _num(resumen["presupuesto_total"])
    pe = _num(resumen["presupuesto_ejecutado"])
    pct_glob = f"{pe / pt * 100:.1f} %" if pt > 0 else "—"
    metr = [
        (t["total_actuaciones"], str(resumen["total"])),
        (t["estado_previsto"], str(resumen["por_estado"].get("Previsto", 0))),
        (t["estado_en_curso"], str(resumen["por_estado"].get("En curso", 0))),
        (t["estado_ejecutado"], str(resumen["por_estado"].get("Ejecutado", 0))),
        (t["presupuesto"], _euros(pt)),
        (t["presupuesto_ejecutado"], f"{_euros(pe)} ({pct_glob})"),
        (t["indicadores"], str(len(df_kpi))),
        (t["sin_dotacion"], str(resumen["sin_dotacion"])),
    ]
    # Rejilla compacta: 2 pares (etiqueta/valor) por fila -> 4 columnas.
    met_data = []
    for i in range(0, len(metr), 2):
        par = metr[i:i + 2]
        fila = []
        for lab, val in par:
            fila += [Paragraph(f"<b>{lab}</b>", est["celda"]),
                     Paragraph(val, est["celda"])]
        if len(par) == 1:
            fila += ["", ""]
        met_data.append(fila)
    met = Table(met_data, colWidths=[42 * mm, 45 * mm, 42 * mm, 45 * mm])
    met.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.4, BORDE),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, CEBRA]),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    cuerpo.append(met)

    # ---- Distribución por estado: tarta (fin de la PÁGINA 1) ----
    cuerpo.append(Spacer(1, SEP_BLOQUE))
    cuerpo.append(Paragraph(t["distribucion_estado"], est["h2"]))
    cuerpo.append(_grafico_o_aviso(_dibujo_estados, (resumen, etiq), est, t))

    # ===================== PÁGINA 2 =====================
    cuerpo.append(PageBreak())

    # ---- Avance presupuestario por ámbito: barras ----
    cuerpo.append(Spacer(1, SEP_BLOQUE))
    cuerpo.append(Paragraph(t["avance_presupuestario_ambito"], est["h2"]))
    cuerpo.append(_grafico_o_aviso(_dibujo_barras, (df_amb, t), est, t))

    # ---- Tabla: Resumen por ámbito ----
    cuerpo.append(Spacer(1, SEP_BLOQUE))
    cuerpo.append(Paragraph(t["resumen_por_ambito"], est["h2"]))
    if df_amb.empty:
        cuerpo.append(Paragraph("—", est["caption"]))
    else:
        filas = [[
            t["ambitos"], t["n_actuaciones"], t["estado_previsto"],
            t["estado_en_curso"], t["estado_ejecutado"],
            t["pres_comprometido"], t["pres_ejecutado"], t["porcentaje_avance"],
        ]]
        for _, r in df_amb.iterrows():
            comp = _num(r["presupuesto_comprometido"])
            ej = _num(r["presupuesto_ejecutado"])
            pct = f"{ej / comp * 100:.1f} %" if comp > 0 else "—"
            ambito = f"{r['ambito_codigo'] or ''} · {r['ambito_nombre'] or ''}".strip(" ·")
            filas.append([
                ambito, r["n_actuaciones"], r["n_previsto"], r["n_en_curso"],
                r["n_ejecutado"], _euros(comp), _euros(ej), pct,
            ])
        anchos = [46, 16, 16, 16, 18, 22, 22, 18]
        cuerpo.append(tabla_estilizada(filas, est, anchos=[a * mm for a in anchos]))

    # ===================== PÁGINA 3 =====================
    cuerpo.append(PageBreak())

    # ---- Tabla: Resumen de indicadores (con semáforo) ----
    cuerpo.append(Spacer(1, SEP_BLOQUE))
    cuerpo.append(Paragraph(t["resumen_indicadores"], est["h2"]))
    if df_kpi.empty:
        cuerpo.append(Paragraph(t["sin_indicadores"], est["caption"]))
    else:
        filas = [[
            "Nº", t["categoria_kpi"], t["indicador"], t["meta"],
            t["ultimo_valor"], t["porcentaje_avance"],
        ]]
        for _, r in df_kpi.iterrows():
            num_v = pd.to_numeric(r["numero"], errors="coerce")
            numero = "—" if pd.isna(num_v) else str(int(num_v))
            categoria = i18n.traducir_categoria(r["categoria"], idioma) or "—"
            uv = pd.to_numeric(r["ultimo_valor"], errors="coerce")
            if not pd.isna(uv):
                ult = f"{float(uv):g}"
            else:
                txt = r.get("ultimo_valor_texto")
                txt = "" if pd.isna(txt) else str(txt).strip()
                ult = (txt[:60] + "…") if len(txt) > 60 else (txt or "—")
            meta = r["meta_texto"]
            meta = "—" if (pd.isna(meta) or str(meta).strip() == "") else str(meta)
            pctv = pd.to_numeric(r["porcentaje_avance"], errors="coerce")
            color = _color_semaforo(r["porcentaje_avance"])
            if pd.isna(pctv):
                celda_pct = "—"
            else:
                punto = f'<font color="{color}">●</font> ' if color else ""
                celda_pct = Paragraph(f'{punto}{float(pctv):.1f} %', est["celda"])
            filas.append([numero, categoria, r["nombre"], meta, ult, celda_pct])
        anchos = [10, 28, 60, 26, 22, 28]
        cuerpo.append(tabla_estilizada(filas, est, anchos=[a * mm for a in anchos]))

    fecha_txt = datetime.now().strftime("%d/%m/%Y %H:%M")
    return construir_pdf(
        t["resumen_plan"], t, cuerpo, fecha_txt, est, subtitulo=nombre_plan
    )
