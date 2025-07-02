import streamlit as st
import pandas as pd
import plotly.express as px
from dateutil.relativedelta import relativedelta
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

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

# --------------------------
# FILTROS
# --------------------------
df_fil, selecciones = aplicar_filtros(df, incluir=["Nivel", "Oferta Actual", "Facultad", "Carrera", "Cohorte", "Trabajo Formal"])

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

# --------------------------
# NOTA
# --------------------------
mostrar_tarjeta_nota(
    texto_principal="""
    <strong>📌 Nota:</strong><br>
    Esta visualización muestra la permanencia promedio (en meses) en un mismo empleador.
    """,
    nombre_filtro="Trabajo Formal",
    descripcion_filtro="""
    <strong>Relación de Dependencia: </strong>Graduados contratados formalmente por un empleador.<br>
    <strong>Afiliado Voluntario: </strong>Personas que se autoafiliaron al IESS. Esto puede incluir emprendedores, profesionales independientes, o personas con ingresos propios no derivados de relación laboral.<br>
    <strong>Desconocido: </strong>Graduados sin información laboral registrada. Esto incluye personas sin empleo formal, inactivas, trabajando fuera del país, o en sectores no registrados en la seguridad social.<br>
    """,
)
