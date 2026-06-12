"""
Módulo de internacionalización (bilingüe es/eu).

Contiene:
- T: diccionario con todos los textos de interfaz por idioma.
- TITULOS_PAGINAS: títulos de las páginas (es/eu) para el menú st.navigation.
- selector_idioma_portada(): pinta el radio de idioma en el sidebar. Es el
  ÚNICO selector de la app; vive en el router app.py y persiste la elección
  en st.session_state["idioma"]. selector_idioma() queda como alias deprecated.
- idioma_actual(): devuelve el idioma activo ('es'/'eu') leído de session_state.
- textos(): devuelve el sub-diccionario T[idioma] del idioma activo.
"""
import streamlit as st

# --------------------------------------------------------------------------
# Diccionario de textos de interfaz.
# El contenido (datos) se guarda tal cual en la BD; aquí solo se traducen
# las ETIQUETAS de la aplicación.
# --------------------------------------------------------------------------
T = {
    "es": {
        # ---- Generales (visión general / app.py) ----
        "titulo": "Seguimiento de Planes Sectoriales",
        "subtitulo": "Departamento de Alimentación, Desarrollo Rural, Agricultura y Pesca",
        "idioma": "Idioma",
        "plan": "Plan",
        "actuaciones": "Actuaciones",
        "presupuesto": "Presupuesto total",
        "indicadores": "Indicadores",
        "ambitos": "Ámbitos",
        "tab_act": "Actuaciones",
        "tab_kpi": "Indicadores (KPI)",
        "presup_ambito": "Presupuesto por ámbito",
        "estado": "Estado",
        "responsables": "Responsables",
        "sin_dotacion": "Sin dotación",
        "fecha_prevista": "Fecha prevista",
        "objetivo": "Objetivo",
        "filtros": "Filtros",
        # ---- Página de gestión de actuaciones ----
        "gestion_actuaciones": "Gestión de actuaciones",
        "selecciona_plan": "Selecciona plan",
        "selecciona_ambito": "Selecciona ámbito",
        "selecciona_actuacion": "Selecciona actuación",
        "datos_actuacion": "Datos de la actuación",
        "presupuesto_actuacion": "Presupuesto",
        "presupuesto_ejecutado": "Presupuesto ejecutado (€)",
        "porcentaje_ejecutado": "% ejecutado",
        "fecha_inicio": "Fecha inicio prevista",
        "fecha_fin": "Fecha fin prevista",
        "guardar_cambios": "Guardar cambios",
        "guardado_ok": "Cambios guardados.",
        "bitacora": "Historial de seguimiento",
        "sin_seguimientos": "Aún no hay seguimientos registrados.",
        "nuevo_seguimiento": "Registrar cómo está hoy",
        "fecha_corte": "Fecha de corte (AAAA-MM-DD)",
        "etiqueta_corte": "Etiqueta del corte (p. ej. DIC 2025)",
        "fecha_revision": "Fecha de la revisión",
        "estado_en_esa_fecha": "Estado en esa fecha",
        "actualizar_estado_actual": "Actualizar también el estado actual de la actuación",
        "detalle": "Detalle",
        "anadir": "Añadir",
        "seguim_anadido": "Seguimiento añadido.",
        "sin_actuaciones": "Este ámbito no tiene actuaciones.",
        "sin_ambitos": "Este plan no tiene ámbitos.",
        "sin_planes": "No hay planes en la base de datos.",
        "no_aplica": "—",
        "fecha_obligatoria": "La fecha de corte es obligatoria.",
        # Fechas previstas: periodo + año
        "periodo": "Periodo",
        "anio": "Año",
        "periodo_vacio": "—",
        "periodo_1sem": "1º semestre",
        "periodo_2sem": "2º semestre",
        "periodo_anio_completo": "Año completo",
        "fecha_no_parseable": "Texto original sin formato estándar",
        "fecha_sera_sobrescrita": (
            "Selecciona periodo y año para conservarlo, o guarda vacío para borrar."
        ),
        # Visión general: nueva columna en la tabla de actuaciones
        "ultimo_seguimiento": "Último seguimiento",
        # Captions de ayuda en la bitácora
        "caption_bitacora": (
            "Diario de la actuación: cada línea refleja cómo estaba en una fecha concreta. "
            "Las anotaciones DIC 2025 y MAY 2026 provienen de los datos importados del Excel."
        ),
        "caption_nuevo_seguim": (
            "Añade una anotación con la fecha de la revisión, el estado y un comentario. "
            "No borra las anteriores; se va construyendo el histórico."
        ),
        # Estados de la actuación. Las CLAVES (los valores que se guardan
        # en la BD) se mantienen en castellano para no romper datos
        # existentes; las etiquetas de visualización sí se traducen.
        "estado_previsto": "Previsto",
        "estado_en_curso": "En curso",
        "estado_ejecutado": "Ejecutado",
        # ---- Página de Indicadores (KPI) ----
        "indicadores_kpi": "Seguimiento de indicadores (KPI)",
        "selecciona_indicador": "Selecciona indicador",
        "tipo_indicador": "Tipo de indicador",
        "todas": "Todas",
        "sin_indicadores": "Este plan no tiene indicadores.",
        "sin_valores_numericos": (
            "Aún no hay valores numéricos registrados para representar el gráfico."
        ),
        "ficha_indicador": "Ficha del indicador",
        "categoria_kpi": "Categoría",
        "unidad": "Unidad",
        "definicion": "Definición",
        "meta_texto": "Meta (texto)",
        "desarrollo": "Cómo se calcula",
        "meta_valor": "Meta (valor numérico)",
        "guardar_meta": "Guardar meta",
        "meta_guardada": "Meta guardada.",
        "valores_por_anio": "Valores por año",
        "valor": "Valor",
        "observaciones": "Observaciones",
        "guardar_valores": "Guardar valores",
        "valores_guardados": "Valores guardados.",
        "grafico_valores": "Evolución por año",
        "linea_meta": "Meta",
        "ultimo_valor": "Último valor",
        "avance_vs_meta": "% avance vs meta",
        "caption_kpi_valor": (
            "Para los gráficos necesitas un número en «Valor». Si no procede, déjalo "
            "vacío y usa «Observaciones» para el matiz cualitativo. Mantén las "
            "unidades coherentes (p. ej. porcentajes como 20,8 y no como 0,208)."
        ),
        "caption_kpi_meta": (
            "La meta numérica se usa solo en el gráfico (línea de objetivo). Si la "
            "meta del indicador es textual (p. ej. «≥ 85%») déjala vacía o pon aquí "
            "el umbral aproximado."
        ),
        # ---- Página "Resumen del Plan" ----
        "resumen_plan": "Resumen del Plan",
        "resumen": "Resumen",
        "ultima_actualizacion": "Última actualización",
        "distribucion_estado": "Distribución por estado",
        "avance_presupuestario_ambito": "Avance presupuestario por ámbito",
        "resumen_por_ambito": "Resumen por ámbito",
        "resumen_indicadores": "Resumen de indicadores",
        "ultimos_movimientos": "Últimos movimientos",
        "comprometido": "Comprometido",
        "ejecutado": "Ejecutado",
        "pres_comprometido": "Pres. comprometido",
        "pres_ejecutado": "Pres. ejecutado",
        "n_actuaciones": "Nº actuaciones",
        "meta": "Meta",
        "porcentaje_avance": "% avance",
        "sin_movimientos": "Sin movimientos registrados todavía.",
        "total_actuaciones": "Total actuaciones",
        "indicador": "Indicador",
        "vision_general": "Visión general",
        "plan_activo_etiqueta": "Plan",
        "para_cambiar_portada": "para cambiar, vuelve a la portada",
        # ---- Resumen del Plan: pestañas, movimientos y coordinación ----
        "resumen_tab_cuadro": "Cuadro resumen",
        "resumen_tab_movimientos": "Cuadro de movimientos",
        "resumen_tab_indicadores": "Cuadro de indicadores",
        "resumen_tab_coordinacion": "Coordinación",
        "mov_otros": "Otros",
        "movs_mas": "(+{n} más antiguos)",
        "resumen_kpi_solo_lectura": (
            "Vista de solo lectura. Para editar metas y valores, ve a la "
            "página Indicadores."
        ),
        "coord_todos": "Todos",
        "coord_fecha_desde": "Desde",
        "coord_fecha_hasta": "Hasta",
        "coord_buscar": "Buscar en encargo / gestor / resultado",
        "coord_col_ambito": "Ámbito",
        "coord_descargar": "Descargar tabla (Excel)",
        # ---- Acceso (clave de gestión) en páginas de edición ----
        "acceso_titulo": "Acceso restringido",
        "acceso_campo": "Clave de gestión",
        "acceso_boton": "Entrar",
        "acceso_error": "Clave incorrecta.",
        "acceso_no_config": (
            "La clave de gestión no está configurada. Avisa al administrador "
            "(no se puede acceder a esta página)."
        ),
        # ---- Exportación a PDF (Resumen del Plan) ----
        "pdf_seccion": "Exportar a PDF",
        "pdf_generar": "Generar PDF",
        "pdf_generando": "Generando PDF…",
        "pdf_descargar": "Descargar PDF",
        "pdf_generado_el": "Generado el",
        "pdf_grafico_no_disp": "(gráfico no disponible)",
        "pdf_sin_filtros": "(sin filtros)",
        # ---- Página "Administración" ----
        "administracion": "Administración",
        "admin_descargar_titulo": "Descargar plan actual",
        "admin_descargar_desc": (
            "Descarga el Excel con el estado actual del plan seleccionado. "
            "Puedes editarlo cómodamente fuera de la app y volver a "
            "subirlo con la opción de abajo."
        ),
        "admin_descargar_boton": "Descargar Plan_Sectorial_{codigo}.xlsx",
        "admin_subir_titulo": "Subir Excel para añadir o reemplazar plan",
        "admin_subir_desc": (
            "Sube un Plan_Sectorial_*.xlsx generado a partir de la "
            "plantilla. Si el plan ya existe en la BD, se reemplazará por "
            "completo (todos sus datos serán sustituidos por los del Excel)."
        ),
        "admin_subir_label": "Selecciona un archivo .xlsx",
        "admin_validando": "Validando Excel ...",
        "admin_incidencias": "Se han encontrado incidencias en el Excel:",
        "admin_ver_incidencias": "Ver detalle",
        "admin_preview": (
            "El Excel contiene el plan **{codigo} – {nombre}**: "
            "{ambitos} ámbitos, {actuaciones} actuaciones, "
            "{indicadores} indicadores, {valores} valores anuales, "
            "{seguimientos} seguimientos."
        ),
        "admin_plan_nuevo": "Este plan no existe todavía en la BD. Se va a CREAR.",
        "admin_crear_plan": "Crear plan",
        "admin_plan_existe_aviso": (
            "ATENCIÓN — Este plan ya existe en la BD. Al continuar se BORRARÁN:\n\n"
            "- **{actuaciones}** actuaciones actuales (con sus **{seguimientos}** anotaciones de seguimiento)\n"
            "- **{indicadores}** indicadores (con sus **{valores}** valores anuales)\n\n"
            "Y se sustituirán por los datos del Excel.\n\n"
            "Esta operación NO se puede deshacer."
        ),
        "admin_cancelar": "Cancelar",
        "admin_reemplazar_plan": "Reemplazar plan",
        "admin_refrescar_otras": (
            "Refresca cualquier otra página para ver los cambios."
        ),
        "admin_error_carga": "Error al cargar el plan:",
        "admin_bd_vacia": (
            "La base de datos está vacía. Sube un Excel de plan en el bloque "
            "siguiente para comenzar."
        ),
        # ---- Administración: pestañas y Coordinación ----
        "admin_tab_carga": "Carga y descarga de Planes",
        "admin_tab_coordinacion": "Coordinación",
        "coord_anadir_titulo": "Añadir registro de coordinación",
        "coord_fecha": "Fecha",
        "coord_encargo": "Encargo realizado",
        "coord_gestor": "Gestor de la operación",
        "coord_resultado": "Resultado",
        "coord_suf_es": "castellano",
        "coord_suf_eu": "euskera",
        "coord_guardar": "Guardar registro",
        "coord_guardado_ok": "Registro de coordinación añadido.",
        "coord_validar_texto": "Rellena al menos uno de los campos de texto.",
        "coord_registros_titulo": "Registros de coordinación",
        "coord_col_actuacion": "Actuación",
        "coord_sin_registros": "Aún no hay registros de coordinación para este plan.",
        # ---- Portada (app.py) ----
        "portada_titulo": "Seguimiento de Planes Sectoriales",
        "portada_selecciona_plan": "Selecciona el Plan Sectorial",
        "portada_intro_1": (
            "Aplicación de apoyo al seguimiento y gestión de los "
            "**Planes Sectoriales** del **Departamento de Alimentación, "
            "Desarrollo Rural, Agricultura y Pesca** del **Gobierno Vasco**. "
            "Permite mantener el avance de las actuaciones, controlar los "
            "presupuestos, actualizar los indicadores y disponer de vistas "
            "ejecutivas para la toma de decisiones."
        ),
        "portada_intro_2": (
            "Actualmente incluye la **Estrategia de Relevo Generacional**. "
            "Está prevista la incorporación progresiva de los planes "
            "sectoriales de **Patata**, **Vacuno de Carne**, "
            "**Vacuno de Leche**, **Bebidas**, **Ovino Latxo**, "
            "**Ecológico** e **Invernaderos**."
        ),
        "portada_vision_titulo": "Visión general",
        "portada_vision_desc": (
            "Resumen por plan: métricas clave, presupuesto por ámbito, "
            "listado de actuaciones por estado y catálogo de indicadores "
            "por categoría."
        ),
        "portada_vision_link": "Ir a Visión general →",
        "portada_gestion_titulo": "Gestión de actuaciones",
        "portada_gestion_desc": (
            "Introduce y actualiza el estado de cada actuación "
            "(Previsto / En curso / Ejecutado), el presupuesto ejecutado, "
            "las fechas previstas y registra anotaciones en el historial "
            "de seguimiento."
        ),
        "portada_gestion_link": "Ir a Gestión de actuaciones →",
        "portada_kpi_titulo": "Indicadores (KPI)",
        "portada_kpi_desc": (
            "Edita los valores anuales de cada indicador, define la meta "
            "numérica y visualiza el avance respecto al objetivo con "
            "gráficos comparativos."
        ),
        "portada_kpi_link": "Ir a Indicadores →",
        "portada_resumen_titulo": "Resumen del Plan",
        "portada_resumen_desc": (
            "Informe ejecutivo consolidado: métricas globales, distribución "
            "por estado, avance presupuestario por ámbito, semáforo de "
            "indicadores y últimos movimientos."
        ),
        "portada_resumen_link": "Ir a Resumen del Plan →",
        "portada_pie": (
            "Los datos se actualizan periódicamente por los responsables "
            "del Departamento de Alimentación, Desarrollo Rural, Agricultura "
            "y Pesca y de HAZI."
        ),
    },
    "eu": {
        "titulo": "Plan Sektorialen Jarraipena",
        "subtitulo": "Elikadura, Landa Garapen, Nekazaritza eta Arrantza Saila",
        "idioma": "Hizkuntza",
        "plan": "Plana",
        "actuaciones": "Jarduketak",
        "presupuesto": "Aurrekontu osoa",
        "indicadores": "Adierazleak",
        "ambitos": "Esparruak",
        "tab_act": "Jarduketak",
        "tab_kpi": "Adierazleak (KPI)",
        "presup_ambito": "Aurrekontua esparruka",
        "estado": "Egoera",
        "responsables": "Arduradunak",
        "sin_dotacion": "Diru-zuzkidurarik gabe",
        "fecha_prevista": "Aurreikusitako data",
        "objetivo": "Helburua",
        "filtros": "Iragazkiak",
        "gestion_actuaciones": "Jarduketen kudeaketa",
        "selecciona_plan": "Aukeratu plana",
        "selecciona_ambito": "Aukeratu esparrua",
        "selecciona_actuacion": "Aukeratu jarduketa",
        "datos_actuacion": "Jarduketaren datuak",
        "presupuesto_actuacion": "Aurrekontua",
        "presupuesto_ejecutado": "Exekutatutako aurrekontua (€)",
        "porcentaje_ejecutado": "% exekutatua",
        "fecha_inicio": "Hasiera-data aurreikusia",
        "fecha_fin": "Amaiera-data aurreikusia",
        "guardar_cambios": "Aldaketak gorde",
        "guardado_ok": "Aldaketak gorde dira.",
        "bitacora": "Jarraipenaren historia",
        "sin_seguimientos": "Oraindik ez dago jarraipenik.",
        "nuevo_seguimiento": "Erregistratu nola dagoen gaur",
        "fecha_corte": "Mozketa-data (UUUU-HH-EE)",
        "etiqueta_corte": "Mozketaren etiketa (adib. ABE 2025)",
        "fecha_revision": "Berrikuste-data",
        "estado_en_esa_fecha": "Egoera data horretan",
        "actualizar_estado_actual": "Eguneratu ere jarduketaren oraingo egoera",
        "detalle": "Xehetasuna",
        "anadir": "Gehitu",
        "seguim_anadido": "Jarraipena gehitu da.",
        "sin_actuaciones": "Esparru honek ez du jarduketarik.",
        "sin_ambitos": "Plan honek ez du esparrurik.",
        "sin_planes": "Datu-basean ez dago planik.",
        "no_aplica": "—",
        "fecha_obligatoria": "Mozketa-data nahitaezkoa da.",
        "periodo": "Aldia",
        "anio": "Urtea",
        "periodo_vacio": "—",
        "periodo_1sem": "1. seihilekoa",
        "periodo_2sem": "2. seihilekoa",
        "periodo_anio_completo": "Urte osoa",
        "fecha_no_parseable": "Jatorrizko testua formatu estandarrik gabe",
        "fecha_sera_sobrescrita": (
            "Aukeratu aldia eta urtea hura mantentzeko, edo gorde hutsik ezabatzeko."
        ),
        "ultimo_seguimiento": "Azken jarraipena",
        "caption_bitacora": (
            "Jarduketaren eguneroko: lerro bakoitzak data zehatz batean nola zegoen islatzen du. "
            "ABE 2025 eta MAI 2026 oharrak Exceletik inportatutako datuetatik datoz."
        ),
        "caption_nuevo_seguim": (
            "Gehitu ohar bat berrikuste-datarekin, egoerarekin eta iruzkin batekin. "
            "Ez ditu aurrekoak ezabatzen; historikoa eraikitzen joaten da."
        ),
        "estado_previsto": "Aurreikusia",
        "estado_en_curso": "Abian",
        "estado_ejecutado": "Exekutatua",
        "indicadores_kpi": "Adierazleen jarraipena (KPI)",
        "selecciona_indicador": "Aukeratu adierazlea",
        "tipo_indicador": "Adierazle mota",
        "todas": "Denak",
        "sin_indicadores": "Plan honek ez du adierazlerik.",
        "sin_valores_numericos": (
            "Oraindik ez dago zenbakizko baliorik grafikoa marrazteko."
        ),
        "ficha_indicador": "Adierazlearen fitxa",
        "categoria_kpi": "Kategoria",
        "unidad": "Unitatea",
        "definicion": "Definizioa",
        "meta_texto": "Helburua (testua)",
        "desarrollo": "Nola kalkulatzen den",
        "meta_valor": "Helburua (zenbakizko balioa)",
        "guardar_meta": "Helburua gorde",
        "meta_guardada": "Helburua gorde da.",
        "valores_por_anio": "Urteko balioak",
        "valor": "Balioa",
        "observaciones": "Oharrak",
        "guardar_valores": "Balioak gorde",
        "valores_guardados": "Balioak gorde dira.",
        "grafico_valores": "Bilakaera urtez urte",
        "linea_meta": "Helburua",
        "ultimo_valor": "Azken balioa",
        "avance_vs_meta": "Aurrerapena helburuaren aldean (%)",
        "caption_kpi_valor": (
            "Grafikoetarako zenbaki bat behar duzu «Balioa» eremuan. Ez badagokio, "
            "utzi hutsik eta erabili «Oharrak» azalpen kualitatiborako. Mantendu "
            "unitateak koherenteak (adib. ehunekoak 20,8 gisa, ez 0,208)."
        ),
        "caption_kpi_meta": (
            "Zenbakizko helburua grafikoan bakarrik erabiltzen da (helburu-marra). "
            "Adierazlearen helburua testuala bada (adib. «≥ %85»), utzi hutsik edo "
            "jarri hemen gutxi gorabeherako muga."
        ),
        # ---- "Planaren Laburpena" orria ----
        "resumen_plan": "Planaren Laburpena",
        "resumen": "Laburpena",
        "ultima_actualizacion": "Azken eguneraketa",
        "distribucion_estado": "Egoeraren araberako banaketa",
        "avance_presupuestario_ambito": "Aurrekontu-aurrerapena esparruka",
        "resumen_por_ambito": "Esparruka laburpena",
        "resumen_indicadores": "Adierazleen laburpena",
        "ultimos_movimientos": "Azken mugimenduak",
        "comprometido": "Konprometitua",
        "ejecutado": "Exekutatua",
        "pres_comprometido": "Aurr. konprometitua",
        "pres_ejecutado": "Aurr. exekutatua",
        "n_actuaciones": "Jarduketa kop.",
        "meta": "Helburua",
        "porcentaje_avance": "Aurrerapena %",
        "sin_movimientos": "Oraindik ez dago mugimendurik.",
        "total_actuaciones": "Jarduketak guztira",
        "indicador": "Adierazlea",
        "vision_general": "Ikuspegi orokorra",
        "plan_activo_etiqueta": "Plana",
        "para_cambiar_portada": "aldatzeko, itzuli azalera",
        # ---- Planaren Laburpena: fitxak, mugimenduak eta koordinazioa ----
        # NOTA: euskera en BORRADOR, pendiente de validar con comunicación de HAZI.
        "resumen_tab_cuadro": "Laburpen-koadroa",
        "resumen_tab_movimientos": "Mugimenduen koadroa",
        "resumen_tab_indicadores": "Adierazleen koadroa",
        "resumen_tab_coordinacion": "Koordinazioa",
        "mov_otros": "Bestelakoak",
        "movs_mas": "(+{n} zaharrago)",
        "resumen_kpi_solo_lectura": (
            "Irakurtzeko soilik. Helburuak eta balioak editatzeko, joan "
            "Adierazleak orrira."
        ),
        "coord_todos": "Denak",
        "coord_fecha_desde": "Noiztik",
        "coord_fecha_hasta": "Noiz arte",
        "coord_buscar": "Bilatu eskaeran / kudeatzailean / emaitzan",
        "coord_col_ambito": "Esparrua",
        "coord_descargar": "Deskargatu taula (Excel)",
        # ---- Sarbidea (kudeaketa-gakoa) edizio-orrietan ----
        # NOTA: euskera en BORRADOR, pendiente de validar con comunicación de HAZI.
        "acceso_titulo": "Sarbide mugatua",
        "acceso_campo": "Kudeaketa-gakoa",
        "acceso_boton": "Sartu",
        "acceso_error": "Gako okerra.",
        "acceso_no_config": (
            "Kudeaketa-gakoa ez dago konfiguratuta. Abisatu administratzaileari "
            "(ezin da orri honetara sartu)."
        ),
        # ---- PDFra esportatzea (Planaren Laburpena) ----
        # NOTA: euskera en BORRADOR, pendiente de validar con comunicación de HAZI.
        "pdf_seccion": "Esportatu PDFra",
        "pdf_generar": "Sortu PDFa",
        "pdf_generando": "PDFa sortzen…",
        "pdf_descargar": "Deskargatu PDFa",
        "pdf_generado_el": "Sortze-data:",
        "pdf_grafico_no_disp": "(grafikoa ez dago erabilgarri)",
        "pdf_sin_filtros": "(iragazkirik gabe)",
        # ---- "Administrazioa" orria ----
        "administracion": "Administrazioa",
        "admin_descargar_titulo": "Deskargatu uneko plana",
        "admin_descargar_desc": (
            "Deskargatu hautatutako planaren uneko egoeraren Excela. "
            "Lasai editatu dezakezu aplikaziotik kanpo eta gero itzuli "
            "beheko aukerarekin."
        ),
        "admin_descargar_boton": "Deskargatu Plan_Sektoriala_{codigo}.xlsx",
        "admin_subir_titulo": "Igo Excela plana gehitzeko edo ordezteko",
        "admin_subir_desc": (
            "Igo plantillaren araberako Plan_Sectorial_*.xlsx fitxategi bat. "
            "Plana datu-basean badago, osorik ordeztuko da (datu guztiak "
            "Excelaren araberako berriekin ordezkatuko dira)."
        ),
        "admin_subir_label": "Aukeratu .xlsx fitxategia",
        "admin_validando": "Excela balioztatzen ...",
        "admin_incidencias": "Excelean intzidentziak aurkitu dira:",
        "admin_ver_incidencias": "Ikusi xehetasunak",
        "admin_preview": (
            "Excelak **{codigo} – {nombre}** plana du: "
            "{ambitos} esparru, {actuaciones} jarduketa, "
            "{indicadores} adierazle, {valores} urteko balio, "
            "{seguimientos} jarraipen."
        ),
        "admin_plan_nuevo": "Plan hau ez dago oraindik datu-basean. SORTU egingo da.",
        "admin_crear_plan": "Sortu plana",
        "admin_plan_existe_aviso": (
            "KONTUZ — Plan hau dagoeneko dago datu-basean. Jarraituz gero, EZABATUKO dira:\n\n"
            "- **{actuaciones}** uneko jarduketa (**{seguimientos}** jarraipen-oharrekin)\n"
            "- **{indicadores}** adierazle (**{valores}** urteko baliorekin)\n\n"
            "Eta Excelaren araberako datuekin ordezkatuko dira.\n\n"
            "Eragiketa hau ezin da desegin."
        ),
        "admin_cancelar": "Utzi",
        "admin_reemplazar_plan": "Ordeztu plana",
        "admin_refrescar_otras": (
            "Aldaketak ikusteko, freskatu beste edozein orri."
        ),
        "admin_error_carga": "Errorea plana kargatzean:",
        "admin_bd_vacia": (
            "Datu-basea hutsik dago. Igo plan baten Excela beheko blokean "
            "hasteko."
        ),
        # ---- Administrazioa: fitxak eta Koordinazioa ----
        # NOTA: euskera en BORRADOR, pendiente de validar con comunicación de HAZI.
        "admin_tab_carga": "Planen karga eta deskarga",
        "admin_tab_coordinacion": "Koordinazioa",
        "coord_anadir_titulo": "Koordinazio-erregistroa gehitu",
        "coord_fecha": "Data",
        "coord_encargo": "Egindako eskaera",
        "coord_gestor": "Eragiketaren kudeatzailea",
        "coord_resultado": "Emaitza",
        "coord_suf_es": "gaztelaniaz",
        "coord_suf_eu": "euskaraz",
        "coord_guardar": "Erregistroa gorde",
        "coord_guardado_ok": "Koordinazio-erregistroa gehitu da.",
        "coord_validar_texto": "Bete testu-eremuetako bat gutxienez.",
        "coord_registros_titulo": "Koordinazio-erregistroak",
        "coord_col_actuacion": "Jarduketa",
        "coord_sin_registros": "Plan honek ez du koordinazio-erregistrorik oraindik.",
        # ---- Azala (app.py) ----
        "portada_titulo": "Plan Sektorialen Jarraipena",
        "portada_selecciona_plan": "Aukeratu Plan Sektoriala",
        "portada_intro_1": (
            "**Eusko Jaurlaritzako** **Elikadura, Landa Garapen, "
            "Nekazaritza eta Arrantza Sailaren** **Plan Sektorialen** "
            "jarraipena eta kudeaketa errazteko aplikazioa. Jarduketen "
            "aurrerapena gordetzeko, aurrekontuak kontrolatzeko, adierazleak "
            "eguneratzeko eta erabakiak hartzeko ikuspegi exekutiboak "
            "izateko."
        ),
        "portada_intro_2": (
            "Gaur egun **Belaunaldi Erreleboaren Estrategia** barne hartzen "
            "du. **Patata**, **Haragitarako Behia**, **Esnetarako Behia**, "
            "**Edariak**, **Latxa**, **Ekologikoa** eta **Berotegiak** plan "
            "sektorialak pixkanaka gehitzea aurreikusten da."
        ),
        "portada_vision_titulo": "Ikuspegi orokorra",
        "portada_vision_desc": (
            "Planaren laburpena: metrika gakoak, esparruka aurrekontua, "
            "egoeraren araberako jarduketen zerrenda eta kategoriaka "
            "adierazleen katalogoa."
        ),
        "portada_vision_link": "Ikuspegi orokorrera →",
        "portada_gestion_titulo": "Jarduketen kudeaketa",
        "portada_gestion_desc": (
            "Sartu eta eguneratu jarduketa bakoitzaren egoera "
            "(Aurreikusia / Abian / Exekutatua), exekutatutako aurrekontua "
            "eta aurreikusitako datak, eta gehitu oharrak jarraipenaren "
            "historian."
        ),
        "portada_gestion_link": "Jarduketen kudeaketara →",
        "portada_kpi_titulo": "Adierazleak (KPI)",
        "portada_kpi_desc": (
            "Editatu adierazle bakoitzaren urteko balioak, ezarri "
            "zenbakizko helburua eta ikusi aurrerapena helburuaren aldean "
            "grafiko konparatiboekin."
        ),
        "portada_kpi_link": "Adierazleetara →",
        "portada_resumen_titulo": "Planaren Laburpena",
        "portada_resumen_desc": (
            "Txosten exekutibo bateratua: metrika globalak, egoeraren "
            "araberako banaketa, esparruka aurrekontu-aurrerapena, "
            "adierazleen semaforoa eta azken mugimenduak."
        ),
        "portada_resumen_link": "Planaren Laburpenera →",
        "portada_pie": (
            "Datuak Elikadura, Landa Garapen, Nekazaritza eta Arrantza "
            "Saileko eta HAZIko arduradunek eguneratzen dituzte "
            "aldizka."
        ),
    },
}

