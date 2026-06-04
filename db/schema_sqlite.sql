-- =====================================================================
--  SEGUIMIENTO DE PLANES SECTORIALES
--  Departamento de Alimentación, Desarrollo Rural, Agricultura y Pesca
--  Esquema de base de datos (SQLite)
--
--  Diseño bilingüe (campos _es / _eu) y multiplan: una misma estructura
--  sirve para todos los planes (Relevo generacional, Patata, Vacuno, etc.)
-- =====================================================================

PRAGMA foreign_keys = ON;

-- ---------------------------------------------------------------------
-- PLANES: cada Plan Sectorial
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS planes (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
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
    fecha_creacion      TEXT DEFAULT (datetime('now'))
);

-- ---------------------------------------------------------------------
-- AMBITOS: ejes de intervención dentro de un plan
--   (Relevo: 5.1, 5.2...  |  Patata: Conocimiento, Sostenibilidad...)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS ambitos (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id     INTEGER NOT NULL,
    codigo      TEXT,                                -- ej. '5.1', 'CON'
    nombre_es   TEXT NOT NULL,
    nombre_eu   TEXT,
    orden       INTEGER DEFAULT 0,
    FOREIGN KEY (plan_id) REFERENCES planes(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- ORGANIZACIONES / RESPONSABLES
--   (GV, DFA, DFB, DFG, HAZI, NEIKER, SECTOR...). El email queda
--   preparado para el futuro envío de avisos, hoy puede ir vacío.
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS responsables (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
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
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    ambito_id             INTEGER NOT NULL,
    codigo                TEXT,                      -- numeración propia del plan
    nombre_es             TEXT NOT NULL,
    nombre_eu             TEXT,
    objetivo_impacto_es   TEXT,
    objetivo_impacto_eu   TEXT,
    instrumento_programa  TEXT,                      -- ej. GAZTENEK, SENDOTU
    presupuesto           REAL,                      -- NULL si no procede
    presupuesto_nota      TEXT,                      -- ej. 'Sin dotación', 'N/D'
    presupuesto_ejecutado REAL,
    fecha_inicio_prevista TEXT,                      -- texto libre o fecha ISO
    fecha_fin_prevista    TEXT,
    estado                TEXT DEFAULT 'Previsto',   -- Previsto / En curso / Ejecutado
    orden                 INTEGER DEFAULT 0,
    notas_es              TEXT,
    notas_eu              TEXT,
    FOREIGN KEY (ambito_id) REFERENCES ambitos(id) ON DELETE CASCADE
);

-- Relación N:M actuación <-> responsables (una actuación puede tener varias orgs)
CREATE TABLE IF NOT EXISTS actuacion_responsables (
    actuacion_id   INTEGER NOT NULL,
    responsable_id INTEGER NOT NULL,
    PRIMARY KEY (actuacion_id, responsable_id),
    FOREIGN KEY (actuacion_id)   REFERENCES actuaciones(id)  ON DELETE CASCADE,
    FOREIGN KEY (responsable_id) REFERENCES responsables(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- SEGUIMIENTOS: bitácora de estado por fecha de corte
--   (esto recoge los "Estado DIC 2025 / Estado MAY 2026" como histórico)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS seguimientos (
    id                    INTEGER PRIMARY KEY AUTOINCREMENT,
    actuacion_id          INTEGER NOT NULL,
    fecha_corte           TEXT NOT NULL,             -- ej. '2025-12-01'
    etiqueta_corte        TEXT,                      -- ej. 'DIC 2025'
    estado                TEXT,                      -- estado en ese corte
    detalle_es            TEXT,
    detalle_eu            TEXT,
    porcentaje_ejecucion  REAL,                      -- 0-100
    presupuesto_ejecutado REAL,
    autor                 TEXT,
    fecha_registro        TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (actuacion_id) REFERENCES actuaciones(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- INDICADORES (KPI)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS indicadores (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
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
    meta_valor     REAL,                             -- meta numérica si aplica
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
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    indicador_id    INTEGER NOT NULL,
    periodo         TEXT NOT NULL,                   -- '2025', '2026', 'Intermedio', 'Meta'...
    valor           REAL,                            -- valor numérico
    valor_texto_es  TEXT,                            -- valor descriptivo
    valor_texto_eu  TEXT,
    nota_es         TEXT,
    nota_eu         TEXT,
    fecha_registro  TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (indicador_id) REFERENCES indicadores(id) ON DELETE CASCADE
);

-- ---------------------------------------------------------------------
-- ALERTAS manuales (las automáticas se calculan al vuelo desde los datos)
-- ---------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS alertas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_id         INTEGER,
    actuacion_id    INTEGER,
    tipo            TEXT DEFAULT 'manual',           -- manual / automatica
    nivel           TEXT DEFAULT 'aviso',            -- info / aviso / riesgo
    mensaje_es      TEXT,
    mensaje_eu      TEXT,
    fecha_creacion  TEXT DEFAULT (datetime('now')),
    resuelta        INTEGER DEFAULT 0,               -- 0/1
    fecha_resolucion TEXT,
    FOREIGN KEY (plan_id)      REFERENCES planes(id)      ON DELETE CASCADE,
    FOREIGN KEY (actuacion_id) REFERENCES actuaciones(id) ON DELETE CASCADE
);

-- Índices útiles
CREATE INDEX IF NOT EXISTS idx_ambitos_plan        ON ambitos(plan_id);
CREATE INDEX IF NOT EXISTS idx_actuaciones_ambito  ON actuaciones(ambito_id);
CREATE INDEX IF NOT EXISTS idx_seguimientos_act    ON seguimientos(actuacion_id);
CREATE INDEX IF NOT EXISTS idx_indicadores_plan    ON indicadores(plan_id);
CREATE INDEX IF NOT EXISTS idx_indvalores_ind      ON indicador_valores(indicador_id);
