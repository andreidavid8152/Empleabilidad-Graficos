import streamlit as st
import pandas as pd
import plotly.express as px
from utils.estilos import aplicar_tema_plotly
from utils.carga_datos import cargar_datos_titulos

# === 1. Configuración inicial
aplicar_tema_plotly()
st.title("🎓 Posgrados con más Egresados")

# === 2. Cargar datos
with st.spinner("Cargando datos..."):
    df = cargar_datos_titulos()

df.columns = df.columns.str.upper().str.strip()
df["NIVEL ACADÉMICA"] = df["NIVEL ACADÉMICA"].str.upper().str.strip()
df["TIPO_TITULO"] = df["NIVEL ACADÉMICA"].apply(
    lambda x: "Pregrado" if x.startswith("TERCER") else (
              "Posgrado" if x.startswith("CUARTO") else "Otro")
)

# === 3. Filtrar universidades que ofrecen posgrados
universidades_posgrado = sorted(
    df[df["TIPO_TITULO"] == "Posgrado"]["INSTITUCIÓN DE EDUCACIÓN SUPERIOR"]
    .dropna()
    .unique()
)
universidades_opciones = ["Todas"] + universidades_posgrado

# === 4. Filtro de universidad
st.markdown("### 🏛️ Selecciona universidad:")
uni_sel = st.selectbox("Universidad", universidades_opciones, index=0)

# === 5. Filtrar posgrados según selección
df_posgrados = df[df["TIPO_TITULO"] == "Posgrado"]
if uni_sel != "Todas":
    df_posgrados = df_posgrados[df_posgrados["INSTITUCIÓN DE EDUCACIÓN SUPERIOR"] == uni_sel]

# === 6. Contar egresados por programa de posgrado (CARRERA)
conteo_posgrados = (
    df_posgrados["CARRERA"]
    .value_counts()
    .head(10)
    .reset_index()
)
conteo_posgrados.columns = ["Programa de Posgrado", "Cantidad de Egresados"]

# === 7. Visualización
fig = px.bar(
    conteo_posgrados,
    x="Cantidad de Egresados",
    y="Programa de Posgrado",
    orientation="h",
    text="Cantidad de Egresados",
    title="Top 10 programas de posgrado con más egresados" + (f" en {uni_sel}" if uni_sel != "Todas" else ""),
)
fig.update_layout(yaxis={'categoryorder': 'total ascending'})
st.plotly_chart(fig, use_container_width=True)
