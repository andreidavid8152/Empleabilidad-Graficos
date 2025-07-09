import streamlit as st
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

aplicar_tema_plotly()
st.title("Distribución por Sector Económico")

# 🌀 Cargar datos sin procesar
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# Procesamiento específico
df = df_base.copy()
df["Esta_empleado"] = df["SALARIO.1"].notnull() | df["RUCEMP.1"].notnull()

# Filtrar solo empleados con sector y mes válido
df = df[df["Esta_empleado"] & df["SECTOR"].notnull() & df["Mes.1"].notnull()]

# Tomar el último mes por graduado como referencia
df = df.sort_values(by=["IdentificacionBanner.1", "Mes.1"], ascending=[True, False])
df = df.drop_duplicates(subset="IdentificacionBanner.1", keep="first")

# --------------------------
# FILTROS
# --------------------------
df_fil, selecciones = aplicar_filtros(
    df,
    incluir=[
        "Nivel",
        "Oferta Actual",
        "Facultad",
        "Carrera",
        "Cohorte",
        "Trabajo Formal",
    ],
)

# --------------------------
# GRÁFICO POR SECTOR
# --------------------------
if df_fil.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
else:
    # Calcular cantidad y porcentaje
    conteo = df_fil["SECTOR"].value_counts().reset_index()
    conteo.columns = ["Sector Económico", "Cantidad"]
    total = conteo["Cantidad"].sum()
    conteo["PorcentajeTexto"] = (conteo["Cantidad"] / total * 100).round(2).astype(
        str
    ) + "%"

    # Gráfico de barras horizontal
    fig = px.bar(
        conteo,
        x="Cantidad",
        y="Sector Económico",
        orientation="h",
        title="Distribución por Sector Económico",
        labels={"Cantidad": "Número de Graduados"},
        text="PorcentajeTexto",  # 👉 solo como texto visual sobre la barra
        hover_data={
            "Sector Económico": False,
            "Cantidad": True,
            "PorcentajeTexto": False,  # ✅ Ocultamos del tooltip
        },
    )

    fig.update_layout(yaxis={"categoryorder": "total ascending"})
    fig.update_traces(textposition="outside")

    st.plotly_chart(fig, use_container_width=True)

# --------------------------
# NOTA
# --------------------------
mostrar_tarjeta_nota(
    texto_principal="""
    <strong>📌 Nota:</strong><br>
    Esta visualización muestra en qué sectores económicos están empleados formalmente los graduados, según la clasificación de actividades económicas CIIU Rev. 4.<br>
    Cada barra representa el número de graduados registrados en empresas de un sector específico durante el año analizado.<br><br>
    <strong>¿Cómo interpretar este gráfico?</strong><br>
    Permite conocer en qué ramas de la economía se insertan los graduados, identificar los sectores con mayor concentración y detectar áreas con baja o nula presencia laboral formal.
    """
)
