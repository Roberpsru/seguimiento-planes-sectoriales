-- =====================================================================
--  MIGRACIÓN — Activar Row Level Security (RLS)
--  Seguimiento de Planes Sectoriales (PostgreSQL / Supabase)
--
--  Objetivo:
--    Bloquear el acceso anónimo a las tablas a través de la API REST
--    pública de Supabase. La app sigue funcionando porque conecta
--    directamente a PostgreSQL con el rol `postgres` (superusuario),
--    que bypasea RLS por definición.
--
--  Aplicado en Supabase el 10/06/2026.
--
--  NOTA: si en el futuro se añaden tablas nuevas al schema public,
--  hay que activar RLS también en ellas o el Security Advisor de
--  Supabase volverá a marcar el aviso.
--
--  Reversión (no recomendada — reabre la vulnerabilidad):
--    -- ALTER TABLE public.<tabla> DISABLE ROW LEVEL SECURITY;
-- =====================================================================

ALTER TABLE public.planes                  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.ambitos                 ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.responsables            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.actuaciones             ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.actuacion_responsables  ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.seguimientos            ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.indicadores             ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.indicador_valores       ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.alertas                 ENABLE ROW LEVEL SECURITY;
