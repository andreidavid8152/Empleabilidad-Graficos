import streamlit as st
import pandas as pd
import plotly.express as px
from dateutil.relativedelta import relativedelta
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly

aplicar_tema_plotly()
st.title("⏳ Duración de Empleos de Graduados")

# Carga inicial
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# Preprocesamiento
df_base['FECINGAFI.1'] = pd.to_datetime(df_base['FECINGAFI.1'], errors='coerce')
df_base['Empleo formal'] = df_base['Empleo formal'].astype(str).str.strip().str.upper()
df_base = df_base.dropna(subset=['FECINGAFI.1', 'IdentificacionBanner.1', 'NOMEMP.1'])

df_ordenado = df_base.sort_values(['IdentificacionBanner.1', 'NOMEMP.1', 'FECINGAFI.1'])
empleos = []

for _, grupo in df_ordenado.groupby(['IdentificacionBanner.1', 'NOMEMP.1']):
    fechas = grupo['FECINGAFI.1'].tolist()
    for i in range(len(fechas) - 1):
        inicio, fin = fechas[i], fechas[i + 1]
        delta = relativedelta(fin, inicio)
        duracion_meses = delta.years * 12 + delta.months
        if duracion_meses > 0:
            fila = grupo.iloc[i].to_dict()
            fila['DuracionMeses'] = duracion_meses
            empleos.append(fila)

df = pd.DataFrame(empleos)

# ---------------------------------
# FILTROS INTERDEPENDIENTES
# ---------------------------------
nivel_sel = st.selectbox("Nivel", ["Todos"] + sorted(df['regimen.1'].dropna().unique()))
df_fil = df if nivel_sel == "Todos" else df[df['regimen.1'] == nivel_sel]

oferta_sel = st.selectbox("Oferta Actual", ["Todos"] + sorted(df_fil['Oferta actual'].dropna().unique()))
df_fil = df_fil if oferta_sel == "Todos" else df_fil[df_fil['Oferta actual'] == oferta_sel]

facultad_sel = st.selectbox("Facultad", ["Todas"] + sorted(df_fil['FACULTAD'].dropna().unique()))
df_fil = df_fil if facultad_sel == "Todas" else df_fil[df_fil['FACULTAD'] == facultad_sel]

carrera_sel = st.selectbox("Carrera", ["Todas"] + sorted(df_fil['CarreraHomologada.1'].dropna().unique()))
df_fil = df_fil if carrera_sel == "Todas" else df_fil[df_fil['CarreraHomologada.1'] == carrera_sel]

cohorte_sel = st.selectbox("Cohorte", ["Todos"] + sorted(df_fil['AnioGraduacion.1'].dropna().unique()))
df_fil = df_fil if cohorte_sel == "Todos" else df_fil[df_fil['AnioGraduacion.1'] == cohorte_sel]

formal_sel = st.selectbox("Trabajo Formal", ["Todos"] + sorted(df_fil['Empleo formal'].dropna().unique()))
df_fil = df_fil if formal_sel == "Todos" else df_fil[df_fil['Empleo formal'] == formal_sel]

# ---------------------------------
# Tipo de gráfico
# ---------------------------------
tipo_grafico = st.radio("Tipo de gráfico", ['Histograma', 'Boxplot por carrera'])

# ---------------------------------
# Visualización
# ---------------------------------
if df_fil.empty:
    st.warning("No hay datos para esta combinación de filtros.")
else:
    if tipo_grafico == 'Histograma':
        fig = px.histogram(
            df_fil,
            x='DuracionMeses',
            nbins=20,
            title='Distribución de duración de empleos',
            labels={'DuracionMeses': 'Meses'}
        )
        fig.update_layout(yaxis_title='Cantidad de empleos')
    else:
        fig = px.box(
            df_fil,
            x='CarreraHomologada.1',
            y='DuracionMeses',
            points='all',
            title='Duración de empleo por carrera',
            labels={'DuracionMeses': 'Meses'}
        )
        fig.update_layout(xaxis_tickangle=-45)

    st.plotly_chart(fig, use_container_width=True)
