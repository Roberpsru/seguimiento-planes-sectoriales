-- =====================================================================
--  SEGUIMIENTO DE PLANES SECTORIALES
--  Departamento de Alimentación, Desarrollo Rural, Agricultura y Pesca
--  Esquema de base de datos (PostgreSQL / Supabase)
--
--  Equivalente a db/schema_sqlite.sql. Diferencias respecto a SQLite:
--    - INTEGER PRIMARY KEY AUTOINCREMENT  ->  SERIAL PRIMARY KEY
--    - REAL                               ->  DOUBLE PRECISION
--    - INTEGER 0/1 usado como booleano    ->  BOOLEAN
--    - datetime('now') (default)          ->  now() / TIMESTAMP
--
--  NOTA sobre fechas: las columnas fecha_inicio_prevista / fecha_fin_prevista
--  y el campo 'periodo' de indicador_valores se mantienen como TEXT en ambos
--  motores PORQUE almacenan TEXTO LIBRE (p. ej. "1º semestre 2025", o el año
--  "2025" como cadena) y el código de la app los compara como cadenas. Pasarlas
--  a DATE/INTEGER rompería la lógica existente.
-- =====================================================================

-- ---------------------------------------------------------------------
-- PLANES: cada Plan Sectorial
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS planes (
    id                  SERIAL PRIMARY KEY,
    codigo              TEXT UNIQUE,                 -- ej. 'RELEVO', 'PATATA'
    nombre_es           TEXT NOT NULL,
    nombre_eu           TEXT,
    descripcion_es      TEXT,
    descripcion_eu      TEXT,
    departamento        TEXT,
    periodo_inicio      INTEGER,                     -- año
    periodo_fin         INTEGER,                     -- año
    objetivo_macro_es   TEXT,
    objetivo_macro_eu   TEXT,
    estado              TEXT DEFAULT 'Activo',       -- Activo / Borrador / Cerrado
    fecha_creacion      TIMESTAMP DEFAULT now()
);

