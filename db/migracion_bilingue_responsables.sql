-- =====================================================================
--  MIGRACIÓN BILINGÜE — tabla `responsables`
--  Seguimiento de Planes Sectoriales (PostgreSQL / Supabase)
--
--  Objetivo:
--    Añadir las dos columnas en euskera que faltan en la tabla
--    `responsables` para que el importador pueda guardar el nombre y la
--    organización del responsable en ambos idiomas.
--
--  Qué hace:
--    - NO renombra ni borra ninguna columna existente (no se pierde dato).
--    - El campo castellano sigue llamándose `nombre` / `organizacion`
--      (sin sufijo `_es`) a propósito: así el importador y las consultas
--      actuales siguen funcionando sin cambios.
--    - Sólo AÑADE `nombre_eu` y `organizacion_eu` (nullable).
--
--  Idempotente: usa ADD COLUMN IF NOT EXISTS, por lo que se puede ejecutar
--  varias veces sin error (la segunda vez no hace nada).
--
--  Cómo aplicarlo en Supabase:
--    1. Abre el proyecto en Supabase → sección "SQL Editor".
--    2. Pega TODO este fichero.
--    3. Ejecuta (botón "Run"). Debe terminar sin errores.
--    4. Comprueba en "Table editor" → tabla `responsables` que aparecen
--       las dos columnas nuevas.
--
--  Reversión (sólo si hiciera falta deshacerlo; BORRA esas columnas y su
--  contenido en euskera):
--    -- ALTER TABLE responsables DROP COLUMN IF EXISTS nombre_eu;
--    -- ALTER TABLE responsables DROP COLUMN IF EXISTS organizacion_eu;
-- =====================================================================

-- Nombre del responsable en euskera (nullable; queda NULL para los
-- responsables ya existentes hasta que se recargue el Excel con su euskera).
ALTER TABLE responsables ADD COLUMN IF NOT EXISTS nombre_eu TEXT;

-- Organización del responsable en euskera (nullable).
ALTER TABLE responsables ADD COLUMN IF NOT EXISTS organizacion_eu TEXT;
