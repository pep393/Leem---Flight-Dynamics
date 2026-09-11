"""
export_cd_csv.py
------------------
Exporta una curva CD vs Mach a un archivo CSV con dos columnas:
    Mach, CD

Todo está fijado en el propio código (sin argumentos):
    archivo:   archivo.mat
    ángulo:    0 grados
    altitud:   1500 m
"""

import numpy as np
import scipy.io as sio


# ============== CONFIGURACIÓN (edita aquí) ==============
RUTA_MAT = "archivo.mat"
GRADOS = 0        # ángulo de ataque deseado [deg]
METROS = 1500     # altitud deseada [m]
RUTA_SALIDA = "CD_vs_Mach.csv"
# ==========================================================


def indice_mas_cercano(vector, valor):
    return int(np.argmin(np.abs(vector - valor)))


# --- Cargar datos del .mat ---
data = sio.loadmat(RUTA_MAT)
alpha = np.asarray(data["Alpha"]).flatten().astype(float)
mach = np.asarray(data["Mach"]).flatten().astype(float)
alt = np.asarray(data["Alt"]).flatten().astype(float)
cd = np.asarray(data["CD"]).astype(float)  # shape (nAlpha, nMach, nAlt)

# --- Buscar los índices más cercanos a los valores pedidos ---
idx_a = indice_mas_cercano(alpha, GRADOS)
idx_alt = indice_mas_cercano(alt, METROS)
a_real = alpha[idx_a]
alt_real = alt[idx_alt]

if a_real != GRADOS or alt_real != METROS:
    print(f"Aviso: usando el valor disponible más cercano "
          f"(α pedido={GRADOS}° -> α usado={a_real:.0f}°; "
          f"Alt pedida={METROS} m -> Alt usada={alt_real:.0f} m)")

curva_cd = cd[idx_a, :, idx_alt]  # un CD por cada Mach

# --- Exportar a CSV: Mach, CD ---
with open(RUTA_SALIDA, "w", encoding="utf-8") as f:
    f.write("Mach,CD\n")
    for m, c in zip(mach, curva_cd):
        f.write(f"{m:.3f},{c:.5f}\n")

print(f"CSV guardado en: {RUTA_SALIDA}")