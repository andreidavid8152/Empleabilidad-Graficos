import streamlit as st
import pandas as pd
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly
from utils.filtros import aplicar_filtros

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
df_fil, _ = aplicar_filtros(df)

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
