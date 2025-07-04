import streamlit as st
import pandas as pd
from utils.estilos import aplicar_tema_plotly
from utils.carga_datos import cargar_datos_titulos

aplicar_tema_plotly()
st.title("🎓 Continuidad Académica y Posgrados")

# === 1. Cargar datos
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_titulos()

df_base.columns = df_base.columns.str.upper().str.strip()
df_base["NIVEL ACADÉMICA"] = df_base["NIVEL ACADÉMICA"].str.upper().str.strip()
df_base["TIPO_TITULO"] = df_base["NIVEL ACADÉMICA"].apply(
    lambda x: "Pregrado" if x.startswith("TERCER") else (
              "Posgrado" if x.startswith("CUARTO") else "Otro")
)

# === 2. Filtros dentro del cuerpo
st.markdown("### 🔍 Selecciona filtros:")

# Filtro visual de facultades (sin afectar df_base)
facultades = df_base["FACULTAD"].dropna().unique()
facultades_filtradas = sorted([
    fac for fac in facultades
    if "posgrado" not in fac.lower() and fac.lower() != "sin registro"
])

col1, col2 = st.columns(2)
with col1:
    facultad_sel = st.selectbox("Facultad", ["Todas"] + facultades_filtradas, key="facultad_filtro")

# Creamos df_filtrado para aplicar los filtros dinámicos
df_filtrado = df_base.copy()
if facultad_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["FACULTAD"] == facultad_sel]

# Filtro visual de carreras (basado en el dataframe filtrado por facultad)
carreras_filtradas = sorted([
    car for car in df_filtrado["CARRERA"].dropna().unique()
    if "posgrado" not in car.lower() and car.lower() != "sin registro"
])
with col2:
    carrera_sel = st.selectbox("Carrera", ["Todas"] + carreras_filtradas, key="carrera_filtro")

# Aplicamos filtro de carrera solo si es distinto de "Todas"
if carrera_sel != "Todas":
    df_filtrado = df_filtrado[df_filtrado["CARRERA"] == carrera_sel]


# === 3. Cálculos
udla = "UNIVERSIDAD DE LAS AMERICAS"

pregrado_udla = df_filtrado[
    (df_filtrado["TIPO_TITULO"] == "Pregrado") &
    (df_filtrado["INSTITUCIÓN DE EDUCACIÓN SUPERIOR"] == udla)
]

posgrados = df_base[df_base["TIPO_TITULO"] == "Posgrado"]

ids_pregrado = set(pregrado_udla["IDENTIFICACION"])
ids_posgrado = set(posgrados["IDENTIFICACION"])
ids_continua = ids_pregrado & ids_posgrado

total_pregrado = len(ids_pregrado)
total_continua = len(ids_continua)
tasa_cont = round(100 * total_continua / total_pregrado, 1) if total_pregrado else None

ids_posgrado_udla = set(
    posgrados[posgrados["INSTITUCIÓN DE EDUCACIÓN SUPERIOR"] == udla]["IDENTIFICACION"]
)
ids_recompra = ids_pregrado & ids_posgrado_udla
tasa_recompra = round(100 * len(ids_recompra) / total_continua, 1) if total_continua else None

primer_posgrados = (
    posgrados[posgrados["IDENTIFICACION"].isin(ids_continua)]
    .sort_values(["IDENTIFICACION", "FECHA DE REGISTRO"])
    .groupby("IDENTIFICACION")
    .first()
    .reset_index()
    .rename(columns={"FECHA DE REGISTRO": "FECHA_POSGRADO"})
)

pregrados_base = (
    pregrado_udla[pregrado_udla["IDENTIFICACION"].isin(ids_continua)]
    .sort_values(["IDENTIFICACION", "FECHA DE REGISTRO"])
    .groupby("IDENTIFICACION")
    .first()
    .reset_index()
    .rename(columns={"FECHA DE REGISTRO": "FECHA_PREGRADO"})
)

df_tiempos1 = pd.merge(primer_posgrados, pregrados_base, on="IDENTIFICACION")
df_tiempos1["FECHA_PREGRADO"] = pd.to_datetime(df_tiempos1["FECHA_PREGRADO"])
df_tiempos1["FECHA_POSGRADO"] = pd.to_datetime(df_tiempos1["FECHA_POSGRADO"])
df_tiempos1["TIEMPO_ANIOS"] = (
    (df_tiempos1["FECHA_POSGRADO"] - df_tiempos1["FECHA_PREGRADO"])
    .dt.total_seconds() / (365.25 * 24 * 3600)
)
tiempo_1 = round(df_tiempos1["TIEMPO_ANIOS"].mean(), 1) if not df_tiempos1.empty else None

segundo_posgrados = (
    posgrados[posgrados["IDENTIFICACION"].isin(ids_continua)]
    .sort_values(["IDENTIFICACION", "FECHA DE REGISTRO"])
    .groupby("IDENTIFICACION")
    .nth(1)
    .reset_index()
    .rename(columns={"FECHA DE REGISTRO": "FECHA_2DO_POSGRADO"})
)

df_tiempos2 = pd.merge(
    segundo_posgrados,
    primer_posgrados[["IDENTIFICACION", "FECHA_POSGRADO"]],
    on="IDENTIFICACION",
    how="inner"
)
df_tiempos2["FECHA_2DO_POSGRADO"] = pd.to_datetime(df_tiempos2["FECHA_2DO_POSGRADO"])
df_tiempos2["FECHA_POSGRADO"] = pd.to_datetime(df_tiempos2["FECHA_POSGRADO"])
df_tiempos2["TIEMPO_ANIOS"] = (
    (df_tiempos2["FECHA_2DO_POSGRADO"] - df_tiempos2["FECHA_POSGRADO"])
    .dt.total_seconds() / (365.25 * 24 * 3600)
)
tiempo_2 = round(df_tiempos2["TIEMPO_ANIOS"].mean(), 1) if not df_tiempos2.empty else None

# === 4. Visualización en tarjetas
st.markdown("### 📊 Resultados")

def tarjeta(title, value, color="#ffffff", icon="✅"):
    st.markdown(f"""
    <div style='background-color:{color};padding:1.2rem 1rem;border-radius:12px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.1);text-align:center;
                border-left: 8px solid #6C63FF; margin-bottom:15px'>
        <div style='font-size:1.1rem;font-weight:bold;margin-bottom:5px;'>{icon} {title}</div>
        <div style='font-size:2rem;color:#333'>{value}</div>
    </div>
    """, unsafe_allow_html=True)

col1, col2 = st.columns(2)
with col1:
    tarjeta("Tasa de Continuidad", f"{tasa_cont}%" if tasa_cont is not None else "—", icon="📈")
    tarjeta("Tasa de Recompra UDLA", f"{tasa_recompra}%" if tasa_recompra is not None else "—", icon="🔁")
with col2:
    tarjeta("Tiempo al 1er Posgrado", f"{tiempo_1} años" if tiempo_1 is not None else "—", icon="⏱️")
    tarjeta("Tiempo al 2do Posgrado", f"{tiempo_2} años" if tiempo_2 is not None else "—", icon="📚")
