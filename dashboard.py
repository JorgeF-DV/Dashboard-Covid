import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json

# --- 1. CONFIGURACIÓN DE LA PÁGINA ---
st.set_page_config(
    page_title="Dashboard COVID-19 Colombia",
    page_icon="🦠",
    layout="wide"
)

# --- FUNCIÓN DE CARGA Y TRANSFORMACIÓN DE DATOS (FASE 1) ---
@st.cache_data
def load_data(file_path):
    """
    Carga, limpia y transforma los datos del CSV.
    También descarga el archivo GeoJSON para el mapa.
    """
    try:
        df = pd.read_csv(file_path, compression='zip') # Leemos el ZIP
    except FileNotFoundError:
        st.error(f"Error: No se encontró el archivo en {file_path}.")
        return None, None, None
    except Exception as e:
        st.error(f"Error al cargar el archivo: {e}")
        return None, None, None

    # Normalizar nombres de columnas
    nuevas_columnas = df.columns.str.lower().str.replace(' ', '_', regex=False).str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
    df.columns = nuevas_columnas
    
    # Transformación de Fechas y Edades
    date_cols = [col for col in df.columns if 'fecha' in col]
    for col in date_cols:
        df[col] = pd.to_datetime(df[col], errors='coerce')
    df['edad'] = pd.to_numeric(df['edad'], errors='coerce')
    
    bins = [0, 18, 30, 50, 70, 110]
    labels = ['0-17', '18-29', '30-49', '50-69', '70+']
    df['grupo_edad'] = pd.cut(df['edad'], bins=bins, labels=labels, right=False)
    
    # --- PREPARACIÓN PARA EL MAPA ---
    df['departamento_mapa'] = df['nombre_departamento'].str.upper()
    df['departamento_mapa'] = df['departamento_mapa'].str.normalize('NFKD').str.encode('ascii', errors='ignore').str.decode('utf-8')
    
    replacements = {
        'BOGOTA D.C.': 'BOGOTA',
        'CARTAGENA D.T. Y C.': 'BOLIVAR', 
        'BARRANQUILLA D.E. Y P.': 'ATLANTICO',
        'SANTA MARTA D.T. Y C.H.': 'MAGDALENA',
        'BUENAVENTURA D.E.': 'VALLE DEL CAUCA',
        'VALLE DEL CAUCA': 'VALLE',
        'SAN ANDRES Y PROVIDENCIA': 'ARCHIPIELAGO DE SAN ANDRES PROVIDENCIA Y SANTA CATALINA',
        'N. DE SANTANDER': 'NORTE DE SANTANDER',
        'STA MARTA D.T.C.H': 'MAGDALENA'
    }
    df['departamento_mapa'] = df['departamento_mapa'].replace(replacements)
    
    # Cargar GeoJSON
    try:
        url = "https://gist.githubusercontent.com/john-guerra/43c7656821069d00dcbc/raw/3aadedf47badbdac823b00dbe259f6bc6d9e1899/colombia.geo.json"
        response = requests.get(url)
        colombia_geojson = response.json()
    except Exception as e:
        st.error(f"Error al cargar el mapa GeoJSON: {e}")
        return df, None, labels
        
    return df, colombia_geojson, labels

# --- CARGA DE DATOS ---
file_path = 'casos_covid_colombia_PROCESADO.zip'
df, colombia_geojson, labels_edad = load_data(file_path)

if df is None:
    st.stop()

# --- FASE 3: FILTROS INTERACTIVOS (CON BOTÓN) ---
st.sidebar.header("Filtros Interactivos")

