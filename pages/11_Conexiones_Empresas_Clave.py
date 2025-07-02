import streamlit as st
import pandas as pd
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

aplicar_tema_plotly()
st.title("🏢 Conexiones con Empresas Clave")

# 🌀 Cargar datos
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# Preprocesamiento
df = df_base.copy()
df['Empleo formal'] = df['Empleo formal'].astype(str).str.strip().str.upper()
df['NOMEMP.1'] = df['NOMEMP.1'].fillna('SIN EMPRESA')
df['Cantidad de empleados'] = pd.to_numeric(df['Cantidad de empleados'], errors='coerce')
df['Cantidad de empleados'] = df['Cantidad de empleados'].fillna(0)

# --------------------------
# FILTROS
# --------------------------
df_fil, selecciones = aplicar_filtros(df, incluir=["Nivel", "Oferta Actual", "Facultad", "Carrera", "Cohorte", "Trabajo Formal"])

# --------------------------
# FILTROS ADICIONALES
# --------------------------
sector_sel = st.selectbox(
    "Sector Económico",
    ["Todos"] + sorted(df_fil['SECTOR'].dropna().unique())
)
df_fil = df_fil if sector_sel == "Todos" else df_fil[df_fil['SECTOR'] == sector_sel]

tam_min = int(df_fil['Cantidad de empleados'].min())
tam_max = int(df_fil['Cantidad de empleados'].max())
tamano_rango = st.slider(
    "Tamaño de empresa (Cantidad de empleados)",
    min_value=tam_min, max_value=tam_max,
    value=(tam_min, tam_max), step=1
)
df_fil = df_fil[
    (df_fil['Cantidad de empleados'] >= tamano_rango[0]) &
    (df_fil['Cantidad de empleados'] <= tamano_rango[1])
]

# --------------------------
# GRÁFICO DE EMPRESAS
# --------------------------
top_empresas = df_fil['NOMEMP.1'].value_counts().nlargest(10).reset_index()
top_empresas.columns = ['Empresa', 'Contrataciones']

if top_empresas.empty:
    st.warning("No hay datos disponibles para esta combinación de filtros.")
else:
    fig = px.bar(
        top_empresas,
        x='Empresa',
        y='Contrataciones',
        text='Contrataciones',
        title='Top 10 empresas que contratan graduados'
    )
    fig.update_layout(yaxis_title='Número de graduados contratados')
    st.plotly_chart(fig, use_container_width=True)

# --------------------------
# NOTA
# --------------------------
mostrar_tarjeta_nota(
    texto_principal="""
    <strong>📌 Nota:</strong><br>
    Esta visualización muestra la relación entre graduados y principales empleadores institucionales.
    """,
    nombre_filtro="Trabajo Formal",
    descripcion_filtro="""
    <strong>Relación de Dependencia: </strong>Graduados contratados formalmente por un empleador.<br>
    <strong>Afiliado Voluntario: </strong>Personas que se autoafiliaron al IESS. Esto puede incluir emprendedores, profesionales independientes, o personas con ingresos propios no derivados de relación laboral.<br>
    <strong>Desconocido: </strong>Graduados sin información laboral registrada. Esto incluye personas sin empleo formal, inactivas, trabajando fuera del país, o en sectores no registrados en la seguridad social.<br>
    """,
)