# Lista canónica de estados (valores tal cual se guardan en la BD).
ESTADOS = ["Previsto", "En curso", "Ejecutado"]


def etiquetas_estado(t):
    """Devuelve un dict {valor_BD: etiqueta_traducida} para los estados."""
    return {
        "Previsto":  t["estado_previsto"],
        "En curso":  t["estado_en_curso"],
        "Ejecutado": t["estado_ejecutado"],
    }


# --------------------------------------------------------------------------
# Categorías de indicadores: traducción SOLO de presentación.
#
# La BD almacena la categoría en castellano (es la fuente de verdad; no hay
# columna `_eu`). Aquí mapeamos cada valor castellano a su etiqueta por idioma
# para mostrarlo traducido en la UI (selector de Tipo, ficha, tablas), sin
# tocar nunca el dato almacenado.
#
# Si aparece una categoría nueva que no esté en el mapa, traducir_categoria()
# devuelve el valor original tal cual (fallback seguro: mejor castellano
# correcto que euskera inventado). Validar y añadir aquí las nuevas.
# --------------------------------------------------------------------------
CATEGORIAS_TRADUCIDAS = {
    # --- Existen en BD hoy ---
    "Resultado / Impacto": {"es": "Resultado / Impacto", "eu": "Emaitza / Eragina"},
    "Impacto":             {"es": "Impacto",             "eu": "Eragina"},
    "Proceso":             {"es": "Proceso",             "eu": "Prozesua"},
    # --- Forward-compat (no usadas aún por ningún indicador) ---
    "Resultado":           {"es": "Resultado",           "eu": "Emaitza"},
    "Ejecución":           {"es": "Ejecución",           "eu": "Exekuzioa"},
    "Apoyo y seguimiento": {"es": "Apoyo y seguimiento", "eu": "Laguntza eta jarraipena"},
}


