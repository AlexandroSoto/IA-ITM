import pandas as pd
import os

# Archivos a limpiar
archivos = [
    ('datos_bala_horizontal.csv', 'velocidad_bala_h', 'distancia_h', 'accion_salto'),
    ('datos_bala_vertical.csv', 'velocidad_bala_v', 'distancia_v', 'accion_retroceso')
]

def limpiar_archivo(nombre_archivo, col_vel, col_dist, col_accion):
    if not os.path.exists(nombre_archivo):
        print(f"Archivo no encontrado: {nombre_archivo}")
        return

    print(f"\n--- LIMPIANDO {nombre_archivo} ---")
    df = pd.read_csv(nombre_archivo)
    print(f"Filas originales: {len(df)}")

    # Mostrar balance de clases antes
    print("Distribución de acciones antes de limpiar:")
    print(df[col_accion].value_counts())

    # Eliminar duplicados exactos
    df = df.drop_duplicates()

    # Eliminar outliers suaves
    df = df[(df[col_vel].between(df[col_vel].quantile(0.01), df[col_vel].quantile(0.99))) &
            (df[col_dist].between(df[col_dist].quantile(0.01), df[col_dist].quantile(0.99)))]

    print(f"Filas después de limpieza: {len(df)}")
    print("Distribución de acciones después de limpiar:")
    print(df[col_accion].value_counts())

    # Guardar como nuevo archivo limpio
    limpio = nombre_archivo.replace('.csv', '_limpio.csv')
    df.to_csv(limpio, index=False)
    print(f"Guardado archivo limpio en: {limpio}\n")

for archivo, vel, dist, acc in archivos:
    limpiar_archivo(archivo, vel, dist, acc)
