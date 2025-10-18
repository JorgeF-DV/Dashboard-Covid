import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Prueba de Carga de Datos (Debug) 🐞")

# --- Variables clave ---
file_path = 'casos_covid_colombia_PROCESADO.zip'
df = None

# --- Intentamos cargar el archivo ---
try:
    st.write(f"Intentando cargar el archivo: `{file_path}`...")
    
    # 1. Intentamos leer el archivo ZIP
    df = pd.read_csv(file_path, compression='zip')
    
    # 2. Si tiene éxito, lo mostramos
    st.success("✅ ¡Éxito! El archivo ZIP fue cargado y leído correctamente.")
    st.write("Primeras 5 filas de los datos:")
    st.dataframe(df.head())

except Exception as e:
    # 3. Si falla, mostramos el error EXACTO de Python
    st.error(f"❌ ¡ERROR AL CARGAR EL ARCHIVO!")
    st.write("El script de Python colapsó con el siguiente error:")
    st.exception(e)

st.write("--- Fin de la prueba ---")