def traducir_categoria(cat, idioma=None):
    """Devuelve la categoría traducida al idioma activo (presentación).

    `cat` es el valor castellano almacenado en BD. Si no está en
    CATEGORIAS_TRADUCIDAS, devuelve el valor original sin tocar (fallback).
    Si `idioma` es None, se lee el idioma activo con idioma_actual().
    """
    if cat is None:
        return cat
    if idioma is None:
        idioma = idioma_actual()
    entrada = CATEGORIAS_TRADUCIDAS.get(cat)
    if not entrada:
        return cat
    return entrada.get(idioma) or entrada.get("es") or cat


# --------------------------------------------------------------------------
# Periodos canónicos para las fechas previstas.
# El valor "" representa "sin periodo seleccionado". Los demás son los
# tokens que se almacenan, concatenados con el año, en la columna de texto
# (p. ej. "1º semestre 2025").
# --------------------------------------------------------------------------
PERIODOS = ["", "1º semestre", "2º semestre", "Año completo"]

# Rango de años aceptado en el desplegable.
ANIOS = list(range(2024, 2033))   # 2024..2032 inclusive


def etiquetas_periodo(t):
    """Devuelve {valor_canónico: etiqueta_traducida} para el selectbox de periodo."""
    return {
        "":              t["periodo_vacio"],
        "1º semestre":   t["periodo_1sem"],
        "2º semestre":   t["periodo_2sem"],
        "Año completo":  t["periodo_anio_completo"],
    }


