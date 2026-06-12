# CLAUDE.md — Guía para Claude Code

Este documento proporciona contexto rápido a Claude Code (y a futuros desarrolladores) para trabajar eficazmente en este proyecto. Léelo antes de tareas grandes; ahorra iteraciones.

---

## Qué es este proyecto

Aplicación **Streamlit + SQLite** para el seguimiento de **Planes Sectoriales** del Departamento de Alimentación, Desarrollo Rural, Agricultura y Pesca del Gobierno Vasco. La desarrolla un equipo técnico interno con apoyo de Claude.

Pensada para **uso interno** (departamento + HAZI + diputaciones forales). Multi-plan y bilingüe.

---

## Stack y entorno

- Python 3.11+, Streamlit (multipágina), SQLite, pandas, openpyxl, Plotly.
- Sin frontend custom — todo Streamlit puro con CSS personalizado en `src/tema.py`.
- BD local en `db/seguimiento.db` (NO se versiona; se genera la primera vez que se importa un plan).
- Entorno de desarrollo: Windows + VSCode + venv. Activación con `.\.venv\Scripts\Activate.ps1`.

---

## Idioma y bilingüismo

- **Idioma de trabajo: castellano.** Comentarios, prompts internos, mensajes de log, nombres de funciones, todo en castellano.
- **La aplicación es bilingüe es/eu.** Cualquier texto visible al usuario debe pasar por `src/i18n.py`. Al añadir una clave nueva, hacerlo SIEMPRE en ambos idiomas.
- Los datos (nombres de actuaciones, descripciones, observaciones) están almacenados bilingües en la BD. Si el euskera falta, mostrar castellano como fallback.

### ⚠️ Textos de DATOS según el idioma activo (no fijar `_es`)

Los textos de datos viven en columnas paralelas `<campo>_es` / `<campo>_eu`
(ej. `nombre_es`/`nombre_eu`, `objetivo_macro_es`/`objetivo_macro_eu`,
`detalle_es`/`detalle_eu`, `meta_es`/`meta_eu`, `valor_texto_es`/`valor_texto_eu`,
y en `coordinaciones`: `encargo_realizado_es/_eu`, `gestor_operacion_es/_eu`,
`resultado_es/_eu`). El bug histórico fue que el SQL **fijaba siempre `_es`**, así
que al cambiar a euskera la UI estática cambiaba pero los datos seguían en
castellano.

> En `coordinaciones`, `fecha` NO es bilingüe (es ISO `AAAA-MM-DD`); solo lo son
> encargo/gestor/resultado, que se mostrarán con `campos_bilingues`/`_nombre`
> cuando se construya su vista (aún no hay UI para coordinaciones).

**Fuente única del idioma activo**: `i18n.idioma_actual()` → `'es'` / `'eu'`
(lee `st.session_state["idioma"]`; `'es'` por defecto y fuera de Streamlit).

**Dos patrones canónicos, según cómo se consuman los datos:**

1. **Consultas que devuelven dicts con `SELECT *` o ambas columnas**
   (`listar_planes`, `listar_ambitos`, `listar_actuaciones`, `obtener_*`,
   `listar_indicadores`, `listar_seguimientos`): el SQL trae `_es` **y** `_eu`,
   y la PÁGINA elige el idioma en Python con su helper local
   `_nombre(item, campo_es, campo_eu)` (fallback al castellano). No tocar el SQL.

2. **Consultas que aliasan a una columna única** (las que devuelven DataFrame:
   `resumen_por_ambito`, `resumen_indicadores`, `ultimos_movimientos`, y las
   queries ad-hoc de `vistas/1_Vision_general.py`): usar SIEMPRE el helper
   **`consultas.campos_bilingues(campos, idioma=None)`** en el SELECT. NUNCA
   escribir `nombre_es AS nombre` a mano.
   ```python
   import consultas
   # cada item: 'nombre'  |  'am.nombre'  |  ('am.nombre', 'ambito_nombre')
   sel = consultas.campos_bilingues([("am.nombre", "ambito_nombre")])
   df = db.leer_df(f"SELECT am.codigo, {sel} FROM ambitos am WHERE plan_id = ?", (pid,))
   ```
   Genera `COALESCE(NULLIF(TRIM(<col>_<idioma>), ''), <col>_<otro>) AS <alias>`
   con **fallback simétrico** (si la traducción del idioma activo está vacía o
   NULL, devuelve la del otro idioma → un plan sin euskera se ve en castellano,
   nunca en blanco). `TRIM`/`NULLIF`/`COALESCE` son idénticos en SQLite y
   PostgreSQL, así que es portable. El placeholder sigue siendo `?`.

