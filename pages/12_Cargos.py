import streamlit as st
import pandas as pd
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly

aplicar_tema_plotly()
st.title("🏆 Ranking de Cargos Ocupados por Graduados")

# 🌀 Cargar datos
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# Limpieza
df = df_base.copy()
df['Empleo formal'] = df['Empleo formal'].astype(str).str.strip().str.upper()
df['SALARIO.1'] = pd.to_numeric(df['SALARIO.1'], errors='coerce')
df['OCUAFI.1'] = df['OCUAFI.1'].fillna('SIN INFORMACIÓN')

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
df_fil = df_fil if formal_sel == "Todos" else df_fil[df_fil['Empleo formal'] == formal_sel]

# --------------------------
# GRÁFICO
# --------------------------
resumen = df_fil.groupby('OCUAFI.1').agg(
    Total=('OCUAFI.1', 'count'),
    SalarioPromedio=('SALARIO.1', 'mean')
).sort_values('Total', ascending=False).reset_index().head(15)

if resumen.empty:
    st.warning("No hay datos disponibles para esta combinación de filtros.")
else:
    fig = px.bar(
        resumen,
        x='OCUAFI.1',
        y='Total',
        text='Total',
        hover_data={'SalarioPromedio': ':.2f'},
        title='Top 15 cargos ocupados por graduados'
    )
    fig.update_layout(
        xaxis_title='Cargo',
        yaxis_title='Número de graduados',
        xaxis_tickangle=-45
    )
    st.plotly_chart(fig, use_container_width=True)