# --------------------------------------------------------------------------
# Etiqueta de corte automática a partir de una fecha.
# Convención fija (es): "ENE 2025", "DIC 2026"... independiente del idioma
# de la UI, ya que es un dato que se almacena en la BD y debe ser estable
# en todo el histórico.
# --------------------------------------------------------------------------
MESES_ABREV_ES = [
    "ENE", "FEB", "MAR", "ABR", "MAY", "JUN",
    "JUL", "AGO", "SEP", "OCT", "NOV", "DIC",
]


def etiqueta_desde_fecha(fecha):
    """Devuelve "MES AAAA" en mayúsculas (es) a partir de un date/datetime."""
    return f"{MESES_ABREV_ES[fecha.month - 1]} {fecha.year}"


def selector_idioma_portada():
    """
    Pinta el radio de idioma en la barra lateral. Es el ÚNICO selector de
    idioma de la app (vive en el router app.py, que se ejecuta en cada
    rerun, por lo que el radio aparece en el sidebar de todas las páginas).

    Persiste la elección en st.session_state["idioma"] (por defecto "es").
    Usando key="idioma", Streamlit sincroniza el widget con session_state y
    la elección se mantiene al navegar entre páginas, igual que el plan.

    La etiqueta del propio selector es bilingüe: "Idioma" en castellano,
    "Hizkuntza" en euskera (t["idioma"] del idioma activo).
    """
    if "idioma" not in st.session_state:
        st.session_state["idioma"] = "es"
    etiqueta = T[st.session_state["idioma"]]["idioma"]
    st.sidebar.radio(
        etiqueta,
        options=["es", "eu"],
        format_func=lambda x: "Castellano" if x == "es" else "Euskera",
        key="idioma",
    )
    return st.session_state["idioma"]


