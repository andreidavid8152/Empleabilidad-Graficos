import streamlit as st
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly
from utils.filtros import aplicar_filtros

aplicar_tema_plotly()
st.title("Distribución de Graduados por Tamaño de Empresa")

# 🌀 Cargar datos sin procesar
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# Procesamiento específico
df = df_base.copy()
df['Esta_empleado'] = df['SALARIO.1'].notnull() | df['RUCEMP.1'].notnull()
df = df[df['Esta_empleado'] & df['Cantidad de empleados'].notnull()]

def clasificar_tamano(n):
    if n <= 10:
        return 'Microempresa (1–10)'
    elif n <= 50:
        return 'Pequeña (11–50)'
    elif n <= 200:
        return 'Mediana (51–200)'
    else:
        return 'Grande (200+)'

df['Tamaño Empresa'] = df['Cantidad de empleados'].apply(clasificar_tamano)

# --------------------------
# FILTROS INTERDEPENDIENTES
# --------------------------
df_fil, _ = aplicar_filtros(df)

# --------------------------
# GRÁFICO
# --------------------------
if df_fil.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
else:
    conteo_tamano = df_fil['Tamaño Empresa'].value_counts().reindex([
        'Microempresa (1–10)',
        'Pequeña (11–50)',
        'Mediana (51–200)',
        'Grande (200+)'
    ]).reset_index()
    conteo_tamano.columns = ['Tamaño Empresa', 'Número de Graduados']
    conteo_tamano = conteo_tamano.dropna()

    fig = px.bar(
        conteo_tamano,
        x='Tamaño Empresa',
        y='Número de Graduados',
        title='Distribución de Graduados por Tamaño de Empresa',
        labels={'Tamaño Empresa': 'Tamaño de empresa'},
        color='Tamaño Empresa'
    )
    fig.update_layout(
        xaxis={'categoryorder': 'array',
               'categoryarray': ['Microempresa (1–10)', 'Pequeña (11–50)', 'Mediana (51–200)', 'Grande (200+)']}
    )
    st.plotly_chart(fig, use_container_width=True)
