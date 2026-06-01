# Archivo histórico — scripts/

Ficheros obsoletos del formato de carga inicial del plan de Relevo
Generacional. Conservados como referencia histórica.

- `importar_relevo.py` — script específico que leía los dos Excel
  originales (`datos/archivo/KPI.xlsx` y
  `datos/archivo/Seguimiento_proyecto.xlsx`).

El flujo actual es único para todos los planes: se usa
`scripts/importar_plan.py [--reemplazar]` sobre cualquier
`datos/Plan_Sectorial_<NOMBRE>.xlsx`. El formato detallado del Excel se
documenta en `Guia_de_carga_de_planes.docx`.
