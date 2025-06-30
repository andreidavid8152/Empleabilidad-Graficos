import streamlit as st
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly
from utils.filtros import aplicar_filtros

aplicar_tema_plotly()
st.title("Tasa de Ocupacion por Quimestre")

# 🌀 Cargar datos sin procesar
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# Procesamiento específico de esta página
df = df_base.copy()

def asignar_quimestre(mes):
    return {2: 'Q1', 5: 'Q2', 9: 'Q3', 11: 'Q4'}.get(mes, None)

df['Quimestre'] = df['Mes.1'].apply(asignar_quimestre)
df['Esta_empleado'] = df['SALARIO.1'].notnull() | df['RUCEMP.1'].notnull()
df = df[df['Quimestre'].notnull()]
df['Periodo'] = df['Anio.1'].astype(str) + ' ' + df['Quimestre']

# --------------------------
# FILTROS
# --------------------------
df_fil, _ = aplicar_filtros(df)

# --------------------------
# AGRUPACIÓN Y GRÁFICO
# --------------------------
if df_fil.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
else:
    resumen = df_fil.groupby(['Periodo']).agg(
        empleados=('Esta_empleado', 'sum'),
        total=('IdentificacionBanner.1', 'nunique')
    ).reset_index()

    resumen['tasa_empleabilidad'] = resumen['empleados'] / resumen['total']

    fig = px.line(
        resumen,
        x='Periodo',
        y='tasa_empleabilidad',
        title='Tasa de Empleabilidad',
        markers=True,
        labels={'tasa_empleabilidad': 'Tasa de empleo'}
    )
    fig.update_layout(xaxis_tickangle=-45)

    st.plotly_chart(fig, use_container_width=True)