def selector_idioma():
    """[DEPRECATED] Alias de selector_idioma_portada().

    Se conserva por seguridad para no romper imports antiguos. El selector
    de idioma vive ahora SOLO en el router app.py vía selector_idioma_portada().
    No usar en páginas nuevas: leer el idioma con idioma_actual().
    """
    return selector_idioma_portada()


# --------------------------------------------------------------------------
# Títulos de las páginas para el menú de navegación (st.navigation).
# El sidebar de navegación se construye en app.py con st.Page(title=...),
# tomando el título del idioma activo (idioma_actual()). Solo el idioma
# activo se muestra (no bilingüe simultáneo), por decisión de diseño.
# --------------------------------------------------------------------------
TITULOS_PAGINAS = {
    "es": {
        "inicio": "Inicio",
        "vision_general": "Visión general",
        "gestion": "Gestión de actuaciones",
        "indicadores": "Indicadores",
        "resumen": "Resumen del Plan",
        "administracion": "Administración",
        # Títulos de SECCIÓN del menú (st.navigation con dict de secciones).
        "seccion_consulta": "Consulta",
        "seccion_gestion": "Gestión",
    },
    "eu": {
        "inicio": "Hasiera",
        "vision_general": "Ikuspegi orokorra",
        "gestion": "Jarduketen kudeaketa",
        "indicadores": "Adierazleak",
        "resumen": "Planaren laburpena",
        "administracion": "Administrazioa",
        # Títulos de SECCIÓN del menú. Euskera en BORRADOR (validar con HAZI).
        "seccion_consulta": "Kontsulta",
        "seccion_gestion": "Kudeaketa",
    },
}


