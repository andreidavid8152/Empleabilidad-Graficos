import pandas as pd
from dateutil.relativedelta import relativedelta
import plotly.express as px
import streamlit as st

from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

# ------------------------------------------------------------------
# AJUSTES GLOBALES
# ------------------------------------------------------------------
aplicar_tema_plotly()
st.title("Índice de Rotación")

# ------------------------------------------------------------------
# 1. CARGA Y BLOQUEO DE COHORTE 2024
# ------------------------------------------------------------------
with st.spinner("Cargando datos..."):
    df = cargar_datos_empleabilidad()

df = df[df["AnioGraduacion.1"] == 2024].copy()  # 🔒 Solo cohorte 2024

# ------------------------------------------------------------------
# 2. LIMPIEZA Y ORDEN
# ------------------------------------------------------------------
df["FECINGAFI.1"] = pd.to_datetime(df["FECINGAFI.1"], errors="coerce")
df = df.dropna(subset=["FECINGAFI.1", "IdentificacionBanner.1", "NOMEMP.1"])
df = df.sort_values(by=["IdentificacionBanner.1", "FECINGAFI.1"])

# ------------------------------------------------------------------
# 3. FILTROS (sin Cohorte)
# ------------------------------------------------------------------
df_fil, selecciones = aplicar_filtros(
    df,
    incluir=["Nivel", "Oferta Actual", "Facultad", "Carrera", "Trabajo Formal"],
)


# ------------------------------------------------------------------
# 4. CÁLCULO DE ROTACIÓN
# ------------------------------------------------------------------
def calcular_rotacion(df_filtrado: pd.DataFrame):
    rotaciones = []

    for pid, grupo in df_filtrado.groupby("IdentificacionBanner.1"):
        grupo = grupo.sort_values("FECINGAFI.1")
        empresas = grupo["NOMEMP.1"].tolist()
        fechas = grupo["FECINGAFI.1"].tolist()
        carrera = grupo["CarreraHomologada.1"].iloc[0]

        rotado = 0
        if len(empresas) > 1:
            primera_empresa = empresas[0]
            primera_fecha = fechas[0]
            for i in range(1, len(empresas)):
                if empresas[i] != primera_empresa:
                    delta = relativedelta(fechas[i], primera_fecha)
                    meses = delta.years * 12 + delta.months
                    if meses <= 12:
                        rotado = 1
                        break

        rotaciones.append(
            {
                "IdentificacionBanner.1": pid,
                "CarreraHomologada.1": carrera,
                "Rotacion": rotado,
            }
        )

    df_rot = pd.DataFrame(rotaciones)
    resumen = (
        df_rot.groupby("CarreraHomologada.1")
        .agg(
            Total=("IdentificacionBanner.1", "count"),
            ConRotacion=("Rotacion", "sum"),
        )
        .reset_index()
    )
    resumen["TasaRotacion"] = resumen["ConRotacion"] / resumen["Total"] * 100
    return resumen.sort_values("TasaRotacion", ascending=False), df_rot


# ------------------------------------------------------------------
# 5. VISUALIZACIÓN + TARJETA INSIGHT
# ------------------------------------------------------------------
if df_fil.empty:
    st.warning("No hay datos para esta combinación de filtros.")
else:
    resumen, df_rot = calcular_rotacion(df_fil)
    tasa_total = (
        df_rot["Rotacion"].sum() / df_rot.shape[0] * 100 if not df_rot.empty else 0
    )

    # Partes dinámicas (carrera / facultad)
    partes_mensaje = []
    if selecciones.get("Carrera") and selecciones["Carrera"] != "Todas":
        partes_mensaje.append(f"la carrera <strong>{selecciones['Carrera']}</strong>")
    if selecciones.get("Facultad") and selecciones["Facultad"] != "Todas":
        partes_mensaje.append(f"la facultad <strong>{selecciones['Facultad']}</strong>")

    mensaje_intro = "El índice de rotación"
    if partes_mensaje:
        mensaje_intro += f" para {' y '.join(partes_mensaje)}"
    mensaje_intro += f" cohorte 2024 es de <strong>{tasa_total:.1f}%</strong>."

    # 🔄 Tarjeta con estilo pastel
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
                <strong>📊 Insight:</strong><br>{mensaje_intro}
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if resumen.empty:
        st.warning("No hay datos de rotación disponibles.")
    else:
        fig = px.bar(
            resumen,
            x="CarreraHomologada.1",
            y="TasaRotacion",
            text="TasaRotacion",
            title="Tasa de rotación en el primer año (cohorte 2024)",
            labels={
                "CarreraHomologada.1": "Carrera",
                "TasaRotacion": "Rotación (%)",
            },
        )
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
        fig.update_layout(
            xaxis_tickangle=-45,
            yaxis_title="Rotación (%)",
            height=600,
        )
        st.plotly_chart(fig, use_container_width=True)

# --------------------------
# NOTA
# --------------------------
mostrar_tarjeta_nota(
    texto_principal="""
    <strong>📌 Nota:</strong><br>
    Esta visualización muestra el índice de rotación laboral en el primer año desde la graduación, considerando únicamente a los graduados de la cohorte 2024 que sí consiguieron empleo formal durante 2024. 
    <br><br>
    El indicador refleja el porcentaje de graduados que cambió de empleador al menos una vez en ese año. Un valor más alto puede sugerir inestabilidad laboral, búsqueda de mejores condiciones o trabajos de corta duración. 
    """
)
