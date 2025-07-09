import pandas as pd
import streamlit as st
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

aplicar_tema_plotly()
st.title("Movilidad Intersectorial")

# === Cargar datos con spinner ===
with st.spinner("Cargando datos..."):
    df = cargar_datos_empleabilidad()

# Preprocesamiento
df = df.dropna(subset=["SECTOR", "FECINGAFI.1"]).copy()
df.loc[:, "FECINGAFI.1"] = pd.to_datetime(df["FECINGAFI.1"], errors="coerce")
df = df.sort_values(by=['IdentificacionBanner.1', 'FECINGAFI.1'])

# Detectar transiciones de sector
df['sector_anterior'] = df.groupby('IdentificacionBanner.1')['SECTOR'].shift()
df['sector_actual'] = df['SECTOR']
df = df.dropna(subset=['sector_anterior', 'sector_actual'])
df = df[df['sector_anterior'] != df['sector_actual']]

# === Filtros generales + filtro por sector ===
# --------------------------
# FILTROS
# --------------------------
df_fil, selecciones = aplicar_filtros(df, incluir=["Nivel", "Oferta Actual", "Facultad", "Carrera", "Cohorte", "Trabajo Formal"])

sectores_disponibles = sorted(pd.unique(df_fil[['sector_anterior', 'sector_actual']].values.ravel()))
sectores_seleccionados = st.multiselect(
    "Filtrar por sectores involucrados:",
    options=sectores_disponibles,
    default=sectores_disponibles
)

df_fil = df_fil[
    df_fil['sector_anterior'].isin(sectores_seleccionados) &
    df_fil['sector_actual'].isin(sectores_seleccionados)
]


# === Tabla general de transiciones ===
st.subheader("📌 Tabla de transiciones generales")
tabla_general = (
    df_fil.groupby(["sector_anterior", "sector_actual"])
    .size()
    .reset_index(name="Cantidad")
    .rename(
        columns={"sector_anterior": "Sector Anterior", "sector_actual": "Sector Actual"}
    )
    .sort_values("Cantidad", ascending=False)
)

# --------------------------
# TARJETAS INSIGHT DE SECTORES MÁS COMUNES
# --------------------------
if not tabla_general.empty:
    # Sector del que más se cambian
    mas_salidas = (
        tabla_general.groupby("Sector Anterior")["Cantidad"]
        .sum()
        .sort_values(ascending=False)
        .idxmax()
    )

    # Sector al que más se cambian
    mas_llegadas = (
        tabla_general.groupby("Sector Actual")["Cantidad"]
        .sum()
        .sort_values(ascending=False)
        .idxmax()
    )

    texto_salidas = f"El sector desde el que más se cambian los graduados es <strong>{mas_salidas}</strong>."
    texto_llegadas = f"El sector al que más se trasladan los graduados es <strong>{mas_llegadas}</strong>."

    st.markdown(
        f"""
    <div style="
        background-color: #fdf0f6;
        border-left: 6px solid #d8b4e2;
        padding: 1rem;
        border-radius: 10px;
        margin-top: 1.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    ">
        <p style="margin: 0; font-size: 1.05rem;">
            <strong>📤 Insight:</strong><br>{texto_salidas}
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        f"""
    <div style="
        background-color: #fdf0f6;
        border-left: 6px solid #AA89CC;
        padding: 1rem;
        border-radius: 10px;
        margin-top: 1rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    ">
        <p style="margin: 0; font-size: 1.05rem;">
            <strong>📥 Insight:</strong><br>{texto_llegadas}
        </p>
    </div> <br/>
    """,
        unsafe_allow_html=True,
    )


if tabla_general.empty:
    st.info("No hay transiciones entre los sectores seleccionados.")
else:
    st.dataframe(tabla_general, use_container_width=True, hide_index=True)

# === Tabla por graduado ===
st.subheader("🧑‍🎓 Tabla de transiciones por graduado")
tabla_graduado = (
    df_fil[
        [
            "IdentificacionBanner.1",
            "Estudiante.1",
            "FECINGAFI.1",
            "sector_anterior",
            "sector_actual",
        ]
    ]
    .rename(
        columns={
            "IdentificacionBanner.1": "Identificacion",
            "Estudiante.1": "Estudiante",
            "FECINGAFI.1": "Fecha Ingreso Afiliacion",
            "sector_anterior": "Sector Anterior",
            "sector_actual": "Sector Actual",
        }
    )
    .sort_values(by=["Identificacion", "Fecha Ingreso Afiliacion"])
)


if tabla_graduado.empty:
    st.info("No hay transiciones registradas por estudiante con los filtros actuales.")
else:
    st.dataframe(tabla_graduado, use_container_width=True, hide_index=True)

# --------------------------
# NOTA
# --------------------------
mostrar_tarjeta_nota(
    texto_principal="""
    <strong>📌 Nota:</strong><br>
    Esta visualización muestra los cambios de sector económico que ocurren entre empleos consecutivos en la trayectoria laboral de los graduados. Permite identificar si los egresados permanecen en un mismo sector productivo o si se movilizan entre industrias distintas a lo largo del tiempo. 
    <br><br>
    Este análisis ayuda a entender el nivel de especialización o diversificación en la inserción laboral. 
    """
)