def textos(idioma=None):
    """Devuelve el diccionario de textos para el idioma indicado o el activo."""
    if idioma is None:
        idioma = st.session_state.get("idioma", "es")
    return T[idioma]


def idioma_actual():
    """Devuelve el idioma activo ('es' o 'eu') según st.session_state.

    Es la fuente única de verdad para que el resto del código (en especial
    src/consultas.py) sepa en qué idioma debe servir los textos que vienen
    de la base de datos. Por defecto 'es'. Si se invoca fuera de un contexto
    de Streamlit (p. ej. desde un script CLI), devuelve 'es' sin romper.
    """
    try:
        return st.session_state.get("idioma", "es")
    except Exception:
        return "es"


# --------------------------------------------------------------------------
# Plan activo (compartido entre páginas).
#
# Streamlit elimina la clave de session_state asociada a un widget cuando
# ese widget se desmonta (al navegar fuera de la página que lo aloja). Para
# evitar perder la selección al salir de la portada, usamos una clave
# PERSISTENTE "_plan_id_actual" que NO es key= de ningún widget. El
# selectbox de la portada se inicializa desde ella con index= y la
# resincroniza tras cada cambio. Todas las páginas leen "_plan_id_actual"
# directamente o a través de asegurar_plan_id() / plan_actual().
# --------------------------------------------------------------------------
def _nombre_plan(p, idioma):
    """Nombre del plan en el idioma activo, con fallback al castellano."""
    if idioma == "eu" and p.get("nombre_eu"):
        return p["nombre_eu"]
    return p.get("nombre_es") or p.get("codigo") or "?"


