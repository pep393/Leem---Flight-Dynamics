"""
Filtro de aletas procedurales para cohetes
==========================================
Lee un archivo .txt con datos de aletas y filtra/ordena según criterios:
  - Estabilidad mínima (MIN) > 2
  - Root >= Span >= Tip
  - Ordenadas por área (de menor a mayor)

Formato esperado de cada línea:
  ID | Stab MIN valor MAX valor | Flutter SF min: valor | Root: valor, Tip: valor, Span: valor
"""

import re
import math

# ─── CONFIGURACIÓN ───────────────────────────────────────────────────────────
INPUT_FILE = "fins.txt"   # <- Cambia aquí el nombre de tu archivo
# ─────────────────────────────────────────────────────────────────────────────


def parse_fins(filepath):
    """Lee y parsea el archivo de aletas."""
    fins = []
    pattern = re.compile(
        r"(\d+)\s*\|\s*Stab MIN\s+([\d.]+)\s+MAX\s+([\d.]+)\s*"
        r"\|\s*Flutter SF min:\s+([\d.nan]+)\s*"
        r"\|\s*Root:\s+([\d.]+),\s*Tip:\s+([\d.]+),\s*Span:\s+([\d.]+)"
    )

    with open(filepath, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            m = pattern.match(line)
            if m:
                fins.append({
                    "id":         int(m.group(1)),
                    "min":        float(m.group(2)),
                    "max":        float(m.group(3)),
                    "flutter_sf": float(m.group(4)) if m.group(4) != "nan" else float("nan"),
                    "root":       float(m.group(5)),
                    "tip":        float(m.group(6)),
                    "span":       float(m.group(7)),
                })
            else:
                print(f"  [AVISO] Línea no reconocida: {line!r}")

    return fins


def trapezoid_area(root, tip, span):
    """Área de una aleta trapezoidal: (root + tip) / 2 * span"""
    return (root + tip) / 2 * span


def filter_and_sort(fins):
    """Aplica los tres filtros y ordena por área ascendente."""
    filtered = []
    for fin in fins:
        # Criterio 1: estabilidad mínima > 2
        if fin["min"] <= 1.5:
            continue
        if fin["max"] >= 3:
            continue
        # Criterio 2: root >= span  y  span >= tip
        if not (fin["root"] >= fin["span"] >= fin["tip"]):
            continue
        fin["area"] = trapezoid_area(fin["root"], fin["tip"], fin["span"])
        filtered.append(fin)

    # Ordenar por área ascendente
    filtered.sort(key=lambda x: x["area"])
    return filtered


def print_results(fins):
    """Muestra los resultados en una tabla legible."""
    if not fins:
        print("No se encontraron aletas que cumplan todos los criterios.")
        return

    header = (f"{'ID':>5}  {'MIN':>6}  {'MAX':>6}  {'Flutter SF':>10}  "
              f"{'Root':>6}  {'Tip':>6}  {'Span':>6}  {'Área':>8}")
    sep = "-" * len(header)
    print(f"\nAletas válidas ({len(fins)} encontradas), ordenadas por área:\n")
    print(header)
    print(sep)
    for f in fins:
        sf_str = f"{f['flutter_sf']:>10.3f}" if not math.isnan(f["flutter_sf"]) else f"{'nan':>10}"
        print(
            f"{f['id']:>5}  {f['min']:>6.3f}  {f['max']:>6.3f}  {sf_str}  "
            f"{f['root']:>6.3f}  {f['tip']:>6.3f}  {f['span']:>6.3f}  "
            f"{f['area']:>8.5f}"
        )
    print(sep)
    print(f"  Área mínima : {fins[0]['area']:.5f}  (ID {fins[0]['id']})")
    print(f"  Área máxima : {fins[-1]['area']:.5f}  (ID {fins[-1]['id']})")


def main():
    print(f"Leyendo archivo: {INPUT_FILE}")
    try:
        fins = parse_fins(INPUT_FILE)
    except FileNotFoundError:
        print(f"\n[ERROR] No se encontró el archivo '{INPUT_FILE}'.")
        print("Coloca el script y el .txt en la misma carpeta, o edita INPUT_FILE.")
        return

    print(f"  {len(fins)} aletas leídas.")
    result = filter_and_sort(fins)
    print_results(result)


if __name__ == "__main__":
    main()