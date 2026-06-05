# Seguimiento de Planes Sectoriales

Aplicación web de seguimiento operativo y ejecutivo de los **Planes Sectoriales** del **Departamento de Alimentación, Desarrollo Rural, Agricultura y Pesca** del **Gobierno Vasco**, desarrollada con apoyo de **HAZI**.

Permite centralizar el seguimiento de todas las actuaciones, presupuestos e indicadores de cada plan desde un único punto de consulta y edición, con soporte bilingüe castellano/euskera.

---

## Funcionalidad

La aplicación se organiza en una portada y cinco páginas funcionales:

- **Portada** — presentación del alcance con logos institucionales y selector de Plan activo.
- **Visión general** — resumen del plan seleccionado: métricas clave, presupuesto por ámbito, listado de actuaciones por estado y catálogo de indicadores agrupados por categoría.
- **Gestión de actuaciones** — edición operativa: cambio de estado (Previsto / En curso / Ejecutado), presupuesto ejecutado, fechas previstas y registro de anotaciones en el historial de seguimiento.
- **Indicadores (KPI)** — edición de valores anuales, meta numérica y visualización del avance respecto al objetivo con gráficos comparativos.
- **Resumen del Plan** — informe ejecutivo consolidado con métricas globales, distribución por estado, avance presupuestario por ámbito, semáforo de indicadores y últimos movimientos.
- **Administración** — carga (subir Excel) y descarga (exportar a Excel) de planes completos, con preview y confirmación antes de cualquier reemplazo.

La interfaz cambia entre castellano y euskera con un selector en el sidebar.

---

## Planes incorporados

- **Estrategia de Relevo Generacional** (2025-2028) — 8 ámbitos, 22 actuaciones, 11 indicadores.
- **Plan Sectorial de Patata de Consumo y Siembra en Euskadi** (2026-2030) — 5 ámbitos, 27 actuaciones, 8 indicadores.

Previstos para incorporación progresiva: Vacuno de Carne, Vacuno de Leche, Bebidas, Ovino Latxo, Ecológico e Invernaderos.

---

## Stack técnico