**Caché**: si una función con `@st.cache_data` construye SQL bilingüe (como
`cargar()` en `vistas/1_Vision_general.py`), el **idioma debe ir como argumento**
de la función cacheada, o el cambio de idioma devolverá el DataFrame anterior.

### ⚠️ Datos NO bilingües (estado, categoría): traducir SOLO al mostrar

Algunos textos de datos **no** tienen columna `_eu`: son una **enumeración
cerrada en castellano que es la fuente de verdad en BD** (se usa como valor de
filtro, de selector y de escritura). No se traducen en BD; se traducen **solo
en presentación** con un mapa en `src/i18n.py`. Regla de oro: **el valor que se
guarda / consulta / pasa a un selector sigue siendo el castellano; solo cambia
cómo se MUESTRA.**

- **Estado de actuación** (`Previsto` / `En curso` / `Ejecutado`): lista canónica
  `ESTADOS` + `etiquetas_estado(t)` → dict `{valor_BD: etiqueta_traducida}`.
  Mostrar SIEMPRE con `etiq_estado.get(v, v)` (o `format_func` en selectores).
  Si además hay color por estado, **indexa el color por la etiqueta ya
  traducida** (lo que acaba en la celda), no por el valor crudo —
  ver tabla de `vistas/1_Vision_general.py`.
- **Categoría de indicador** (`Resultado / Impacto`, `Impacto`, `Proceso`):
  `CATEGORIAS_TRADUCIDAS` + `traducir_categoria(cat, idioma=None)`. Devuelve el
  valor original tal cual si la categoría no está en el mapa (fallback seguro:
  mejor castellano correcto que euskera inventado). Si aparece una categoría
  nueva en BD, **validar la traducción con el usuario** antes de añadirla.

Sitios donde hoy se aplica `traducir_categoria`: selector "Tipo" y ficha en
`3_Indicadores.py`, tabla de `4_Resumen_del_Plan.py` y agrupación de
`1_Vision_general.py`. Sitios con `etiquetas_estado`: selectores y historial de
`2_Gestion_actuaciones.py`, métricas/donut/últimos movimientos de
`4_Resumen_del_Plan.py` y la tabla de `1_Vision_general.py`.

---

## Estructura clave — qué hace cada cosa

