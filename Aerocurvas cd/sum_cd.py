import pandas as pd

# Configuración
archivo_entrada = 'mach_cd_sin_chaflan_preciso.csv'
archivo_salida = 'mach_cd_sin_chaflan_preciso_power_on.csv'
col_idx = 1      # 0 = primera columna, 1 = segunda columna
offset = 0.025     # Valor a sumar (usar negativo para restar)

# Cargar indicando que no hay cabecera
df = pd.read_csv(archivo_entrada, header=None)

# Modificar la columna por su posición entera
df[col_idx] = df[col_idx] - offset

# Guardar manteniendo el formato original (sin cabeceras ni índice de filas)
df.to_csv(archivo_salida, header=False, index=False)