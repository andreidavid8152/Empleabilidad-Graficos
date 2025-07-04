import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from dateutil.relativedelta import relativedelta
from math import ceil

# utilidades propias
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

# ------------------------------------------------------------------
# AJUSTES ESTÉTICOS
# ------------------------------------------------------------------
aplicar_tema_plotly()
st.title("⏱️ Tiempo al Primer Empleo desde la Graduación - 2024")

# ------------------------------------------------------------------
# 1. CARGA Y PRE-PROCESAMIENTO
# ------------------------------------------------------------------
with st.spinner("Cargando datos…"):
    df_base = cargar_datos_empleabilidad()

df = df_base.copy()
df['FechaGraduacion.1'] = pd.to_datetime(df['FechaGraduacion.1'], errors='coerce')
df['FECINGAFI.1']       = pd.to_datetime(df['FECINGAFI.1'],      errors='coerce')

# ------------------------------------------------------------------
# 2. FILTRAR A COHORTE 2024
# ------------------------------------------------------------------
df_2024_all = df[df['AnioGraduacion.1'] == 2024].copy()

# ------------------------------------------------------------------
# 3. PREPARAR DATAFRAME POR ESTUDIANTE
# ------------------------------------------------------------------
df_students = df_2024_all.drop_duplicates(subset='IdentificacionBanner.1').copy()

mask_emp = (
    df_2024_all['SALARIO.1'].notnull() |
    df_2024_all['RUCEMP.1'].notnull()
)
df_emp = df_2024_all[mask_emp]\
    .sort_values(['IdentificacionBanner.1', 'FECINGAFI.1'])

def obtener_fecha_primer_empleo(g):
    fg = g['FechaGraduacion.1'].iloc[0]
    post = g[g['FECINGAFI.1'] >= fg]
    if not post.empty:
        return post['FECINGAFI.1'].min()
    prev = g[g['FECINGAFI.1'] < fg]
    if not prev.empty:
        return prev['FECINGAFI.1'].max()
    return pd.NaT

primeras = (
    df_emp
    .groupby('IdentificacionBanner.1')
    .apply(obtener_fecha_primer_empleo)
    .reset_index(name='FechaIngresoPrimerEmpleo')
)
df_students = df_students.merge(primeras, on='IdentificacionBanner.1', how='left')

def calcular_meses(ing, grad):
    if pd.isna(ing):
        return np.nan
    if ing >= grad:
        d = relativedelta(ing, grad)
        return d.years * 12 + d.months
    return 0

df_students['Meses al primer empleo'] = df_students.apply(
    lambda r: calcular_meses(r['FechaIngresoPrimerEmpleo'], r['FechaGraduacion.1']),
    axis=1
)

# ------------------------------------------------------------------
# 4. APLICAR FILTROS
# ------------------------------------------------------------------
# 4.1 Con Trabajo Formal → para gráfica y métricas parciales
df_filtrado, selecciones = aplicar_filtros(
    df_students,
    incluir=["Nivel", "Oferta Actual", "Facultad", "Carrera", "Trabajo Formal"]
)

# Fijar cohorte
cohorte_sel = st.selectbox("Cohorte (Año Graduación)", ["2024"], index=0, disabled=True)
selecciones["Cohorte"] = cohorte_sel

# 4.2 Calcular total **sin** filtro de Trabajo Formal
df_base_total = df_students.copy()

# aplicar los otros filtros manualmente
# nivel → df['regimen.1'], oferta → df['Oferta actual']
# facultad → df['FACULTAD'], carrera → df['CarreraHomologada.1']
if selecciones["Nivel"] != "Todos":
    df_base_total = df_base_total[
        df_base_total["regimen.1"] == selecciones["Nivel"]
    ]
if selecciones["Oferta Actual"] != "Todos":
    df_base_total = df_base_total[
        df_base_total["Oferta actual"] == selecciones["Oferta Actual"]
    ]
if selecciones["Facultad"] != "Todas":
    df_base_total = df_base_total[
        df_base_total["FACULTAD"] == selecciones["Facultad"]
    ]
if selecciones["Carrera"] != "Todas":
    df_base_total = df_base_total[
        df_base_total["CarreraHomologada.1"] == selecciones["Carrera"]
    ]

# ------------------------------------------------------------------
# 5. MÉTRICAS
# ------------------------------------------------------------------
total          = df_base_total.shape[0]
mask_pregrad   = df_filtrado["FechaIngresoPrimerEmpleo"].notna() & \
                 (df_filtrado["FechaIngresoPrimerEmpleo"] < df_filtrado["FechaGraduacion.1"])
mask_postgrad  = df_filtrado["FechaIngresoPrimerEmpleo"].notna() & \
                 (df_filtrado["FechaIngresoPrimerEmpleo"] >= df_filtrado["FechaGraduacion.1"])