- `app.py` — **router** de la app (lo que se pasa a `streamlit run`). Con la API `st.Page` + `st.navigation` NO contiene contenido de página: ejecuta una sola vez `set_page_config`, `aplicar_tema()`, el arranque de la BD y el **único selector de idioma** (`selector_idioma_portada()`); luego construye el menú con los títulos traducidos (`TITULOS_PAGINAS[idioma_actual()]`) y ejecuta la página seleccionada (`pg.run()`). Se ejecuta en CADA rerun (es el marco común de todas las páginas).
- `vistas/Inicio.py` — la **portada** (antes en `app.py`): logos, intro, tarjetas de acceso y el **selector de Plan global** (escribe en `st.session_state["_plan_id_actual"]`).
- `vistas/N_*.py` — las cinco páginas funcionales. Viven en `vistas/` (NO en `pages/`, ver pitfall 4). Cada una llama a `asegurar_plan_id()` al inicio, lee el idioma con `idioma_actual()` y NO pinta su propio `set_page_config`/`aplicar_tema`/selector de idioma (lo hace el router). Dos páginas usan `st.tabs`: **Administración** (2 pestañas: "Carga y descarga de Planes" / "Coordinación") y **Resumen del Plan** (4 pestañas: "Cuadro resumen", "Cuadro de movimientos" —historial por estado—, "Cuadro de indicadores" —solo lectura: ficha + tabla estática "Valores por año" + gráfico, vía `componentes_kpi`— y "Coordinación" —tabla `st.dataframe` filtrable con descarga a Excel—). La exportación a PDF del Resumen está pendiente (roadmap).
- `src/i18n.py` — diccionarios de traducción `T` + `TITULOS_PAGINAS` (títulos de página es/eu para el menú) + `selector_idioma_portada()` (único selector, en el router; `selector_idioma()` queda como alias deprecated) + `idioma_actual()` (idioma activo es/eu) + `selector_plan_portada()` + `asegurar_plan_id()`. Para **datos no bilingües** (enumeraciones castellanas que se traducen solo al mostrar): `ESTADOS` + `etiquetas_estado(t)` (estados) y `CATEGORIAS_TRADUCIDAS` + `traducir_categoria(cat, idioma)` (categorías de indicador) — ver **Idioma y bilingüismo**.
- `src/tema.py` — `aplicar_tema()` con CSS verde institucional. Selectores específicos por clase `.st-key-bloque_*`.
- `src/db.py` — acceso **agnóstico de motor** (SQLite o PostgreSQL). `get_conexion()` (alias `conectar()`) abre la conexión al motor activo; `P()` da el placeholder; `ejecutar()` e `insertar_devolver_id()` encapsulan diferencias entre motores; `inicializar_db()` crea el esquema correcto. Ver sección **Persistencia**.
- `src/arranque.py` — `inicializar_si_necesario()`: en SQLite crea el esquema y carga los Excel de `datos/` si la BD está vacía. Lo llama el router `app.py` al arrancar. En PostgreSQL no hace nada.
- `src/consultas.py` — funciones reutilizables para consultar planes, ámbitos, actuaciones, indicadores, seguimientos y coordinaciones. Incluye `campos_bilingues()`, vía canónica para seleccionar textos de datos en el idioma activo con fallback (ver **Idioma y bilingüismo**). Para coordinaciones: `anadir_coordinacion(...)` (INSERT con placeholder `?`) y `listar_coordinaciones(plan_id, idioma)` (DataFrame vía `db.leer_df` + `campos_bilingues`; incluye `ambito_id`/`ambito_codigo`/`ambito_nombre` y `actuacion_id` para poder filtrar). Para el histórico: `listar_movimientos(plan_id, idioma, limite=None)` (todos los seguimientos, o LIMIT si `limite`); `ultimos_movimientos()` queda como alias fino.
- `src/componentes_kpi.py` — componentes de Indicadores de **solo lectura** reutilizados por `vistas/3_Indicadores.py` (edición) y la pestaña "Cuadro de indicadores" de Resumen: `selector_categoria_indicador(plan, t, idioma, key_prefix)`, `ficha_indicador(...)`, `tabla_valores_solo_lectura(...)` y `grafico_valores(...)`. No abren contenedor ni usan `st.stop()` (seguros dentro de `st.tabs`); el `key_prefix` evita que las dos vistas compartan estado de selector.
- `src/acceso.py` — `requiere_clave(t)`: barrera por **clave compartida** en las TRES páginas de edición (Gestión de actuaciones, Indicadores, Administración); las de solo consulta (Inicio, Visión general, Resumen del Plan) quedan abiertas. Se llama justo tras leer idioma/textos y, si la sesión no está autorizada, pinta un formulario `password` y hace `st.stop()`. La clave se lee de `st.secrets["CLAVE_GESTION"]` o `os.environ["CLAVE_GESTION"]`; si no está configurada, **fail-closed** (bloqueado con aviso). Comparación EXACTA (case-sensitive). Autorización para toda la sesión vía `st.session_state["_acceso_gestion_ok"]` (clave persistente, NO es key de widget — pitfall 1).
- `src/importador.py` — `cargar_plan_desde_excel()` y `exportar_plan_a_excel()`. Lo usan tanto el CLI como la página de Administración.
- `db/schema_sqlite.sql` y `db/schema_postgres.sql` — mismo esquema en cada dialecto. Tablas: `planes`, `ambitos`, `responsables`, `actuaciones`, `actuacion_responsables`, `seguimientos`, `coordinaciones`, `indicadores`, `indicador_valores`, `alertas` (esta última definida pero todavía no utilizada por la app). `db.py` elige el fichero según el motor activo.
  - `coordinaciones` — diario de coordinación por actuación (1:N con `actuaciones`, `ON DELETE CASCADE`). Columnas: `fecha` (ISO `AAAA-MM-DD`, **obligatoria**, no bilingüe), `encargo_realizado_es/_eu`, `gestor_operacion_es/_eu`, `resultado_es/_eu` (datos **bilingües**) y `fecha_registro`. La descripción de la actuación NO se almacena aquí: se obtiene por JOIN (se usa `objetivo_impacto_es/_eu`). La alimenta la hoja "Coordinación" del Excel y también se gestiona (alta + listado) desde **Administración → pestaña "Coordinación"**; en Supabase se creó con `db/migracion_coordinacion.sql` (con RLS activado).
