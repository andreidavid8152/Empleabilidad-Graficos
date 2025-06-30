import streamlit as st
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly
from utils.filtros import aplicar_filtros

aplicar_tema_plotly()
st.title("Ranking de Carreras por Empleabilidad")

# 🌀 Cargar datos sin procesar
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# Procesamiento específico
df = df_base.copy()
df['Esta_empleado'] = df['SALARIO.1'].notnull() | df['RUCEMP.1'].notnull()

def asignar_quimestre(mes):
    return {2: 'Q1', 5: 'Q2', 9: 'Q3', 11: 'Q4'}.get(mes, None)

df['Quimestre'] = df['Mes.1'].apply(asignar_quimestre)
df = df[df['Quimestre'].notnull()]
df['Periodo'] = df['Anio.1'].astype(str) + ' ' + df['Quimestre']

# --------------------------
# FILTROS INTERDEPENDIENTES
# --------------------------
df_fil, _ = aplicar_filtros(df)

periodos = sorted(df_fil['Periodo'].dropna().unique())
periodo_sel = st.selectbox("Filtrar por Periodo", ["Todos"] + periodos)
df_fil = df_fil if periodo_sel == "Todos" else df_fil[df_fil['Periodo'] == periodo_sel]

# --------------------------
# CÁLCULO DE RANKING PROMEDIADO POR QUIMESTRE
# --------------------------
if df_fil.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
else:
    # Paso 1: Tasa por carrera y quimestre
    resumen = df_fil.groupby(['CarreraHomologada.1', 'Periodo']).agg(
        empleados=('Esta_empleado', 'sum'),
        total=('IdentificacionBanner.1', 'nunique')
    ).reset_index()

    resumen = resumen[resumen['total'] > 0]  # Evitar división por cero
    resumen['TasaQuimestral'] = resumen['empleados'] / resumen['total']

    # Paso 2: Promedio de tasas quimestrales por carrera
    ranking = resumen.groupby('CarreraHomologada.1')['TasaQuimestral'].mean().reset_index()
    ranking = ranking.sort_values('TasaQuimestral', ascending=False)

    # Paso 3: Gráfico
    fig = px.bar(
        ranking,
        x='CarreraHomologada.1',
        y='TasaQuimestral',
        title='Ranking de Carreras por Empleabilidad',
        labels={'CarreraHomologada.1': 'Carrera', 'TasaQuimestral': 'Tasa promedio'},
        color='TasaQuimestral'
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