mask_noemp     = df_filtrado["FechaIngresoPrimerEmpleo"].isna()

pregrad_count  = int(mask_pregrad.sum())
postgrad_count = int(mask_postgrad.sum())
sinemp_count   = int(mask_noemp.sum())

# ------------------------------------------------------------------
# 5.1 TARJETA DE INSIGHT
# ------------------------------------------------------------------
df_plot = df_filtrado[mask_postgrad].copy()
if not df_plot.empty:
    df_plot["Meses al primer empleo"] = pd.to_numeric(
        df_plot["Meses al primer empleo"], errors="coerce"
    )
    df_plot["MesNum"] = df_plot["Meses al primer empleo"].fillna(0).astype(int)
    df_plot["MesText"] = df_plot["MesNum"].apply(
        lambda x: "Menos de un mes" if x == 0 else f"{x} mes{'es' if x != 1 else ''}"
    )

    freq = df_plot["MesText"].value_counts().reset_index()
    freq.columns = ["Mes", "Cantidad"]
    freq["Cantidad"] = freq["Cantidad"].astype(int)
    freq["Prioridad"] = freq["Mes"].apply(lambda m: 0 if m == "Menos de un mes" else 1)
    freq["MesNum"]     = freq["Mes"].apply(
        lambda m: 0 if m == "Menos de un mes" else int(m.split()[0])
    )
    freq = freq.sort_values(
        by=["Cantidad", "Prioridad", "MesNum"],
        ascending=[False, True, True]
    )
    mes_top = freq.iloc[0]["Mes"].lower()

    fac = selecciones.get("Facultad")
    car = selecciones.get("Carrera")
    if car and car != "Todas":
        sujeto = f"un egresado de la carrera {car}"
    elif fac and fac != "Todas":
        sujeto = f"un egresado de la facultad {fac}"
    else:
        sujeto = "un egresado"

    texto_mensaje = (
        f"A {sujeto} le toma en promedio {mes_top} conseguir empleo después de graduarse."
    )
    st.markdown(f"""
    <div style="
        background-color: #fdf0f6;
        border-left: 6px solid #d8b4e2;
        padding: 1rem;
        border-radius: 10px;
        margin-top: 1.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    ">
        <p style="margin: 0; font-size: 1.05rem;">
            <strong>📊 Insight:</strong><br>{texto_mensaje}
        </p>
    </div>
    """, unsafe_allow_html=True)

# ------------------------------------------------------------------
# 6. VISUALIZACIÓN
# ------------------------------------------------------------------
if df_plot.empty:
    st.warning("No hay datos con empleo post-graduación para los filtros seleccionados.")
else:
    freq["Porcentaje"] = (freq["Cantidad"] / freq["Cantidad"].sum() * 100).round(2)
    meses_vals = sorted({int(v) for v in df_plot["MesNum"] if v > 0})
    etiquetas  = ["Menos de un mes"] + [
        f"{m} mes{'es' if m != 1 else ''}" for m in meses_vals
    ]
    freq["Mes"] = pd.Categorical(freq["Mes"], categories=etiquetas, ordered=True)
    freq = freq.sort_values("Mes")

    fig = px.bar(
        freq,
        x="Mes",
        y="Cantidad",
        custom_data=["Porcentaje"],
        labels={"Mes": "Meses desde la graduación", "Cantidad": "Número de estudiantes"},
        title="Distribución del Tiempo al Primer Empleo (Cohorte 2024)"
    )
    fig.update_traces(
        hovertemplate=(
            "Meses desde la graduación: <b>%{x}</b><br>"
            "Número de estudiantes: %{y}<br>"
            "Porcentaje: %{customdata[0]}%<extra></extra>"
        )
    )
    max_y = freq["Cantidad"].max()
    step  = 1 if max_y <= 10 else ceil(max_y / 5)
    fig.update_yaxes(tickmode="linear", dtick=step, tickformat=",d")
    fig.update_layout(yaxis_title="Número de estudiantes", xaxis_title="Meses desde la graduación")
    st.plotly_chart(fig, use_container_width=True)

# ------------------------------------------------------------------
# 7. NOTA EXPLICATIVA
# ------------------------------------------------------------------
mostrar_tarjeta_nota(
    texto_principal="""
<strong>📌 Nota:</strong><br>
Meses promedio desde la graduación hasta el primer registro laboral formal. (Solo 2024)
""",
    nombre_filtro="Trabajo Formal",
    descripcion_filtro="""
<strong>Relación de Dependencia:</strong> Graduados contratados formalmente.<br>
<strong>Afiliado Voluntario:</strong> Autoafiliados al IESS (emprendedores, independientes, etc.).<br>
<strong>Desconocido:</strong> Sin información laboral registrada (sin empleo formal, inactivos,<br>
trabajando fuera del país o en sectores no reportados).
"""
)