- `documentos/` — manuales de usuario y plantilla en blanco (Guia_de_uso.docx, Guia_de_carga_de_planes.docx, Plantilla_Plan_Sectorial.xlsx). Material de consulta humana; no se procesa por código.

---

## Convenciones visuales

- **Color primario**: verde institucional `#1F5F3A`.
- **Fondos pastel para tarjetas** (solo en portada): verde `#EAF0EC`, azul `#E6EEF5`, ámbar `#F5EDE0`, morado `#EDE6F0`.
- **Bordes verde** en tarjetas y bloques del resto de páginas.
- **Cabeceras de tabla** en verde claro `#EAF0EC`.
- **Semáforo de estados**: gris para Previsto, ámbar para En curso, verde para Ejecutado.
- **Sin emojis** en la UI, salvo los semáforos 🟢🟡🔴 en el resumen de indicadores.

### Patrón crítico de tarjetas con borde

```python
with st.container(border=True, key="bloque_xxx"):
    ...
```

El `key=` es **esencial**: Streamlit añade la clase `.st-key-bloque_xxx` al DOM, que `src/tema.py` usa para aplicar el borde verde y, en la portada, los fondos pasteles específicos por tarjeta.

---

## ⚠️ Pitfalls de Streamlit aprendidos a las malas

### 1. Widget unmount borra session_state

Cuando un widget con `key="X"` está en una página y el usuario navega a otra, **Streamlit borra `st.session_state["X"]`** al desmontar el widget. Esto rompe la persistencia de selecciones entre páginas.

**Patrón correcto** para estado compartido entre páginas (como el plan seleccionado):

```python
# Almacén persistente — clave NO asociada a ningún widget
if "_plan_id_actual" not in st.session_state:
    st.session_state["_plan_id_actual"] = ids[0]

# Widget SIN key= (para que no contamine el almacén)
seleccionado = st.selectbox(
    "Plan",
    options=ids,
    index=ids.index(st.session_state["_plan_id_actual"]),
    format_func=lambda i: nombres[i],
)

# Sincronización manual
st.session_state["_plan_id_actual"] = seleccionado
```

Ver `selector_plan_portada()` en `src/i18n.py` como implementación de referencia.

**Regla**: nunca usar como key de un widget la misma clave que se necesita persistir entre páginas.

### 2. Estilos sobre containers

`st.container(border=True)` por sí solo no permite targetearlo con CSS desde fuera. Hace falta `key="bloque_X"` para que Streamlit añada `.st-key-bloque_X` al DOM. Requiere Streamlit ≥ 1.36.

### 3. Caché de Streamlit

`@st.cache_data` puede dejar resultados obsoletos tras modificar la BD (carga de plan, edición de actuaciones). Si se usa, invalidar tras escrituras o reiniciar el servidor.

### 4. Multipágina: `st.navigation` y carpeta `vistas/` (NO `pages/`)

La app usa la API moderna `st.Page` + `st.navigation` (Streamlit ≥ 1.36),
montada en el router `app.py`. Las páginas viven en **`vistas/`**, NO en la
carpeta mágica `pages/`: si estuvieran en `pages/`, Streamlit las autoañadiría
al sidebar **además** del menú de `st.navigation`, duplicando la navegación.
Por eso la carpeta se llama `vistas/`.

- **Orden del menú**: lo da el ORDEN de la lista que se pasa a `st.navigation`
  en `app.py`, no el nombre de fichero. Los prefijos numéricos (`1_`, `2_`…)
  se conservan por familiaridad pero ya no determinan el orden. Para reordenar,
  reordena la lista `paginas` en `app.py`.
- **Títulos traducidos**: cada `st.Page(..., title=...)` toma el título del
  idioma activo desde `TITULOS_PAGINAS[idioma_actual()]` en `src/i18n.py`. Al
  cambiar de idioma en el sidebar, los nombres del menú cambian al instante.
