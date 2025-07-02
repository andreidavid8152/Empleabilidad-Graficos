import streamlit as st
import pandas as pd
import plotly.express as px
from utils.estilos import aplicar_tema_plotly
from utils.carga_datos import cargar_datos_titulos

# === 1. Configuración inicial
aplicar_tema_plotly()
st.title("🏫 Universidades de Origen - Posgrados")

# === 2. Cargar datos
with st.spinner("Cargando datos..."):
    df = cargar_datos_titulos()

df.columns = df.columns.str.upper().str.strip()
df["NIVEL ACADÉMICA"] = df["NIVEL ACADÉMICA"].str.upper().str.strip()
df["TIPO_TITULO"] = df["NIVEL ACADÉMICA"].apply(
    lambda x: "Pregrado" if x.startswith("TERCER") else (
              "Posgrado" if x.startswith("CUARTO") else "Otro")
)

udla = "UNIVERSIDAD DE LAS AMERICAS"

# === 3. Filtrar estudiantes de posgrado en la UDLA
df_posgrado_udla = df[
    (df["TIPO_TITULO"] == "Posgrado") &
    (df["INSTITUCIÓN DE EDUCACIÓN SUPERIOR"] == udla)
]

# === 4. Encontrar universidades de pregrado de esos estudiantes
ids_posgrado_udla = set(df_posgrado_udla["IDENTIFICACION"])

df_pregrado = df[
    (df["TIPO_TITULO"] == "Pregrado") &
    (df["IDENTIFICACION"].isin(ids_posgrado_udla))
]

# === 5. Contar universidades de origen
conteo_universidades = (
    df_pregrado["INSTITUCIÓN DE EDUCACIÓN SUPERIOR"]
    .value_counts()
    .drop(udla, errors="ignore")  # Excluir UDLA si aparece como pregrado
    .head(10)
    .reset_index()
)
conteo_universidades.columns = ["Universidad de Pregrado", "Cantidad de Estudiantes"]

# === 6. Visualización
fig = px.bar(
    conteo_universidades,
    x="Cantidad de Estudiantes",
    y="Universidad de Pregrado",
    orientation="h",
    text="Cantidad de Estudiantes",
    title="Top 10 universidades de origen de estudiantes de posgrado en la UDLA"
)
fig.update_layout(yaxis={'categoryorder':'total ascending'})
st.plotly_chart(fig, use_container_width=True)
