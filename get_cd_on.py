import numpy as np
import pandas as pd


def calcular_cd_propulsion(
    archivo_entrada, archivo_salida, D_base=None, D_exit=None, S=None, A_e=None
):
    """Calcula el Cd con propulsiÃ³n y exporta un CSV con solo mach y cdPowerOn."""
    # 1. Cargar el CSV de entrada (Mach, Cd Power Off)
    df = pd.read_csv(archivo_entrada, header=None, names=["mach", "cd_power_off"])

    # 2. Calcular Ã¡reas si se han proporcionado diÃ¡metros
    if D_base is not None and D_exit is not None:
        S = np.pi * (D_base / 2) ** 2
        A_e = np.pi * (D_exit / 2) ** 2

    if S is None or A_e is None:
        raise ValueError(
            "Debes proporcionar las Ã¡reas (S, A_e) o los diÃ¡metros (D_base, D_exit)."
        )

    # 3. Factor de correcciÃ³n geomÃ©trica: (S - A_e) / S
    factor = (S - A_e) / S

    # 4. Crear el DataFrame final solo con las dos columnas deseadas
    df_salida = pd.DataFrame(
        {"mach": df["mach"], "cdPowerOn": df["cd_power_off"] * factor}
    )

    # 5. Exportar al nuevo CSV
    df_salida.to_csv(archivo_salida, index=False)
    print(f"Archivo exportado con Ã©xito a: {archivo_salida}")

    return df_salida


# --- EJEMPLO DE USO ---
df_resultado = calcular_cd_propulsion(
    archivo_entrada="mach_cd_prot_sin_cono_cola.csv",
    archivo_salida="mach_cd_prot_sin_cono_cola_power_on.csv",
    D_base= 0.08656,
    D_exit=0.06,  
)

print("\nVista previa del resultado:")
print(df_resultado.head())