- **Enlaces internos**: `st.page_link("vistas/N_*.py", ...)` (la portada usa
  estos para las tarjetas de acceso rápido).

### 5. `st.selectbox` que muestra contenido traducido → opciones = IDs estables

Un selector cuyas `options` sean **strings traducidos** o **dicts re-leídos** se
desincroniza al cambiar de idioma: el valor guardado en `session_state` ya no
coincide con ninguna opción nueva (queda en castellano o muestra "Choose an
option"). Además, un selectbox **sin `key=`** deriva su clave automática del
`label`, que ES traducido (`"Selecciona ámbito"` → `"Aukeratu esparrua"`): al
cambiar de idioma Streamlit lo trata como widget nuevo y **reinicia la
selección**.

**Patrón canónico** (lo aplican los selectores de `2_Gestion_actuaciones.py` y
`3_Indicadores.py`): `options` = **IDs estables**, nombre traducido vía
`format_func` (se reevalúa en cada rerun → sigue el idioma activo), y `key`
**estable que NO dependa del label**:

```python
items_por_id = {it["id"]: it for it in items}
sel_id = st.selectbox(
    t["selecciona_x"],
    options=[it["id"] for it in items],
    format_func=lambda i: _nombre(items_por_id[i], "nombre_es", "nombre_eu"),
    key=f"sel_x_{plan['id']}",          # estable; cambia de plan → reinicia
)
item = consultas.obtener_x(sel_id)      # downstream recibe el ID, no el dict
```

- La `key` debe incluir aquello cuyo cambio SÍ deba reiniciar el selector
  (plan, ámbito, categoría) y nada más; así el cambio de idioma la mantiene.
- **Excepción** (enumeraciones castellanas, ver bilingüismo): las `options`
  son los **strings de BD** tal cual (fuente de verdad para guardar) y solo el
  `format_func` traduce — p. ej. estado con `etiquetas_estado`, "Tipo" con
  `traducir_categoria`. NO migrar esos a IDs.

---

## Persistencia (SQLite / PostgreSQL)

La app es **dual**: el mismo código corre sobre SQLite (local) o PostgreSQL
(Supabase, despliegue). El motor se resuelve **una vez al importar `src/db.py`**,
en este orden:

1. Variable de entorno `DATABASE_URL` → `MOTOR_BD = "postgres"`.
2. `st.secrets["DATABASE_URL"]` (Streamlit Cloud) → `MOTOR_BD = "postgres"`.
3. Si no hay ninguna → `MOTOR_BD = "sqlite"` en `db/seguimiento.db`.

### Cómo está resuelto

- **SQLite**: `get_conexion()` devuelve la conexión NATIVA `sqlite3.Connection`
  (con `row_factory=sqlite3.Row`). El atajo `con.execute(...)`, el placeholder
  `?` y pandas se comportan exactamente igual que siempre.
- **PostgreSQL**: `get_conexion()` devuelve un adaptador fino (`_ConexionPG`
  sobre psycopg2) que imita la API mínima usada en el proyecto (`con.execute()`,
  `con.cursor()`, commit/rollback/close) y **traduce automáticamente `?` → `%s`**.
  Por eso las consultas con `?` ya existentes son portables sin reescribirlas.
  Expone **dos cursores** (ver pitfall 6): `con.cursor()` de **tuplas** (para
  pandas) y `con.execute()` con **`RealDictCursor`** (acceso por nombre,
  `row["plan_id"]`, como `sqlite3.Row`).

### Pitfalls de la capa de datos (importante)

1. **Placeholders**: escribir SIEMPRE `?` en el SQL (o `{P}` en `db.ejecutar`).
   No mezclar `%s` a mano: la traducción la hace `db.py`.
2. **IDs autogenerados**: NO usar `cursor.lastrowid` directamente (no existe en
   PostgreSQL). Usar `db.insertar_devolver_id(con, tabla, columnas, valores)`,
   que en PostgreSQL añade `RETURNING id`.
3. **SQL específico de motor**: evitar dialecto SQLite. Usar `COALESCE` (no
   `IFNULL`), `CURRENT_TIMESTAMP` (no `datetime('now')`). Para "insertar
   ignorando duplicados" hay rama por motor (`INSERT OR IGNORE` vs
   `ON CONFLICT DO NOTHING`); ver `src/importador.py`.
