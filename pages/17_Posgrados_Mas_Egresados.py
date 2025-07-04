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
    lambda x: (
        "Pregrado"
        if x.startswith("TERCER")
        else ("Posgrado" if x.startswith("CUARTO") else "Otro")
    )
)

# === 3. Filtrar universidades que ofrecen posgrados
universidades_posgrado = sorted(
    df[df["TIPO_TITULO"] == "Posgrado"]["INSTITUCIÓN DE EDUCACIÓN SUPERIOR"]
    .dropna()
    .unique()
)
universidades_opciones = ["Todas"] + universidades_posgrado

# === 4. Filtro de universidad
uni_sel = st.selectbox("Universidad", universidades_opciones, index=0)

# === 4.1. Filtro de facultad dependiente de la universidad
# Primero filtramos el dataframe que contiene posgrados según universidad
if uni_sel != "Todas":
    df_facultades = df[
        (df["TIPO_TITULO"] == "Posgrado")
        & (df["INSTITUCIÓN DE EDUCACIÓN SUPERIOR"] == uni_sel)
    ]
else:
    df_facultades = df[df["TIPO_TITULO"] == "Posgrado"]

# Sacamos lista de facultades únicas
facultades_opciones = sorted(
    df_facultades.loc[df_facultades["FACULTAD"] != "SIN REGISTRO", "FACULTAD"].unique()
)
facultades_opciones = ["Todas"] + facultades_opciones

# Mostramos el selectbox
fac_sel = st.selectbox("Facultad", facultades_opciones, index=0)


# === 5. Filtrar posgrados según selección combinada
df_posgrados = df[df["TIPO_TITULO"] == "Posgrado"]

if uni_sel != "Todas":
    df_posgrados = df_posgrados[
        df_posgrados["INSTITUCIÓN DE EDUCACIÓN SUPERIOR"] == uni_sel
    ]

if fac_sel != "Todas":
    df_posgrados = df_posgrados[df_posgrados["FACULTAD"] == fac_sel]


# Conteo de egresados por programa
conteo_all = df_posgrados.groupby(
    "CARRERA"
).size()  # cuenta filas  # Series con índice = carrera, valor = conteo
total_egresados = int(conteo_all.sum())

conteo_posgrados = (
    conteo_all.sort_values(ascending=False)
    .head(10)  # top-10
    .reset_index(name="Cantidad")  # columna de conteo se llama "Cantidad"
    .rename(columns={"CARRERA": "Programa de Posgrado"})
)

# === 6. Calcular porcentaje y texto
conteo_posgrados["Porcentaje"] = (
    conteo_posgrados["Cantidad"] / total_egresados * 100
).round(1)
conteo_posgrados["Texto"] = conteo_posgrados["Porcentaje"].astype(str) + "%"

# === 7. Visualización
fig = px.bar(
    conteo_posgrados,
    x="Cantidad",
    y="Programa de Posgrado",
    orientation="h",
    text="Texto",  # mostrar %
    hover_data={},
    title="Top 10 programas de posgrado con más egresados"
    + (f" en {uni_sel}" if uni_sel != "Todas" else ""),
)

fig.update_traces(
    textposition="inside",
    hovertemplate=(
        "Cantidad de egresados=%{x}"  # 1ª línea  (x = valor de la barra)
        "<br>Programa de Posgrado=%{y}"  # 2ª línea  (y = etiqueta de la barra)
        "<extra></extra>"
    ),
)
fig.update_layout(
    yaxis=dict(categoryorder="total ascending"),
    xaxis_title="Cantidad de Egresados",  # mantenemos eje en valores absolutos
    uniformtext_minsize=8,
    uniformtext_mode="show",
)

st.plotly_chart(fig, use_container_width=True)
