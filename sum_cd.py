import pandas as pd

# 1. Configuración de parámetros
archivo_entrada = "interpolacion_mach_cd_no_prot.csv"
archivo_salida = "mach_cd_prot_sin_cono_cola.csv"
columna_a_modificar = "CD_Linear"  # Cambiar o especificar la columna deseada
cantidad_a_sumar = 0.26            # Modifica este valor según lo requieras

# 2. Cargar el archivo CSV
df = pd.read_csv(archivo_entrada)

# 3. Sumar la cantidad a la columna especificada
df[columna_a_modificar] = df[columna_a_modificar] + cantidad_a_sumar

# O bien, para sumar la cantidad a TODAS las columnas numéricas:
# df = df + cantidad_a_sumar

# 4. Exportar el resultado a un nuevo archivo CSV
df.to_csv(archivo_salida, index=False)

print(f"Proceso completado. Archivo guardado como '{archivo_salida}'.")