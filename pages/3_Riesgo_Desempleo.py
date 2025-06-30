import streamlit as st
import pandas as pd
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly
from utils.filtros import aplicar_filtros

aplicar_tema_plotly()
st.title("📉 Riesgo de Desempleo por Cohorte")

# 🌀 Cargar datos
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# Preprocesamiento
df = df_base.copy()
df['Esta_empleado'] = df['SALARIO.1'].notnull() | df['RUCEMP.1'].notnull()

# --------------------------
# FILTROS INTERDEPENDIENTES
# --------------------------
df_fil, selecciones = aplicar_filtros(df, incluir=["Nivel", "Oferta Actual", "Facultad", "Carrera", "Cohorte"])

formal_check = st.checkbox("¿Solo empleo formal?", value=False)
tipo_grafico = st.radio("Tipo de gráfico", options=["Líneas", "Barras"], horizontal=True)

# --------------------------
# CÁLCULO DE DESEMPLEO
# --------------------------
if df_fil.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
else:
    total = df_fil.groupby('AnioGraduacion.1')['IdentificacionBanner.1'].nunique()

    if formal_check:
        empleados_df = df_fil[df_fil['Empleo formal'].astype(str).str.upper() == 'EMPLEO FORMAL']
    else:
        empleados_df = df_fil[df_fil['Esta_empleado']]

    empleados = empleados_df.groupby('AnioGraduacion.1')['IdentificacionBanner.1'].nunique()

    resumen = pd.DataFrame({'empleados': empleados, 'total': total}).reset_index()
    resumen = resumen[resumen['total'] > 0]
    resumen['desempleo'] = 1 - (resumen['empleados'] / resumen['total'])
    resumen = resumen.sort_values('AnioGraduacion.1')

    titulo = f'Tasa de desempleo por cohorte{" (solo empleo formal)" if formal_check else ""}'

    if tipo_grafico == 'Barras':
        fig = px.bar(
            resumen,
            x='AnioGraduacion.1',
            y='desempleo',
            labels={'AnioGraduacion.1': 'Año de graduación', 'desempleo': 'Tasa de desempleo'},
            title=titulo,
            text_auto='.1%'
        )
    else:
        fig = px.line(
            resumen,
            x='AnioGraduacion.1',
            y='desempleo',
            labels={'AnioGraduacion.1': 'Año de graduación', 'desempleo': 'Tasa de desempleo'},
            title=titulo,
            markers=True
        )
        fig.update_traces(mode='lines+markers')
        fig.update_yaxes(tickformat=".0%")

    st.plotly_chart(fig, use_container_width=True)
