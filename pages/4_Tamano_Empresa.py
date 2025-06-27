import streamlit as st
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly

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
nivel_sel = st.selectbox("Nivel", ["Todos"] + sorted(df['regimen.1'].dropna().unique()))
df_fil = df if nivel_sel == "Todos" else df[df['regimen.1'] == nivel_sel]

oferta_sel = st.selectbox("Oferta Actual", ["Todos"] + sorted(df_fil['Oferta actual'].dropna().unique()))
df_fil = df_fil if oferta_sel == "Todos" else df_fil[df_fil['Oferta actual'] == oferta_sel]

facultad_sel = st.selectbox("Facultad", ["Todas"] + sorted(df_fil['FACULTAD'].dropna().unique()))
df_fil = df_fil if facultad_sel == "Todas" else df_fil[df_fil['FACULTAD'] == facultad_sel]

carrera_sel = st.selectbox("Carrera", ["Todas"] + sorted(df_fil['CarreraHomologada.1'].dropna().unique()))
df_fil = df_fil if carrera_sel == "Todas" else df_fil[df_fil['CarreraHomologada.1'] == carrera_sel]

cohorte_sel = st.selectbox("Cohorte (Año Graduación)", ["Todos"] + sorted(df_fil['AnioGraduacion.1'].dropna().unique()))
df_fil = df_fil if cohorte_sel == "Todos" else df_fil[df_fil['AnioGraduacion.1'] == cohorte_sel]

formal_sel = st.selectbox("Trabajo Formal", ["Todos"] + sorted(df_fil['Empleo formal'].dropna().astype(str).unique()))
df_fil = df_fil if formal_sel == "Todos" else df_fil[df_fil['Empleo formal'].astype(str) == formal_sel]

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