4. **Tipos de fecha**: `actuaciones.fecha_inicio_prevista` / `fecha_fin_prevista`
   guardan **texto libre** ("1º semestre 2025") y `indicador_valores.periodo`
   guarda el año como cadena ("2025", con usos `.isdigit()`). Por eso esas
   columnas se mantienen **TEXT en ambos motores** (no DATE/INTEGER). Las
   fechas de corte se siguen guardando como ISO `AAAA-MM-DD` en TEXT.
5. **Transacciones**: en PostgreSQL son obligatorias. La carga de planes ya va
   en una transacción con `commit()` final y `rollback()` ante error.
6. **`pandas.read_sql_query` + `RealDictCursor` = DataFrame corrupto**.
   - *Síntoma*: el DataFrame devuelve los **nombres de columna como valor en
     cada celda** (toda fila es `ambito_codigo`, `n_actuaciones`, ...). Aguas
     abajo, p. ej., `df["id"]` vale la cadena `"id"` y una página puede acabar
     mostrando "No se pudo cargar el plan" o pintando los nombres como datos.
   - *Causa*: pandas itera el cursor esperando **tuplas** (acceso posicional);
     `RealDictCursor` le entrega **dicts**, así que cada "fila" termina siendo
     el conjunto de **claves** del dict (los nombres de columna), no los valores.
   - *Contexto / diseño de cursores*: en PostgreSQL, `src/db.py` expone DOS
     cursores. El cursor por defecto (`con.cursor()`) es de **tuplas**; el acceso
     por nombre desde código Python se obtiene con `con.execute(...)`, que crea
     un **`RealDictCursor`** explícito (`fila["id"]`, `dict(fila)`).
   - *Por qué es invisible en SQLite*: `sqlite3.Row` soporta acceso **posicional
     y por nombre** a la vez, así que pandas y el código funcionan con la misma
     conexión sin distinguir cursores.
   - **Regla práctica (canónica)**: para leer DataFrames desde la BD, **NUNCA
     pasar la conexión directamente a `pd.read_sql_query`**. Usar siempre
     **`db.leer_df(query, params)`**, que construye el DataFrame manualmente
     desde `cur.description` + `cur.fetchall()` sobre el cursor por defecto,
     siendo agnóstico al tipo de cursor de cada motor (y a la versión de pandas).
     Ejemplo:
     ```python
     import db
     df = db.leer_df(
         "SELECT codigo, nombre_es FROM planes WHERE estado = ?",
         ("Activo",),
     )
     ```
     El placeholder es `?` (o `{P}`); `db.leer_df` lo traduce al motor activo.
     Las funciones de `src/consultas.py` que devuelven DataFrames
     (`resumen_por_ambito`, `resumen_indicadores`, `ultimos_movimientos`) y
     `cargar()` en `vistas/1_Vision_general.py` ya usan este helper.

### Carga inicial

- **SQLite**: automática en el arranque (`src/arranque.py` desde `app.py`) si la
  BD está vacía.
- **PostgreSQL**: manual y previa, con `scripts/importar_plan.py` desde una red
  sin restricciones. El arranque NO carga nada en PostgreSQL (evita duplicados).

### Configuración local de PostgreSQL

Copiar `.streamlit/secrets.toml.example` a `.streamlit/secrets.toml` y poner la
`DATABASE_URL` real. `secrets.toml` NO se versiona; el `.example` sí.

> Nota: la red de HAZI bloquea el puerto de Supabase. La prueba contra
> PostgreSQL se hace desde Streamlit Cloud u otra red.

### ⚠️ Pruebas y secretos (regla obligatoria)

- **Las pruebas locales se hacen SIEMPRE contra SQLite.** El
  `.streamlit/secrets.toml` de desarrollo contiene **solo `CLAVE_GESTION`** (la
  clave de las páginas de edición), **sin `DATABASE_URL`**, de modo que `db.py`
  resuelve SQLite (`db/seguimiento.db`) y ninguna prueba ni script toca Supabase
  por accidente. El `DATABASE_URL` de producción vive en
  `.streamlit/secrets.toml.PROD` (no se usa en local). Para una **operación
  deliberada contra Supabase** se añade temporalmente `DATABASE_URL` al
  `secrets.toml` (o se restaura desde `.PROD`) y se quita nada más terminar. En
  Streamlit Cloud, `CLAVE_GESTION` y `DATABASE_URL` se configuran en Secrets.
  > Aprendido a las malas: con `DATABASE_URL` presente en secrets,
  > `db._resolver_motor()` elige PostgreSQL y `db.inicializar_db()` se ejecuta
  > contra Supabase (una vez creó una tabla en producción durante un test).
  > `secrets.toml` y `secrets.toml.PROD` están en `.gitignore` (credenciales/clave).
