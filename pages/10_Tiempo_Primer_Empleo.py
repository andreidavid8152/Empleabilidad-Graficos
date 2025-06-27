import streamlit as st
import pandas as pd
import plotly.express as px
from dateutil.relativedelta import relativedelta
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly

aplicar_tema_plotly()
st.title("⏱️ Tiempo al Primer Empleo desde la Graduación")

# 🌀 Cargar datos
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# Preprocesamiento específico
df = df_base.copy()
df['FechaGraduacion.1'] = pd.to_datetime(df['FechaGraduacion.1'], errors='coerce')
df['FECINGAFI.1'] = pd.to_datetime(df['FECINGAFI.1'], errors='coerce')

# Eliminar registros sin fechas o con ingreso antes de graduación
df = df.dropna(subset=['FechaGraduacion.1', 'FECINGAFI.1'])
df = df[df['FECINGAFI.1'] >= df['FechaGraduacion.1']]

# Calcular meses al primer empleo
def calcular_meses(graduacion, ingreso):
    delta = relativedelta(ingreso, graduacion)
    return delta.years * 12 + delta.months

df['Meses al primer empleo'] = df.apply(
    lambda row: calcular_meses(row['FechaGraduacion.1'], row['FECINGAFI.1']),
    axis=1
)

# Conservar solo el primer empleo por persona
df = df.sort_values(['IdentificacionBanner.1', 'FECINGAFI.1'])
df = df.drop_duplicates(subset='IdentificacionBanner.1', keep='first')

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
# GRÁFICO DE HISTOGRAMA
# --------------------------
if df_fil.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
else:
    fig = px.histogram(
        df_fil,
        x='Meses al primer empleo',
        nbins=20,
        title='Distribución del Tiempo al Primer Empleo',
        labels={'Meses al primer empleo': 'Meses desde graduación'}
    )
    fig.update_layout(yaxis_title='Número de graduados', xaxis_title='Meses desde graduación')
    st.plotly_chart(fig, use_container_width=True)
