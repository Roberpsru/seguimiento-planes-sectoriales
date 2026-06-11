"""
CLI para cargar un Plan Sectorial desde un Excel con la plantilla estándar
(7 hojas de datos + 1 de Instrucciones).

Es un envoltorio fino sobre `src/importador.cargar_plan_desde_excel`. La
lógica de lectura, validación e inserción vive ahí, y se comparte con la
página `vistas/5_Administracion.py`.

Uso:
    python scripts/importar_plan.py <ruta_excel> [--reemplazar] [--dry-run]
"""
import argparse
import sys
from pathlib import Path

# Permitir importar src/importador.py
RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "src"))

import db  # noqa: E402
from importador import cargar_plan_desde_excel  # noqa: E402


def _imprimir_resumen(result, dry_run):
    """Reproduce el formato de salida con prefijos [OK] / [AVISO] / [ERROR]."""
    if result["plan_codigo"]:
        print(
            f"[OK] Plan detectado: {result['plan_codigo']} - "
            f"{result['plan_nombre']}"
        )
        r = result["resumen"]
        print(
            f"     Ámbitos: {r['ambitos']} | "
            f"Responsables: {r['responsables']} | "
            f"Actuaciones: {r['actuaciones']} | "
            f"Indicadores: {r['indicadores']} | "
            f"Valores: {r['valores']} | "
            f"Seguimientos: {r['seguimientos']} | "
            f"Coordinaciones: {r.get('coordinaciones', 0)}"
        )

    print("[OK] Validando ...")
    if result["incidencias"] and result["accion"] != "preview":
        # Errores duros (no preview con plan ya existente).
        if not result["ok"] and result["accion"] == "error" \
                and not result.get("plan_existia_antes"):
            print(f"[ERROR] {len(result['incidencias'])} incidencia(s) "
                  f"encontradas:")
            for e in result["incidencias"]:
                print(f"  - {e}")
            print("[ERROR] Carga abortada.")
            return 2
    if result["incidencias"] and result["accion"] == "error" \
            and result.get("plan_existia_antes") and not dry_run:
        # Caso "ya existe sin --reemplazar".
        print(f"[ERROR] {result['mensaje']}")
        return 3

    if not result["incidencias"]:
        print("[OK] Validación correcta.")

    r = result["resumen"]
    if result["accion"] == "preview":
        if result["plan_existia_antes"]:
            print(
                f"[AVISO] El plan '{result['plan_codigo']}' ya existe en la "
                f"BD; con --reemplazar se sobrescribiría."
            )
        print(
            f"[OK] Plan {result['plan_codigo']} validado: "
            f"{r['ambitos']} ámbitos, "
            f"{r['actuaciones']} actuaciones, "
            f"{r['indicadores']} indicadores, "
            f"{r['valores']} valores, "
            f"{r['seguimientos']} seguimientos "
            f"(simulación - no se ha insertado nada)."
        )
        return 0

    if result["accion"] == "reemplazado":
        print(
            f"[AVISO] Plan existente '{result['plan_codigo']}' borrado "
            f"(y sus datos en cascada) y reemplazado por la nueva versión."
        )

    if result["accion"] in ("creado", "reemplazado"):
        print(
            f"[OK] Plan {result['plan_codigo']} cargado: "
            f"{r['ambitos']} ámbitos, "
            f"{r['actuaciones']} actuaciones, "
            f"{r['indicadores']} indicadores, "
            f"{r['valores']} valores, "
            f"{r['seguimientos']} seguimientos."
        )
        return 0

    # Fallback: error genérico
    print(f"[ERROR] {result['mensaje']}")
    return 4


def main():
    parser = argparse.ArgumentParser(
        description="Importa un Plan Sectorial desde un Excel con la "
                    "plantilla estándar."
    )
    parser.add_argument("ruta", help="Ruta al archivo Excel")
    parser.add_argument(
        "--reemplazar", action="store_true",
        help="Borra el plan existente (mismo código) antes de cargar.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Lee y valida pero NO inserta nada.",
    )
    args = parser.parse_args()

    ruta = Path(args.ruta)
    if not ruta.exists():
        print(f"[ERROR] No existe el archivo: {ruta}")
        sys.exit(1)

    print(f"[OK] Leyendo {ruta} ...")

    # Asegurar que la BD existe (la app espera schema cargado).
    db.inicializar_db()

    result = cargar_plan_desde_excel(
        ruta, reemplazar=args.reemplazar, dry_run=args.dry_run,
    )

    code = _imprimir_resumen(result, dry_run=args.dry_run)
    sys.exit(code)


if __name__ == "__main__":
    main()
