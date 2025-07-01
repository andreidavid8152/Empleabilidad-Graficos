import pandas as pd
import streamlit as st
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

aplicar_tema_plotly()
st.title("📊 Movilidad Intersectorial")

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
df_fil, _ = aplicar_filtros(df)
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
tabla_general = df_fil.groupby(['sector_anterior', 'sector_actual']).size().reset_index(name='Cantidad')
if tabla_general.empty:
    st.info("No hay transiciones entre los sectores seleccionados.")
else:
    st.dataframe(tabla_general, use_container_width=True, hide_index=True)

# === Tabla por graduado ===
st.subheader("🧑‍🎓 Tabla de transiciones por graduado")
tabla_graduado = df_fil[[
    'IdentificacionBanner.1', 'Estudiante.1', 'FECINGAFI.1',
    'sector_anterior', 'sector_actual'
]].sort_values(by=['IdentificacionBanner.1', 'FECINGAFI.1'])

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
    Esta visualización muestra los cambios de sector económico entre empleos consecutivos en la trayectoria del graduado.
    """,
    nombre_filtro="Trabajo Formal",
    descripcion_filtro="""
    <strong>Relación de Dependencia: </strong>Graduados contratados formalmente por un empleador.<br>
    <strong>Afiliado Voluntario: </strong>Personas que se autoafiliaron al IESS. Esto puede incluir emprendedores, profesionales independientes, o personas con ingresos propios no derivados de relación laboral.<br>
    <strong>Desconocido: </strong>Graduados sin información laboral registrada. Esto incluye personas sin empleo formal, inactivas, trabajando fuera del país, o en sectores no registrados en la seguridad social.<br>
    """,
)
