import streamlit as st
import pandas as pd
import plotly.express as px
from dateutil.relativedelta import relativedelta

from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

# ------------------------------------------------------------------
# AJUSTES ESTÉTICOS
# ------------------------------------------------------------------
aplicar_tema_plotly()
st.title("Duración del Empleo")

# ------------------------------------------------------------------
# 1. CARGA Y PRE-PROCESAMIENTO
# ------------------------------------------------------------------
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

df_base["FECINGAFI.1"] = pd.to_datetime(df_base["FECINGAFI.1"], errors="coerce")
df_base["Empleo formal"] = df_base["Empleo formal"].astype(str).str.strip().str.upper()
df_base = df_base.dropna(subset=["FECINGAFI.1", "IdentificacionBanner.1", "NOMEMP.1"])

# ------------------------------------------------------------------
# 2. CÁLCULO DE DURACIÓN EN CADA EMPLEO (incluye el último empleo)
# ------------------------------------------------------------------
df_ordenado = df_base.sort_values(["IdentificacionBanner.1", "NOMEMP.1", "FECINGAFI.1"])

empleos = []
for _, grupo in df_ordenado.groupby(["IdentificacionBanner.1", "NOMEMP.1"]):
    fechas = grupo["FECINGAFI.1"].tolist()
    for i in range(len(fechas) - 1):
        inicio, fin = fechas[i], fechas[i + 1]
        delta = relativedelta(fin, inicio)
        duracion_meses = delta.years * 12 + delta.months
        if duracion_meses > 0:
            fila = grupo.iloc[i].to_dict()
            fila["DuracionMeses"] = duracion_meses
            empleos.append(fila)
    # ✅ Incluir el último empleo con duración 0
    if fechas:
        fila_final = grupo.iloc[-1].to_dict()
        fila_final["DuracionMeses"] = 0
        empleos.append(fila_final)

df = pd.DataFrame(empleos)

# ------------------------------------------------------------------
# 3. APLICAR FILTROS (incluye Cohorte y Trabajo Formal)
# ------------------------------------------------------------------
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

# ------------------------------------------------------------------
# 4. INSIGHT Y VISUALIZACIÓN
# ------------------------------------------------------------------
if df_fil.empty:
    st.warning("No hay datos para esta combinación de filtros.")
else:
    # 4.1 Insight: mes con más despidos (duración > 0)
    df_despidos = df_fil[df_fil["DuracionMeses"] > 0]
    conteo_mes = df_despidos["DuracionMeses"].value_counts()

    top_month = int(conteo_mes.idxmax())
    count_top = int(conteo_mes.max())
    total_despidos = int(conteo_mes.sum())
    pct_top = round(count_top / total_despidos * 100, 1)

    # Mapeo de número de mes a nombre en español
    month_map = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre",
    }
    top_month_name = month_map.get(top_month, f"Mes {top_month}")

    texto_insight = (
        f"📊 <strong>{top_month_name}</strong> concentra el mayor porcentaje de despidos de "
        f"empleos formales (<strong>{pct_top}%</strong>), indicando un punto crítico de rotación."
    )
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
            {texto_insight}
        </p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 4.2 Histograma de duración con porcentaje dentro de las barras
    fig = px.histogram(
        df_fil,
        x="DuracionMeses",
        nbins=20,
        histnorm="percent",
        labels={"DuracionMeses": "Meses"},
        title="Distribución de duración de empleos",
    )
    fig.update_traces(
        texttemplate="%{y:.1f}%",
        textposition="inside",
        hovertemplate=(
            "Meses en el empleo: <b>%{x}</b><br>"
            "Porcentaje: <b>%{y:.1f}%</b><extra></extra>"
        ),
    )
    fig.update_layout(
        yaxis_title="Porcentaje de empleos",
        uniformtext_minsize=8,
        uniformtext_mode="hide",
    )
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------------
# 5. NOTA EXPLICATIVA
# ------------------------------------------------------------------
mostrar_tarjeta_nota(
    texto_principal="""
    <strong>📌 Nota:</strong><br>
    Esta visualización muestra la duración de los empleos (en meses) que han tenido los graduados, medida en un mismo empleador. 
    <br><br>
    Permite observar la estabilidad laboral de los egresados, identificando si los vínculos laborales tienden a ser cortos o prolongados. 
    Llama la atención el alto porcentaje de empleos que duran menos de un mes, lo que puede reflejar alta rotación, contratos temporales o salidas tempranas del sistema formal. 
    """
)
