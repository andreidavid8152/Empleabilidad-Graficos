import streamlit as st
import pandas as pd
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
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
# FILTROS
# --------------------------
df_fil, selecciones = aplicar_filtros(df, incluir=["Nivel", "Oferta Actual", "Facultad", "Carrera", "Cohorte", "Trabajo Formal"])

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

# --------------------------
# NOTA
# --------------------------
mostrar_tarjeta_nota(
    texto_principal="""
    <strong>📌 Nota:</strong><br>
    Esta visualización muestra la clasificación y frecuencia de los puestos ocupados por los graduados.
    """,
    nombre_filtro="Trabajo Formal",
    descripcion_filtro="""
    <strong>Relación de Dependencia: </strong>Graduados contratados formalmente por un empleador.<br>
    <strong>Afiliado Voluntario: </strong>Personas que se autoafiliaron al IESS. Esto puede incluir emprendedores, profesionales independientes, o personas con ingresos propios no derivados de relación laboral.<br>
    <strong>Desconocido: </strong>Graduados sin información laboral registrada. Esto incluye personas sin empleo formal, inactivas, trabajando fuera del país, o en sectores no registrados en la seguridad social.<br>
    """,
)
