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
    lambda x: (
        "Pregrado"
        if x.startswith("TERCER")
        else ("Posgrado" if x.startswith("CUARTO") else "Otro")
    )
)

udla = "UNIVERSIDAD DE LAS AMERICAS"

# === 3. Filtrar estudiantes de posgrado en la UDLA
df_posgrado_udla = df[
    (df["TIPO_TITULO"] == "Posgrado")
    & (df["INSTITUCIÓN DE EDUCACIÓN SUPERIOR"] == udla)
]

# === 4. Encontrar universidades de pregrado de esos estudiantes
ids_posgrado_udla = set(df_posgrado_udla["IDENTIFICACION"])

df_pregrado = df[
    (df["TIPO_TITULO"] == "Pregrado") & (df["IDENTIFICACION"].isin(ids_posgrado_udla))
]

# === 5. Conteo completo y total GLOBAL ------------------------------
conteo_full = df_pregrado["INSTITUCIÓN DE EDUCACIÓN SUPERIOR"].value_counts()
total_estudiantes = conteo_full.sum()  # denominador global

# === 6. Top-10 y porcentaje -----------------------------------------
conteo_universidades = conteo_full.head(
    10
).reset_index()  # top-10  # genera 'index' y 0

# 👈 Pon los nombres correctos y en el orden correcto
conteo_universidades.columns = ["Universidad de Pregrado", "Cantidad"]

# Ahora sí existe la columna 'Cantidad'
conteo_universidades["Porcentaje"] = (
    conteo_universidades["Cantidad"] / total_estudiantes * 100
).round(1)
conteo_universidades["Texto"] = conteo_universidades["Porcentaje"].astype(str) + "%"

# === 7. Visualización
fig = px.bar(
    conteo_universidades,
    x="Cantidad",  # eje sigue en valores absolutos
    y="Universidad de Pregrado",
    orientation="h",
    text="Texto",  # muestra %
    hover_data={},  # ocultamos columnas extra
    title="Top 10 universidades de origen de estudiantes de posgrado en la UDLA",
)

fig.update_traces(
    textposition="inside",
    hovertemplate=(
        "Cantidad de estudiantes=%{x}"
        "<br>Universidad de Pregrado=%{y}"
        "<extra></extra>"
    ),
)

fig.update_layout(
    yaxis=dict(categoryorder="total ascending"),
    xaxis_title="Cantidad de Estudiantes",
    uniformtext_minsize=8,
    uniformtext_mode="show",
)

st.plotly_chart(fig, use_container_width=True)


# ════════════════════════════════════════════════════════════════════
#  DESTINO DE POSGRADO PARA EGRESADOS DE PREGRADO EN LA UDLA
# ════════════════════════════════════════════════════════════════════

# 1 Graduados de PREGRADO en la UDLA
df_pregrado_udla = df[
    (df["TIPO_TITULO"] == "Pregrado")
    & (df["INSTITUCIÓN DE EDUCACIÓN SUPERIOR"] == udla)
]
ids_pregrado_udla = set(df_pregrado_udla["IDENTIFICACION"])

# 2 Todos sus POSGRADOS (en cualquier universidad) ─ SIN duplicados
df_posgrados_todos = (
    df[
        (df["TIPO_TITULO"] == "Posgrado")
        & (df["IDENTIFICACION"].isin(ids_pregrado_udla))
    ]
    # convertir fecha dentro del subset
    .assign(
        FECHA_REG=lambda d: pd.to_datetime(
            d["FECHA DE REGISTRO"], dayfirst=True, errors="coerce"
        )
    )
    .sort_values("FECHA_REG")  # cronología real
    .drop_duplicates("IDENTIFICACION", keep="first")  # primer posgrado
    .drop(columns="FECHA_REG")  # limpiamos
)


# 3 Conteo global y total
conteo_full_dest = df_posgrados_todos[
    "INSTITUCIÓN DE EDUCACIÓN SUPERIOR"
].value_counts()
total_dest = conteo_full_dest.sum()

# 4 Top-10 + porcentajes
conteo_destinos = conteo_full_dest.head(10).reset_index()

conteo_destinos.columns = ["Universidad de Posgrado", "Cantidad"]

conteo_destinos["Porcentaje"] = (conteo_destinos["Cantidad"] / total_dest * 100).round(
    1
)
conteo_destinos["Texto"] = conteo_destinos["Porcentaje"].astype(str) + "%"

# 5 Gráfico
fig2 = px.bar(
    conteo_destinos,
    x="Cantidad",
    y="Universidad de Posgrado",
    orientation="h",
    text="Texto",
    hover_data={},
    title="Top 10 universidades destino de posgrado para egresados de pregrado UDLA",
)

fig2.update_traces(
    textposition="inside",
    hovertemplate=(
        "Cantidad de estudiantes=%{x}"
        "<br>Universidad de Posgrado=%{y}"
        "<extra></extra>"
    ),
)
fig2.update_layout(
    yaxis=dict(categoryorder="total ascending"),
    xaxis_title="Cantidad de Estudiantes",
    uniformtext_minsize=8,
    uniformtext_mode="show",
)

st.plotly_chart(fig2, use_container_width=True)
