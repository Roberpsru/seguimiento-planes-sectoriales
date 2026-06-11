-- =====================================================================
--  MIGRACIÓN — Tabla `coordinaciones`
--  Seguimiento de Planes Sectoriales (PostgreSQL / Supabase)
--
--  Objetivo:
--    Crear la tabla `coordinaciones` (diario de coordinación por actuación:
--    encargo realizado, gestor de la operación y resultado, fechado) y
--    activar Row Level Security en ella, igual que el resto de tablas del
--    schema public (ver migracion_activar_rls.sql).
--
--  Diseño (equivalente a db/schema_postgres.sql):
--    - 1:N con actuaciones (FK ON DELETE CASCADE).
--    - La descripción de la actuación NO se almacena aquí: se obtiene por JOIN.
--    - Textos de datos bilingües (_es / _eu).
--    - `fecha` es texto ISO 'AAAA-MM-DD' y obligatoria (dato de justificación).
--
--  Idempotente: CREATE TABLE / INDEX IF NOT EXISTS. ENABLE ROW LEVEL SECURITY
--    es idempotente (re-activarlo no da error).
--
--  Aplicado en Supabase el 11/06/2026 (tabla creada + RLS activo, verificado).
--
--  Cómo aplicarlo en Supabase:
--    1. Abre el proyecto en Supabase -> "SQL Editor".
--    2. Pega TODO este fichero y ejecuta ("Run"). Debe terminar sin errores.
--    3. Comprueba en "Table editor" que aparece la tabla `coordinaciones`
--       y que el Security Advisor ya no marca aviso de RLS para ella.
--
--  Reversión (no recomendada; BORRA la tabla y sus datos):
--    -- DROP TABLE IF EXISTS coordinaciones;
-- =====================================================================

CREATE TABLE IF NOT EXISTS coordinaciones (
    id                   SERIAL PRIMARY KEY,
    actuacion_id         INTEGER NOT NULL,
    fecha                TEXT NOT NULL,             -- ISO 'AAAA-MM-DD' (obligatoria)
    encargo_realizado_es TEXT,
    encargo_realizado_eu TEXT,
    gestor_operacion_es  TEXT,
    gestor_operacion_eu  TEXT,
    resultado_es         TEXT,
    resultado_eu         TEXT,
    fecha_registro       TIMESTAMP DEFAULT now(),
    FOREIGN KEY (actuacion_id) REFERENCES actuaciones(id) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_coordinaciones_act ON coordinaciones(actuacion_id);

-- Bloquear el acceso anónimo vía la API REST pública de Supabase. La app
-- conecta como rol `postgres` (superusuario) y bypasea RLS por definición.
ALTER TABLE public.coordinaciones ENABLE ROW LEVEL SECURITY;
