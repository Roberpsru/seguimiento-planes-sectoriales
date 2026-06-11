# Checklist — Primera carga en Supabase (PostgreSQL)

Guía para la **carga inicial** de los Planes Sectoriales en una base de datos
PostgreSQL de Supabase, y para configurar el despliegue en Streamlit Cloud.

La aplicación es de **persistencia dual**: usa SQLite en local y PostgreSQL si
existe `DATABASE_URL` (ver sección «Persistencia» en `CLAUDE.md` / `README.md`).
En PostgreSQL la carga inicial es **manual** (no se hace en cada arranque, para
no duplicar datos): es exactamente lo que cubre este documento.

Pensado para Windows + PowerShell, ejecutado desde una red **sin** el bloqueo de
puerto de HAZI.

---

## 0. Requisitos previos

- [ ] Proyecto creado en Supabase.
- [ ] Estás en una red que **no bloquea el puerto** de Supabase (5432/6543). La
      red de HAZI lo bloquea → hazlo desde casa, móvil compartiendo datos, u
      otra red.
- [ ] Entorno virtual activado y dependencias instaladas (incluye el nuevo
      `psycopg2-binary`):

```powershell
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 1. Obtener la cadena de conexión

En Supabase: **Project Settings → Database → Connection string → URI**.

Usa la de **Session pooler** (es IPv4 y va bien para esta carga puntual). Tiene
esta forma:

```
postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres
```

- [ ] Sustituye `<password>` por la contraseña real de la BD.
- [ ] Si la contraseña tiene caracteres especiales (`@ : / # ?`), hay que
      **URL-encodearlos** (p. ej. `@` → `%40`).
- [ ] Añade SSL al final (Supabase lo exige): `?sslmode=require`.

Cadena final de ejemplo:

```
postgresql://postgres.abcxyz:MiPass%40123@aws-0-eu-west-3.pooler.supabase.com:6543/postgres?sslmode=require
```

## 2. Apuntar la app a Supabase en esta sesión de PowerShell

```powershell
$env:DATABASE_URL = "postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres?sslmode=require"
```

Compruébalo:

```powershell
echo $env:DATABASE_URL
```

> Esta variable vive **solo en esta ventana** de PowerShell. Al cerrarla
> desaparece (justo lo que queremos para una carga puntual).

## 3. Crear el esquema en Supabase

El script de importación ya crea el esquema solo, pero puedes hacerlo explícito
y comprobar que la conexión funciona:

```powershell
python -m src.db
```

Debe imprimir `Base de datos lista. Motor de BD: postgres` (no se muestra la
cadena de conexión, por seguridad). Si falla aquí, es conexión
(red/cadena/SSL), no datos.

## 4. Cargar los dos planes

```powershell
python scripts/importar_plan.py datos/Plan_Sectorial_Relevo_Generacional.xlsx
python scripts/importar_plan.py datos/Plan_Sectorial_Patata.xlsx
```

- [ ] Cada uno debe terminar con `[OK] Plan ... cargado: N ámbitos, ...`.
- [ ] Si un plan ya existía (recarga), añade `--reemplazar`.

## 5. Verificar la carga

```powershell
python -c "import sys; sys.path.insert(0,'src'); import consultas; [print(p['codigo'], '-', p['nombre_es']) for p in consultas.listar_planes()]"
```

Debe listar **PATATA** y **RELEVO_GEN**. (Como `DATABASE_URL` sigue puesta, esto
consulta Supabase, no el SQLite local.)

Opcional, arrancar la app local apuntando ya a Supabase para verla con datos
reales:

```powershell
streamlit run app.py
```

## 6. Configurar Streamlit Cloud (despliegue)

En la app de Streamlit Cloud: **Settings → Secrets**, y pega:

```toml
DATABASE_URL = "postgresql://postgres.<ref>:<password>@aws-0-<region>.pooler.supabase.com:6543/postgres?sslmode=require"
```

- [ ] Con esto, la app desplegada usa Supabase automáticamente (no inicializa ni
      carga nada: en PostgreSQL la carga es manual, la que acabas de hacer).
- [ ] **No** subas `secrets.toml` al repo (ya está en `.gitignore`). La
      plantilla versionada es `.streamlit/secrets.toml.example`.

---

## Notas y posibles tropiezos

- **Idempotencia del esquema**: `python -m src.db` usa
  `CREATE TABLE IF NOT EXISTS`, no borra datos. Repetirlo es inofensivo.
- **Recargar un plan**: `python scripts/importar_plan.py <excel> --reemplazar`
  borra el plan existente (en cascada) y lo vuelve a cargar.
- **Si `python -m src.db` o el import fallan con timeout**: casi siempre es el
  puerto bloqueado (red de HAZI) o falta `?sslmode=require`.
- **Pooler vs directo**: la conexión directa (`db.<ref>.supabase.co:5432`) es
  solo IPv6 salvo que tengas el add-on IPv4; por eso se recomienda el **pooler**
  (IPv4) tanto para la carga como para la app.
- **Volver a trabajar en local con SQLite**: cierra la ventana de PowerShell, o
  limpia la variable y la app vuelve a SQLite:
  ```powershell
  Remove-Item Env:\DATABASE_URL
  ```