# --- *** INICIO DEL CAMBIO *** ---
# TODOS los inputs van DENTRO del formulario
with st.sidebar.form(key='filtro_form'):
    min_fecha = df['fecha_de_diagnostico'].min().date()
    max_fecha = df['fecha_de_diagnostico'].max().date()
    fecha_inicio, fecha_fin = st.date_input(
        "Selecciona el rango de fechas:",
        [min_fecha, max_fecha],
        min_value=min_fecha,
        max_value=max_fecha
    )
    departamentos = sorted(df['nombre_departamento'].unique())
    deptos_seleccionados = st.multiselect(
        "Selecciona Departamentos:",
        departamentos,
        default=departamentos
    )
    edades_seleccionadas = st.multiselect(
        "Selecciona Grupos de Edad:",
        labels_edad,
        default=labels_edad
    )
    
    st.sidebar.subheader("Opciones de Depuración")
    check_nombres_mapa = st.checkbox("Mostrar nombres de departamentos")
    check_datos_crudos = st.checkbox("Mostrar datos crudos filtrados")
    
    # --- EL BOTÓN PARA APLICAR FILTROS ---
    submit_button = st.form_submit_button(label='Aplicar Filtros 🚀')

# --- *** FIN DEL CAMBIO *** ---


# --- APLICAR FILTROS AL DATAFRAME ---
# Este código ahora solo se ejecuta con los valores del formulario
fecha_inicio = pd.to_datetime(fecha_inicio)
fecha_fin = pd.to_datetime(fecha_fin)
df_filtrado = df[
    (df['fecha_de_diagnostico'] >= fecha_inicio) &
    (df['fecha_de_diagnostico'] <= fecha_fin) &
    (df['nombre_departamento'].isin(deptos_seleccionados)) &
    (df['grupo_edad'].isin(edades_seleccionadas))
]

# --- HERRAMIENTAS DE DEBUG EN SIDEBAR ---
# Esto ahora usa los valores 'check_nombres_mapa' y 'check_datos_crudos'
# que se capturaron DENTRO del formulario
st.sidebar.subheader("Ayuda para el Mapa (Debug)")
if check_nombres_mapa:
    st.sidebar.write("**Nombres en tu CSV (normalizados):**")
    st.sidebar.dataframe(sorted(df['departamento_mapa'].unique()))
    if colombia_geojson:
        st.sidebar.write("**Nombres en el archivo del Mapa (GeoJSON):**")
        nombres_mapa = sorted([feature['properties']['NOMBRE_DPT'] for feature in colombia_geojson['features']])
        st.sidebar.dataframe(nombres_mapa)
    st.sidebar.info("Compara las listas. Si un nombre no coincide, añádelo al diccionario 'replacements'.")

if check_datos_crudos:
    st.sidebar.header("Datos Filtrados") 
    st.sidebar.dataframe(df_filtrado.head(50))


# --- FASE 2: CREACIÓN DEL DASHBOARD ---
st.title("Dashboard de Análisis COVID-19 en Colombia 🇨🇴")
st.write(f"Mostrando datos desde {fecha_inicio.date()} hasta {fecha_fin.date()}")

# 2.4 Indicadores Clave (KPI)
st.header("Indicadores Clave (KPIs)")

total_confirmados = len(df_filtrado)
total_fallecidos = len(df_filtrado[df_filtrado['estado'] == 'Fallecido'])
total_recuperados = len(df_filtrado[df_filtrado['recuperado'] == 'Recuperado'])
total_activos = len(df_filtrado[df_filtrado['recuperado'] == 'Activo']) 

if total_confirmados > 0:
    tasa_letalidad = (total_fallecidos / total_confirmados) * 100
else:
    tasa_letalidad = 0

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Confirmados", f"{total_confirmados:,}")
col2.metric("Total Fallecidos", f"{total_fallecidos:,}")
col3.metric("Total Recuperados", f"{total_recuperados:,}")
col4.metric("Tasa de Letalidad", f"{tasa_letalidad:.2f}%")

st.write("---")

# Verificamos si el DataFrame filtrado está vacío
if df_filtrado.empty:
    st.warning("No se encontraron datos para los filtros seleccionados. Por favor, amplía tu búsqueda.")
