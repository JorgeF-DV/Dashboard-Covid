import pandas as pd

print("Iniciando la creación de la muestra...")

try:
    # 1. Lee el archivo ZIP grande
    df_grande = pd.read_csv('casos_covid_colombia_PROCESADO.zip', compression='zip')

    # 2. Toma una muestra aleatoria de 100,000 filas
    df_muestra = df_grande.sample(n=100000)

    # 3. Guarda la muestra en un NUEVO archivo CSV (este será pequeño)
    df_muestra.to_csv('datos_muestra.csv', index=False)

    print("✅ ¡Éxito! Se ha creado el archivo 'datos_muestra.csv' con 100,000 registros.")

except Exception as e:
    print(f"❌ Error al crear la muestra: {e}")