- **NUNCA imprimir `DATABASE_URL` ni ningún secreto** (contraseñas, tokens,
  cadenas de conexión) en logs, salidas de consola ni mensajes. Si necesitas
  confirmar el motor activo, imprime solo `db.MOTOR_BD` (`'sqlite'`/`'postgres'`),
  nunca la URL.

### Seguridad: Row Level Security (RLS) en Supabase

En Supabase está **activado RLS en todas las tablas del schema `public`**
(`db/migracion_activar_rls.sql`, aplicado el 10/06/2026). Bloquea el acceso
anónimo vía la API REST pública de Supabase. La app **no se ve afectada**:
conecta directamente a PostgreSQL con el rol `postgres` (superusuario), que
bypasea RLS por definición.

> ⚠️ Si en el futuro se añade una tabla nueva al schema `public`, hay que
> activar RLS también en ella (`ALTER TABLE public.<tabla> ENABLE ROW LEVEL
> SECURITY;`) o el Security Advisor de Supabase volverá a marcar el aviso.
> Ejemplo aplicado: `db/migracion_coordinacion.sql` crea la tabla
> `coordinaciones` y activa su RLS en el mismo fichero.

Los ficheros `db/migracion_*.sql` son migraciones puntuales aplicadas a mano en
el SQL Editor de Supabase (idempotentes cuando es posible). No los ejecuta la
app; quedan versionados como registro histórico de cambios sobre la BD desplegada.

---

## Carga y exportación de planes

- **Formato único**: `datos/Plan_Sectorial_<NOMBRE>.xlsx` con 9 hojas estandarizadas: Instrucciones, Plan, Ámbitos, Responsables, Actuaciones, Indicadores, Valores_indicadores, Seguimientos, Coordinación.
- **Hoja "Coordinación"** (cabeceras bilingües en dos líneas, como Seguimientos): se liga por `Código actuación` (debe existir); `Fecha` es obligatoria y se valida como ISO. Las dos columnas de **descripción son informativas** (se ignoran al importar; al exportar se rellenan con la descripción de la actuación, `objetivo_impacto_es/_eu`). Es una hoja **opcional al importar**: los Excel antiguos sin ella siguen cargando. El **euskera de las etiquetas nuevas** (Fecha, Encargo realizado, Gestor operación, Resultado) es **BORRADOR**, pendiente de validar con el equipo de comunicación de HAZI.
- **Importar**: `cargar_plan_desde_excel(origen, reemplazar=False, dry_run=False)` en `src/importador.py`. Acepta path o bytes (para subidas desde Streamlit).
- **Exportar**: `exportar_plan_a_excel(plan_id)` devuelve bytes listos para `st.download_button`.
- **Dos clientes** de las mismas funciones: el script CLI `scripts/importar_plan.py` y la página `vistas/5_Administracion.py`. Esta página está organizada en **dos pestañas (`st.tabs`)**: "Carga y descarga de Planes" (descargar/subir Excel) y "Coordinación" (alta + listado de `coordinaciones` del plan activo). Las claves i18n nuevas `admin_tab_*` / `coord_*` tienen el **euskera en borrador**, pendiente de validar con comunicación de HAZI.
- **Toda carga en una transacción**: rollback completo si falla cualquier paso.

---

## Glosario de dominio

