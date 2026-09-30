from pathlib import Path

def fusionar_txts_seamless(directorio_origen, nombre_salida="archivo_combinado.txt"):
    """
    Concatena todos los .txt de una carpeta de forma continua, 
    sin añadir espacios ni saltos de línea adicionales entre archivos.
    """
    dir_path = Path(directorio_origen)
    
    if not dir_path.exists():
        print(f"Error: La ruta '{directorio_origen}' no existe.")
        return

    output_path = dir_path / nombre_salida
    archivos_procesados = 0

    try:
        with open(output_path, 'w', encoding='utf-8') as outfile:
            for file_path in sorted(dir_path.glob('*.txt')):
                if file_path.resolve() == output_path.resolve():
                    continue
                
                with open(file_path, 'r', encoding='utf-8') as infile:
                    outfile.write(infile.read())
                
                archivos_procesados += 1
                
        print(f"Operación completada. Se unieron {archivos_procesados} archivos sin espacios intermedios en: {output_path}")

    except Exception as e:
        print(f"Ocurrió un error durante el proceso: {e}")

if __name__ == "__main__":
    CARPETA_OBJETIVO = "DATOS"
    fusionar_txts_seamless(CARPETA_OBJETIVO)