import streamlit as st
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly
from utils.filtros import aplicar_filtros

aplicar_tema_plotly()
st.title("Distribución de Salarios por Periodo")

# 🌀 Cargar datos sin procesar
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# Procesamiento específico
df = df_base.copy()
df = df[df['SALARIO.1'].notnull()]
def asignar_quimestre(mes):
    return {2: 'Q1', 5: 'Q2', 9: 'Q3', 11: 'Q4'}.get(mes, None)

df['Quimestre'] = df['Mes.1'].apply(asignar_quimestre)
df = df[df['Quimestre'].notnull()]
df['Periodo'] = df['Anio.1'].astype(str) + ' ' + df['Quimestre']

# --------------------------
# FILTROS INTERDEPENDIENTES
# --------------------------
df_fil, _ = aplicar_filtros(df)

# --------------------------
# BOXPLOT Y RESUMEN
# --------------------------
if df_fil.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
else:
    fig = px.box(
        df_fil,
        x='Periodo',
        y='SALARIO.1',
        title='Distribución de Salarios por Periodo',
        labels={'SALARIO.1': 'Salario', 'Periodo': 'Año-Quimestre'},
        points='outliers'
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    resumen = df_fil['SALARIO.1'].describe()
    st.subheader("Resumen estadístico del salario")
    st.markdown(f"""
    - **Media:** ${resumen['mean']:.2f}  
    - **Mediana:** ${df_fil['SALARIO.1'].median():.2f}  
    - **Desviación estándar:** ${resumen['std']:.2f}  
    - **Q1 (percentil 25):** ${resumen['25%']:.2f}  
    - **Q3 (percentil 75):** ${resumen['75%']:.2f}  
    - **Máximo:** ${resumen['max']:.2f}  
    - **Mínimo:** ${resumen['min']:.2f}  
    - **Número de observaciones:** {int(resumen['count'])}
    """)
