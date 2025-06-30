import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import plotly.colors as pc
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly
from utils.filtros import aplicar_filtros

aplicar_tema_plotly()
st.title("🔁 Movilidad Intersectorial")

# === Cargar datos con spinner ===
with st.spinner("Cargando datos..."):
    df = cargar_datos_empleabilidad()

df = df.dropna(subset=["SECTOR", "FECINGAFI.1"]).copy()
df.loc[:, "FECINGAFI.1"] = pd.to_datetime(df["FECINGAFI.1"], errors="coerce")
df = df.sort_values(by=['IdentificacionBanner.1', 'FECINGAFI.1'])

# Detectar transiciones de sector
df['sector_anterior'] = df.groupby('IdentificacionBanner.1')['SECTOR'].shift()
df['sector_actual'] = df['SECTOR']
df = df.dropna(subset=['sector_anterior', 'sector_actual'])
df = df[df['sector_anterior'] != df['sector_actual']]

# === Filtros ===
df_fil, _ = aplicar_filtros(df)

# === Generar datos para Sankey ===
def generar_flujo(df_filtrado):
    transiciones = df_filtrado.groupby(['sector_anterior', 'sector_actual']).size().reset_index(name='count')
    if transiciones.empty:
        return [], [], [], []

    labels = pd.unique(transiciones[['sector_anterior', 'sector_actual']].values.ravel())
    label_dict = {label: idx for idx, label in enumerate(labels)}
    source = transiciones['sector_anterior'].map(label_dict)
    target = transiciones['sector_actual'].map(label_dict)
    value = transiciones['count']

    return labels.tolist(), source.tolist(), target.tolist(), value.tolist()

labels, source, target, value = generar_flujo(df_fil)

# === Mostrar gráfico ===
if not labels:
    st.warning("No hay datos suficientes para mostrar movilidad entre sectores.")
else:
    colors = pc.qualitative.Pastel  # Puedes usar: Pastel, Set2, Bold, etc.
    color_palette = (colors * ((len(labels) // len(colors)) + 1))[:len(labels)]

    fig = go.Figure(data=[go.Sankey(
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=labels,
            color=color_palette
        ),
        link=dict(
            source=source,
            target=target,
            value=value
        )
    )])

    fig.update_layout(title_text="Transiciones entre sectores", font_size=10)
    st.plotly_chart(fig, use_container_width=True)