else:
    # Si hay datos, dibujamos todos los gráficos
    col_izq, col_der = st.columns((7, 3))

    with col_izq:
        # 2.1 Gráfico de Evolución Temporal
        st.subheader("Evolución Temporal de Casos")
        df_tiempo = df_filtrado.groupby(pd.Grouper(key='fecha_de_diagnostico', freq='D')).agg(
            Confirmados=('id_de_caso', 'count'),
            Fallecidos=('estado', lambda x: (x == 'Fallecido').sum()),
            Recuperados=('recuperado', lambda x: (x == 'Recuperado').sum())
        ).reset_index()
        
        df_evolucion_melted = df_tiempo.melt(
            id_vars='fecha_de_diagnostico', 
            var_name='Tipo de Caso', 
            value_name='Número de Casos'
        )
        
        fig_lineas = px.line(df_evolucion_melted, 
                             x='fecha_de_diagnostico', 
                             y='Número de Casos', 
                             color='Tipo de Caso',
                             title='Casos Confirmados, Fallecidos y Recuperados por Día')
        st.plotly_chart(fig_lineas, use_container_width=True)

        # 2.2 Mapa Coroplético
        st.subheader("Mapa de Casos por Departamento")
        if colombia_geojson:
            df_departamentos = df_filtrado.groupby(['departamento_mapa', 'nombre_departamento']).size().reset_index(name='Casos')
            
            fig_mapa = px.choropleth(df_departamentos,
                                     geojson=colombia_geojson,
                                     locations='departamento_mapa',
                                     featureidkey='properties.NOMBRE_DPT',
                                     color='Casos',
                                     hover_name='nombre_departamento',
                                     color_continuous_scale="Reds", 
                                     title='Casos Totales por Departamento')
            
            fig_mapa.update_geos(
                center={"lat": 4.57, "lon": -74.29},
                lataxis_range=[-4.5, 13.0],
                lonaxis_range=[-80.0, -66.5],
                visible=False
            )
            st.plotly_chart(fig_mapa, use_container_width=True)
        else:
            st.warning("No se pudo cargar el mapa (GeoJSON no disponible).")

    with col_der:
        # 2.3 Gráfico de Barras - Departamentos más Afectados
        st.subheader("Top 10 Departamentos Afectados")
        df_top_deptos = df_filtrado.groupby('nombre_departamento').size().nlargest(10).reset_index(name='Casos')
        
        fig_barras_deptos = px.bar(df_top_deptos.sort_values(by='Casos', ascending=True),
                                   x='Casos',
                                   y='nombre_departamento',
                                   orientation='h',
                                   title='Top 10 Departamentos con más casos')
        st.plotly_chart(fig_barras_deptos, use_container_width=True)

    # --- 2.5 Criterio Propio (Dos gráficos más) ---
    st.write("---")
    st.header("Análisis Adicionales (Criterio Propio)")

    col_extra1, col_extra2 = st.columns(2)

    with col_extra1:
        st.subheader("Distribución de Casos por Edad y Sexo")
        df_edad_sexo = df_filtrado.groupby(['grupo_edad', 'sexo']).size().reset_index(name='Casos')
        
        fig_edad_sexo = px.bar(df_edad_sexo,
                               x='grupo_edad',
                               y='Casos',
                               color='sexo',
                               barmode='group',
                               title='Casos por Grupo de Edad y Sexo')
        st.plotly_chart(fig_edad_sexo, use_container_width=True)

    with col_extra2:
        st.subheader("Distribución por Tipo de Contagio")
        df_contagio = df_filtrado['tipo_de_contagio'].value_counts().reset_index()
        df_contagio.columns = ['Tipo de Contagio', 'Casos']
        
        fig_contagio = px.pie(df_contagio,
                              names='Tipo de Contagio',
                              values='Casos',
                              title='Fuentes de Contagio más comunes',
                              hole=0.3)
        st.plotly_chart(fig_contagio, use_container_width=True)