def asegurar_plan_id():
    """
    Garantiza que st.session_state["_plan_id_actual"] exista (caso de
    entrada directa a una página sin pasar por la portada). SOLO inicializa
    si la clave no existe en absoluto; nunca sobrescribe una selección
    anterior. Devuelve el plan_id o None si no hay planes en la BD.
    """
    import consultas  # noqa: WPS433
    if "_plan_id_actual" not in st.session_state:
        planes = consultas.listar_planes()
        if not planes:
            return None
        st.session_state["_plan_id_actual"] = planes[0]["id"]
    return st.session_state["_plan_id_actual"]


def plan_actual():
    """
    Devuelve el dict completo del plan activo (según
    st.session_state["_plan_id_actual"]). None si no hay plan seleccionado
    o no se encuentra.
    """
    import consultas  # noqa: WPS433
    pid = st.session_state.get("_plan_id_actual")
    if pid is None:
        return None
    for p in consultas.listar_planes():
        if p["id"] == pid:
            return p
    return None


def selector_plan_portada():
    """
    Pinta el selector de Plan en la PORTADA (app.py).

    Truco para que la selección sobreviva a la navegación entre páginas:
    el selectbox NO usa `key=` (Streamlit borraría la clave al desmontar
    el widget). En su lugar leemos/escribimos manualmente la clave
    persistente "_plan_id_actual": el widget se inicializa con `index=`
    desde ella y la actualizamos con el valor devuelto por el selectbox.
    """
    import consultas  # noqa: WPS433

    planes = consultas.listar_planes()
    if not planes:
        st.warning(T[st.session_state.get("idioma", "es")]["sin_planes"])
        return None

    idioma = st.session_state.get("idioma", "es")
    t = T[idioma]

    # Orden alfabético por nombre en el idioma activo.
    planes_ord = sorted(planes, key=lambda p: _nombre_plan(p, idioma).lower())
    ids = [p["id"] for p in planes_ord]
    nombres = {p["id"]: _nombre_plan(p, idioma) for p in planes_ord}

    # Almacén persistente — clave que NUNCA es widget key.
    if (
        "_plan_id_actual" not in st.session_state
        or st.session_state["_plan_id_actual"] not in ids
    ):
        st.session_state["_plan_id_actual"] = ids[0]

    idx_actual = ids.index(st.session_state["_plan_id_actual"])

    st.markdown(
        f"<div style='text-align:center; font-weight:600; "
        f"margin: 0.4rem 0 0.4rem 0;'>"
        f"{t['portada_selecciona_plan']}</div>",
        unsafe_allow_html=True,
    )
    seleccionado = st.selectbox(
        label=t["portada_selecciona_plan"],
        options=ids,
        format_func=lambda i: nombres.get(i, str(i)),
        index=idx_actual,
        label_visibility="collapsed",
    )

    # Sincroniza el almacén con la nueva selección.
    st.session_state["_plan_id_actual"] = seleccionado
    return seleccionado