- **Plan Sectorial**: programa estratégico del Departamento (ej. Estrategia de Relevo Generacional, Plan Sectorial de Patata).
- **Ámbito**: agrupación temática dentro de un plan (ej. "Acceso a la tierra", "Conocimiento").
- **Actuación**: acción concreta con presupuesto, calendario, responsable y estado. Unidad básica de seguimiento.
- **Estado**: `Previsto` / `En curso` / `Ejecutado` (mapeo de colores: gris / ámbar / verde).
- **Seguimiento (anotación)**: corte temporal con fecha, estado y observaciones. Cada actuación acumula un historial; no se sobreescriben anotaciones previas.
- **Indicador (KPI)**: métrica numérica con meta, unidad y valores anuales. Asociado al plan, no a una actuación concreta.
- **Responsable**: organización o persona a cargo de una actuación. Códigos habituales: GV, HAZI, NEIKER, DDFF, DFA, DFB, DFG, SECTOR.
- **Coordinación**: anotación fechada del trabajo de coordinación de una actuación (encargo realizado, gestor de la operación y resultado). Diario 1:N por actuación, como los seguimientos; tabla `coordinaciones`.

---

## Cosas que NO se deben tocar sin permiso explícito

- El **esquema de la BD** (`db/schema_sqlite.sql` y `db/schema_postgres.sql`, que deben mantenerse equivalentes). Cualquier cambio implica migración de datos cargados.
- La **estructura de las 8 hojas** del Excel estandarizado (nombres de hojas, nombres de columnas, posición de cabeceras). Romperlas rompe los importadores.
- La función `asegurar_plan_id()` y la clave `_plan_id_actual` — costaron varias iteraciones de depuración.
- El **idioma de trabajo**: todo en castellano.
- Los **scripts archivados** (`scripts/archivo/`, `datos/archivo/`) son referencia histórica; no son ejemplos a imitar.

---

## Cosas que sí pueden iterarse libremente

- Estilos visuales y textos de la UI (siempre por `src/i18n.py`).
- Nuevas páginas o nuevas funcionalidades.
- Reorganización interna de funciones dentro de `src/`.
- Validaciones adicionales en el importador.
- Nuevas consultas en `src/consultas.py`.

---

## Workflow típico de cambios

1. **Leer primero** los ficheros relevantes. Para cualquier cambio que toque BD, leer `db/schema_sqlite.sql` (y, si aplica, `db/schema_postgres.sql`) para conocer los nombres exactos de columnas.
2. **Identificar el patrón existente** y mantener consistencia (estilo de mensajes, estructura de página, nombres de variables).
3. **Aplicar cambios mínimos y atómicos**. Evitar refactorizaciones grandes "de paso".
4. **Smoke test sintáctico** tras editar varios archivos:
   ```bash
   python -c "import ast; [ast.parse(open(f).read()) for f in [...]]"
   ```
5. **Reportar** qué archivos se han modificado, con un resumen de los cambios.
6. **Sugerir** al usuario que refresque con **Ctrl+Shift+R** para ver cambios visuales.

---

## Estado actual del proyecto (validado)

- 5 páginas funcionales (Visión general, Gestión, Indicadores, Resumen, Administración) + portada.
- Bilingüismo es/eu en toda la UI.
- Selector de Plan global desde la portada, propagado a todas las páginas vía `_plan_id_actual`.
- Carga y exportación de planes desde Excel, vía CLI y vía UI.
- Dos planes cargados:
  - **Estrategia de Relevo Generacional** (con datos reales, seguimientos de DIC 2025 y MAY 2026)
  - **Plan Sectorial de Patata** (recién publicado, todas las actuaciones en estado Previsto)

---

## Cosas en el roadmap

- Incorporar los seis planes pendientes (Vacuno Carne, Vacuno Leche, Bebidas, Ovino Latxo, Ecológico, Invernaderos).
- Despliegue en servidor de HAZI.
- Sistema de usuarios y permisos (Administración pasará a ser admin-only).
- Avisos automáticos en plataforma cuando se aproximen hitos.
- Exportación a PDF del Resumen del Plan.

---

## Cómo trabajar bien con este proyecto

- **El usuario es Gobierno Vasco / HAZI** (no programador a tiempo completo). Habla en castellano, claro y conciso.
- **Prefiere prompts en bloques de código copiables** para pasarlos a Claude Code desde el terminal de VSCode.
- **Prefiere iteraciones pequeñas** y comprobables con captura/refresco, no grandes refactores de golpe.
- **Pide opinión técnica honesta**, no validación cosmética. Si una idea suya tiene un trade-off, mencionarlo.
- Tras cada cambio, **decir siempre** qué archivos se modificaron y qué hacer para verificar (refresco, navegación a una página concreta, etc.).
