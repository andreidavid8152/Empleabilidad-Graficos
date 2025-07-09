import streamlit as st
import pandas as pd
import plotly.express as px
from utils.estilos import aplicar_tema_plotly
from utils.carga_datos import cargar_datos_titulos

# === 1. Configuración inicial
aplicar_tema_plotly()
st.title("🎓 Posgrados estudiados por egresados de pregrado")

# === 2. Cargar datos
with st.spinner("Cargando datos..."):
    df = cargar_datos_titulos()

# === 3. Normalizar columnas relevantes
df.columns = df.columns.str.upper().str.strip()
df["NIVEL ACADÉMICA"] = df["NIVEL ACADÉMICA"].str.upper().str.strip()

# Clasificar título
df["TIPO_TITULO"] = df["NIVEL ACADÉMICA"].apply(
    lambda x: (
        "Pregrado"
        if x.startswith("TERCER")
        else ("Posgrado" if x.startswith("CUARTO") else "Otro")
    )
)

# === 4. Filtro de origen de pregrado
df_pregrado = df[df["TIPO_TITULO"] == "Pregrado"]

# Universidades y facultades solo con pregrado
universidades = sorted(df_pregrado["INSTITUCIÓN DE EDUCACIÓN SUPERIOR"].dropna().unique())
universidades_opciones = ["Todas"] + universidades
uni_sel = st.selectbox("Universidad de pregrado", universidades_opciones, index=0)

# Facultades dependientes de universidad
if uni_sel != "Todas":
    df_fac = df_pregrado[df_pregrado["INSTITUCIÓN DE EDUCACIÓN SUPERIOR"] == uni_sel]
else:
    df_fac = df_pregrado

facultades = sorted(df_fac.loc[df_fac["FACULTAD"] != "SIN REGISTRO", "FACULTAD"].unique())
facultades_opciones = ["Todas"] + facultades
fac_sel = st.selectbox("Facultad de pregrado", facultades_opciones, index=0)

# === 5. Obtener cédulas (Identificacion) de egresados de esa universidad/facultad
df_filtrado_pregrado = df_pregrado.copy()
if uni_sel != "Todas":
    df_filtrado_pregrado = df_filtrado_pregrado[df_filtrado_pregrado["INSTITUCIÓN DE EDUCACIÓN SUPERIOR"] == uni_sel]
if fac_sel != "Todas":
    df_filtrado_pregrado = df_filtrado_pregrado[df_filtrado_pregrado["FACULTAD"] == fac_sel]

cedulas_pregrado = df_filtrado_pregrado["IDENTIFICACION"].dropna().unique()

# === 6. Buscar sus posgrados (por identificación)
df_posgrados = df[
    (df["TIPO_TITULO"] == "Posgrado") & (df["IDENTIFICACION"].isin(cedulas_pregrado))
]

# === 7. Conteo de posgrados
conteo = (
    df_posgrados.groupby("CARRERA")
    .size()
    .sort_values(ascending=False)
    .head(10)
    .reset_index(name="Cantidad")
    .rename(columns={"CARRERA": "Programa de Posgrado"})
)

# Si no hay resultados
if conteo.empty:
    st.warning("No se encontraron posgrados registrados para los egresados seleccionados.")
else:
    total = int(conteo["Cantidad"].sum())
    conteo["Porcentaje"] = (conteo["Cantidad"] / total * 100).round(1)
    conteo["Texto"] = conteo["Porcentaje"].astype(str) + "%"

    # === 8. Visualización
    fig = px.bar(
        conteo,
        x="Cantidad",
        y="Programa de Posgrado",
        orientation="h",
        text="Texto",
        title="Top 10 posgrados estudiados por egresados"
        + (f" de {fac_sel}" if fac_sel != "Todas" else "")
        + (f" en {uni_sel}" if uni_sel != "Todas" else ""),
    )

    fig.update_traces(
        textposition="inside",
        hovertemplate=(
            "Cantidad de egresados=%{x}"
            "<br>Programa de Posgrado=%{y}"
            "<extra></extra>"
        ),
    )
    fig.update_layout(
        yaxis=dict(categoryorder="total ascending"),
        xaxis_title="Cantidad de Egresados",
        uniformtext_minsize=8,
        uniformtext_mode="show",
    )

    st.plotly_chart(fig, use_container_width=True)
