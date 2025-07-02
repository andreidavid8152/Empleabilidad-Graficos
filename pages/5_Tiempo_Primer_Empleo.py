import streamlit as st
import pandas as pd
import plotly.express as px
from dateutil.relativedelta import relativedelta
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

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
# FILTROS
# --------------------------
df_fil, selecciones = aplicar_filtros(df, incluir=["Nivel", "Oferta Actual", "Facultad", "Carrera", "Cohorte", "Trabajo Formal"])

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

# --------------------------
# NOTA
# --------------------------
mostrar_tarjeta_nota(
    texto_principal="""
    <strong>📌 Nota:</strong><br>
    Esta visualización muestran los meses promedio desde la graduación hasta el primer registro laboral formal. (Solo 2024 por ahora).
    """,
    nombre_filtro="Trabajo Formal",
    descripcion_filtro="""
    <strong>Relación de Dependencia: </strong>Graduados contratados formalmente por un empleador.<br>
    <strong>Afiliado Voluntario: </strong>Personas que se autoafiliaron al IESS. Esto puede incluir emprendedores, profesionales independientes, o personas con ingresos propios no derivados de relación laboral.<br>
    <strong>Desconocido: </strong>Graduados sin información laboral registrada. Esto incluye personas sin empleo formal, inactivas, trabajando fuera del país, o en sectores no registrados en la seguridad social.<br>
    """,
)
