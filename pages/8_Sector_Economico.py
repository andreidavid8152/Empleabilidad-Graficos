import streamlit as st
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

aplicar_tema_plotly()
st.title("Distribución de Graduados por Sector Económico")

# 🌀 Cargar datos sin procesar
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# Procesamiento específico
df = df_base.copy()
df['Esta_empleado'] = df['SALARIO.1'].notnull() | df['RUCEMP.1'].notnull()
df = df[df['Esta_empleado'] & df['SECTOR'].notnull()]

# --------------------------
# FILTROS INTERDEPENDIENTES
# --------------------------
df_fil, _ = aplicar_filtros(df)

# --------------------------
# GRÁFICO POR SECTOR
# --------------------------
if df_fil.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
else:
    conteo_sector = df_fil['SECTOR'].value_counts().reset_index()
    conteo_sector.columns = ['Sector Económico', 'Número de Graduados']

    fig = px.bar(
        conteo_sector,
        x='Número de Graduados',
        y='Sector Económico',
        orientation='h',
        title='Distribución por Sector Económico',
        labels={'Número de Graduados': 'Cantidad'}
    )
    fig.update_layout(yaxis={'categoryorder': 'total ascending'})
    st.plotly_chart(fig, use_container_width=True)

# --------------------------
# NOTA
# --------------------------
mostrar_tarjeta_nota(
    texto_principal="""
    <strong>📌 Nota:</strong><br>
    Esta visualización muestra la clasificación del empleo según la actividad económica de la empresa (CIIU Rev.4).
    """,
    nombre_filtro="Trabajo Formal",
    descripcion_filtro="""
    <strong>Relación de Dependencia: </strong>Graduados contratados formalmente por un empleador.<br>
    <strong>Afiliado Voluntario: </strong>Personas que se autoafiliaron al IESS. Esto puede incluir emprendedores, profesionales independientes, o personas con ingresos propios no derivados de relación laboral.<br>
    <strong>Desconocido: </strong>Graduados sin información laboral registrada. Esto incluye personas sin empleo formal, inactivas, trabajando fuera del país, o en sectores no registrados en la seguridad social.<br>
    """,
)