- **Python 3.11+**
- **Streamlit** — interfaz web multipágina
- **Persistencia dual** — **SQLite** en local (`db/seguimiento.db`) y **PostgreSQL** (Supabase) en despliegue, sin cambiar código (ver [Persistencia](#persistencia-sqlite--postgresql)).
- **pandas + openpyxl** — lectura y escritura de Excel
- **Plotly** — gráficos interactivos
- **psycopg2** — driver de PostgreSQL

---

## Persistencia (SQLite / PostgreSQL)

La aplicación funciona indistintamente sobre **SQLite** (local) o **PostgreSQL**
(Supabase, para el despliegue) sin cambiar el código. El motor se decide en el
arranque a partir de la variable `DATABASE_URL`:

1. Si existe la **variable de entorno** `DATABASE_URL` → PostgreSQL con esa URL.
2. Si existe `st.secrets["DATABASE_URL"]` (Streamlit Cloud) → PostgreSQL con esa URL.
3. En cualquier otro caso → **SQLite** en `db/seguimiento.db`.

Para usar PostgreSQL en local (no recomendado desde la red de HAZI, que bloquea
el puerto), copia la plantilla y rellena la cadena real:

```bash
cp .streamlit/secrets.toml.example .streamlit/secrets.toml
# Edita DATABASE_URL con la cadena de Supabase. secrets.toml NO se versiona.
```

Cadena típica de Supabase (pooler en el puerto 6543):

```
postgresql://usuario:contraseña@host:6543/postgres
```

**Carga inicial de datos:**

- En **SQLite** la carga es automática: si la BD está vacía, el arranque crea el
  esquema (`db/schema_sqlite.sql`) y carga los Excel de `datos/`.
- En **PostgreSQL** la carga inicial es **manual** (no se hace en cada arranque,
  para no duplicar datos). Crea el esquema y carga los planes una vez con el CLI,
  desde una red sin restricciones:
  ```bash
  # Con DATABASE_URL apuntando a Supabase:
  python -m src.db                       # crea el esquema (schema_postgres.sql)
  python scripts/importar_plan.py datos/Plan_Sectorial_Relevo_Generacional.xlsx
  python scripts/importar_plan.py datos/Plan_Sectorial_Patata.xlsx
  ```

---

## Instalación y arranque local

1. Clonar el repositorio y entrar en la carpeta del proyecto.

2. Crear y activar entorno virtual:
   ```bash
   python -m venv .venv
   # Windows PowerShell:
   .\.venv\Scripts\Activate.ps1
   # macOS / Linux:
   source .venv/bin/activate
   ```

3. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

4. Arrancar la aplicación:
   ```bash
   streamlit run app.py
   ```
   En local (SQLite), si la BD no existe o está vacía, **se crea y se cargan
   automáticamente** todos los planes de `datos/Plan_Sectorial_*.xlsx` en el
   primer arranque. No hace falta ningún paso manual.

   (Opcional) Si prefieres cargar los planes a mano antes de arrancar:
   ```bash
   python scripts/importar_plan.py datos/Plan_Sectorial_Relevo_Generacional.xlsx
   python scripts/importar_plan.py datos/Plan_Sectorial_Patata.xlsx
   ```

5. Abrir el navegador en [http://localhost:8501](http://localhost:8501).

---

## Estructura del proyecto

```
seguimiento_planes/
├── app.py                              # Router: st.navigation + selector de idioma
├── vistas/                             # Páginas (st.Page); NO usar el nombre mágico pages/
│   ├── Inicio.py                       # Portada: logos, intro y selector de Plan
│   ├── 1_Vision_general.py
│   ├── 2_Gestion_actuaciones.py
│   ├── 3_Indicadores.py
│   ├── 4_Resumen_del_Plan.py
│   └── 5_Administracion.py            # Carga / descarga de Excel
├── src/
│   ├── db.py                           # Conexión agnóstica (SQLite / PostgreSQL)
│   ├── arranque.py                     # Init automático de la BD (solo SQLite)
│   ├── consultas.py                    # Queries reutilizables
│   ├── i18n.py                         # Bilingüismo + selectores globales
│   ├── tema.py                         # CSS verde institucional
│   └── importador.py                   # Carga / exportación Excel <-> BD
├── scripts/
│   ├── importar_plan.py               # CLI: wrapper sobre src/importador.py
│   └── archivo/
│       └── importar_relevo.py         # Obsoleto, conservado como referencia
├── datos/
│   ├── gova.jpg, hazi.jpg              # Logos institucionales
│   ├── Plan_Sectorial_Relevo_Generacional.xlsx
│   ├── Plan_Sectorial_Patata.xlsx
│   └── archivo/                        # Excel originales no estandarizados
├── db/
│   ├── schema_sqlite.sql               # Esquema SQLite
│   ├── schema_postgres.sql             # Esquema PostgreSQL (equivalente)
│   └── seguimiento.db                  # BD local (no versionada)
├── .streamlit/
│   ├── config.toml                     # Tema visual de Streamlit (versionado)
│   └── secrets.toml.example            # Plantilla de DATABASE_URL (versionada)
├── requirements.txt
├── README.md
└── CLAUDE.md                           # Contexto para Claude Code
```

---

## Carga y actualización de planes

Todos los planes se cargan desde un formato Excel estandarizado: `datos/Plan_Sectorial_<NOMBRE>.xlsx` con 8 hojas (Instrucciones, Plan, Ámbitos, Responsables, Actuaciones, Indicadores, Valores_indicadores, Seguimientos).

### Desde la aplicación (recomendado para usuarios no técnicos)

Página **Administración**:
1. **Descargar** el Excel del plan actual con el botón correspondiente.
2. Editarlo cómodamente fuera de la app.
3. **Subir** el Excel modificado. La app detecta si el plan es nuevo o existente, muestra el impacto (qué se va a sustituir) y pide confirmación.

### Desde la línea de comandos

```bash
python scripts/importar_plan.py datos/Plan_Sectorial_<NOMBRE>.xlsx [--reemplazar] [--dry-run]
```

- Sin flags: aborta si el plan ya existe.
- `--reemplazar`: borra el plan existente y lo recarga.
- `--dry-run`: valida sin insertar.

### Crear un plan nuevo desde cero

1. Duplicar uno de los Excel existentes (`datos/Plan_Sectorial_Patata.xlsx` o `Plan_Sectorial_Relevo_Generacional.xlsx`) como punto de partida.
2. Vaciar las filas de datos y rellenar las 7 hojas (Plan, Ámbitos, Responsables, Actuaciones, Indicadores, Valores_indicadores, Seguimientos) con la información del nuevo plan. La hoja `Instrucciones` no se procesa.
3. Guardar como `Plan_Sectorial_<NOMBRE>.xlsx` y cargar por cualquiera de los dos métodos. Para validar el formato sin escribir en la BD, usar `--dry-run`.

---

## Documentación adjunta

- **CLAUDE.md** — guía para Claude Code y futuros desarrolladores: convenciones, decisiones técnicas, pitfalls.
- **documentos/Guia_de_uso.docx** y **documentos/Guia_de_carga_de_planes.docx** — documentación funcional y guía detallada del formato Excel (pendientes de elaborar).
- **documentos/Plantilla_Plan_Sectorial.xlsx** — plantilla en blanco para nuevos planes (pendiente; mientras tanto, duplicar uno de los Excel existentes en `datos/`).

---

## Estado del proyecto

En desarrollo activo. Próximos pasos previstos:
- Incorporación progresiva de los seis planes sectoriales pendientes.
- Despliegue en servidor de HAZI con acceso para el Departamento.
- Sistema de usuarios y permisos (la página de Administración debería ser solo para administradores).
- Avisos automáticos en plataforma cuando se aproximan hitos de actuaciones.
- Exportación a PDF del Resumen del Plan para informes.

---

## Contacto

Para cualquier mejora, error o solicitud de incorporación de plan, contactar con el responsable técnico de la aplicación en HAZI.