-- ---------------------------------------------------------------------
-- AMBITOS: ejes de intervención dentro de un plan
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ambitos (
    id          SERIAL PRIMARY KEY,
    plan_id     INTEGER NOT NULL,
    codigo      TEXT,                                -- ej. '5.1', 'CON'
    nombre_es   TEXT NOT NULL,
    nombre_eu   TEXT,
    orden       INTEGER DEFAULT 0,
    FOREIGN KEY (plan_id) REFERENCES planes(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- ORGANIZACIONES / RESPONSABLES
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS responsables (
    id              SERIAL PRIMARY KEY,
    nombre          TEXT NOT NULL,        -- castellano (no se renombra: lo usa el importador)
    nombre_eu       TEXT,
    organizacion    TEXT,                 -- castellano
    organizacion_eu TEXT,
    email           TEXT
);

-- ---------------------------------------------------------------------
-- ACTUACIONES: el corazón del seguimiento
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS actuaciones (
    id                    SERIAL PRIMARY KEY,
    ambito_id             INTEGER NOT NULL,
    codigo                TEXT,                      -- numeración propia del plan
    nombre_es             TEXT NOT NULL,
    nombre_eu             TEXT,
    objetivo_impacto_es   TEXT,
    objetivo_impacto_eu   TEXT,
    instrumento_programa  TEXT,                      -- ej. GAZTENEK, SENDOTU
    presupuesto           DOUBLE PRECISION,          -- NULL si no procede
    presupuesto_nota      TEXT,                      -- ej. 'Sin dotación', 'N/D'
    presupuesto_ejecutado DOUBLE PRECISION,
    fecha_inicio_prevista TEXT,                      -- texto libre o fecha ISO
    fecha_fin_prevista    TEXT,
    estado                TEXT DEFAULT 'Previsto',   -- Previsto / En curso / Ejecutado
    orden                 INTEGER DEFAULT 0,
    notas_es              TEXT,
    notas_eu              TEXT,
    FOREIGN KEY (ambito_id) REFERENCES ambitos(id) ON DELETE CASCADE
);

-- Relación N:M actuación <-> responsables
CREATE TABLE IF NOT EXISTS actuacion_responsables (
    actuacion_id   INTEGER NOT NULL,
    responsable_id INTEGER NOT NULL,
    PRIMARY KEY (actuacion_id, responsable_id),
    FOREIGN KEY (actuacion_id)   REFERENCES actuaciones(id)  ON DELETE CASCADE,
    FOREIGN KEY (responsable_id) REFERENCES responsables(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- SEGUIMIENTOS: bitácora de estado por fecha de corte
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS seguimientos (
    id                    SERIAL PRIMARY KEY,
    actuacion_id          INTEGER NOT NULL,
    fecha_corte           TEXT NOT NULL,             -- ej. '2025-12-01'
    etiqueta_corte        TEXT,                      -- ej. 'DIC 2025'
    estado                TEXT,                      -- estado en ese corte
    detalle_es            TEXT,
    detalle_eu            TEXT,
    porcentaje_ejecucion  DOUBLE PRECISION,          -- 0-100
    presupuesto_ejecutado DOUBLE PRECISION,
    autor                 TEXT,
    fecha_registro        TIMESTAMP DEFAULT now(),
    FOREIGN KEY (actuacion_id) REFERENCES actuaciones(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- INDICADORES (KPI)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS indicadores (
    id             SERIAL PRIMARY KEY,
    plan_id        INTEGER NOT NULL,
    ambito_id      INTEGER,                          -- opcional
    categoria      TEXT,                             -- Resultado/Impacto, Ejecución, Apoyo y seguimiento
    numero         INTEGER,
    nombre_es      TEXT NOT NULL,
    nombre_eu      TEXT,
    definicion_es  TEXT,
    definicion_eu  TEXT,
    meta_es        TEXT,                             -- meta como texto (ej. '≥ 85%')
    meta_eu        TEXT,
    meta_valor     DOUBLE PRECISION,                 -- meta numérica si aplica
    unidad         TEXT,
    desarrollo_es  TEXT,                             -- cómo se calcula / notas
    desarrollo_eu  TEXT,
    orden          INTEGER DEFAULT 0,
    FOREIGN KEY (plan_id)   REFERENCES planes(id)   ON DELETE CASCADE,
    FOREIGN KEY (ambito_id) REFERENCES ambitos(id)  ON DELETE SET NULL
);

-- ---------------------------------------------------------------------
-- VALORES DE INDICADORES por periodo (admite valor numérico o textual)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS indicador_valores (
    id              SERIAL PRIMARY KEY,
    indicador_id    INTEGER NOT NULL,
    periodo         TEXT NOT NULL,                   -- '2025', '2026', 'Intermedio', 'Meta'...
    valor           DOUBLE PRECISION,                -- valor numérico
    valor_texto_es  TEXT,                            -- valor descriptivo
    valor_texto_eu  TEXT,
    nota_es         TEXT,
    nota_eu         TEXT,
    fecha_registro  TIMESTAMP DEFAULT now(),
    FOREIGN KEY (indicador_id) REFERENCES indicadores(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- COORDINACIONES: diario de coordinación por actuación
--   (qué encargo se hizo, quién gestiona la operación y con qué resultado).
--   1:N con actuaciones. La descripción de la actuación NO se almacena aquí:
--   se obtiene por JOIN. Los textos de datos son bilingües (_es / _eu);
--   fecha es ISO 'AAAA-MM-DD' y obligatoria (dato de justificación).
-- ---------------------------------------------------------------------
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

-- ---------------------------------------------------------------------
-- ALERTAS manuales (la app aún no las usa)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alertas (
    id              SERIAL PRIMARY KEY,
    plan_id         INTEGER,
    actuacion_id    INTEGER,
    tipo            TEXT DEFAULT 'manual',           -- manual / automatica
    nivel           TEXT DEFAULT 'aviso',            -- info / aviso / riesgo
    mensaje_es      TEXT,
    mensaje_eu      TEXT,
    fecha_creacion  TIMESTAMP DEFAULT now(),
    resuelta        BOOLEAN DEFAULT FALSE,
    fecha_resolucion TIMESTAMP,
    FOREIGN KEY (plan_id)      REFERENCES planes(id)      ON DELETE CASCADE,
    FOREIGN KEY (actuacion_id) REFERENCES actuaciones(id) ON DELETE CASCADE
);

-- Índices útiles
CREATE INDEX IF NOT EXISTS idx_ambitos_plan        ON ambitos(plan_id);
CREATE INDEX IF NOT EXISTS idx_actuaciones_ambito  ON actuaciones(ambito_id);
CREATE INDEX IF NOT EXISTS idx_seguimientos_act    ON seguimientos(actuacion_id);
CREATE INDEX IF NOT EXISTS idx_indicadores_plan    ON indicadores(plan_id);
CREATE INDEX IF NOT EXISTS idx_indvalores_ind      ON indicador_valores(indicador_id);
CREATE INDEX IF NOT EXISTS idx_coordinaciones_act  ON coordinaciones(actuacion_id);
