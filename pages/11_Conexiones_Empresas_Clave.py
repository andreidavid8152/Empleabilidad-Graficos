import streamlit as st
import pandas as pd
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly

aplicar_tema_plotly()
st.title("🏢 Conexiones con Empresas Clave")

# 🌀 Cargar datos
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# Preprocesamiento
df = df_base.copy()
df['Empleo formal'] = df['Empleo formal'].astype(str).str.strip().str.upper()
df['NOMEMP.1'] = df['NOMEMP.1'].fillna('SIN EMPRESA')
df['Cantidad de empleados'] = pd.to_numeric(df['Cantidad de empleados'], errors='coerce')
df['Cantidad de empleados'] = df['Cantidad de empleados'].fillna(0)

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
# FILTROS ADICIONALES
# --------------------------
sector_sel = st.selectbox(
    "Sector Económico",
    ["Todos"] + sorted(df_fil['SECTOR'].dropna().unique())
)
df_fil = df_fil if sector_sel == "Todos" else df_fil[df_fil['SECTOR'] == sector_sel]

tam_min = int(df_fil['Cantidad de empleados'].min())
tam_max = int(df_fil['Cantidad de empleados'].max())
tamano_rango = st.slider(
    "Tamaño de empresa (Cantidad de empleados)",
    min_value=tam_min, max_value=tam_max,
    value=(tam_min, tam_max), step=1
)
df_fil = df_fil[
    (df_fil['Cantidad de empleados'] >= tamano_rango[0]) &
    (df_fil['Cantidad de empleados'] <= tamano_rango[1])
]

# --------------------------
# GRÁFICO DE EMPRESAS
# --------------------------
top_empresas = df_fil['NOMEMP.1'].value_counts().nlargest(10).reset_index()
top_empresas.columns = ['Empresa', 'Contrataciones']

if top_empresas.empty:
    st.warning("No hay datos disponibles para esta combinación de filtros.")
else:
    fig = px.bar(
        top_empresas,
        x='Empresa',
        y='Contrataciones',
        text='Contrataciones',
        title='Top 10 empresas que contratan graduados'
    )
    fig.update_layout(yaxis_title='Número de graduados contratados')
    st.plotly_chart(fig, use_container_width=True)
