import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly
import plotly.express as px

aplicar_tema_plotly()
st.title("⚠️ Carreras Críticas por Baja Empleabilidad")

# 🌀 Cargar datos sin procesar
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# Preprocesamiento
df = df_base.copy()
df['Esta_empleado'] = df['SALARIO.1'].notnull() | df['RUCEMP.1'].notnull()

def asignar_quimestre(mes):
    return {2: 'Q1', 5: 'Q2', 9: 'Q3', 11: 'Q4'}.get(mes, None)

df['Quimestre'] = df['Mes.1'].apply(asignar_quimestre)
df = df[df['Quimestre'].notnull()]
df['Periodo'] = df['Anio.1'].astype(str) + ' ' + df['Quimestre']

# --------------------------
# FILTROS INTERDEPENDIENTES
# --------------------------
nivel_sel = st.selectbox("Nivel", ["Todos"] + sorted(df['regimen.1'].dropna().unique()))
df_fil = df if nivel_sel == "Todos" else df[df['regimen.1'] == nivel_sel]

oferta_sel = st.selectbox("Oferta Actual", ["Todos"] + sorted(df_fil['Oferta actual'].dropna().unique()))
df_fil = df_fil if oferta_sel == "Todos" else df_fil[df_fil['Oferta actual'] == oferta_sel]

facultad_sel = st.selectbox("Filtrar por Facultad (opcional)", ["Todas"] + sorted(df_fil['FACULTAD'].dropna().unique()))
df_fil = df_fil if facultad_sel == "Todas" else df_fil[df_fil['FACULTAD'] == facultad_sel]

# --------------------------
# SLIDER DE UMBRAL (porcentaje)
# --------------------------
umbral_pct = st.slider(
    "Umbral de alerta (% de empleabilidad mínima):",
    min_value=0, max_value=90, step=5, value=60,
    format="%d%%"
)
umbral = umbral_pct / 100  # Convertir a decimal para el cálculo

# --------------------------
# CÁLCULO DE ALERTAS
# --------------------------
resumen = df_fil.groupby(['CarreraHomologada.1', 'Periodo']).agg(
    empleados=('Esta_empleado', 'sum'),
    total=('IdentificacionBanner.1', 'nunique')
).reset_index()

resumen['tasa'] = resumen['empleados'] / resumen['total']
resumen = resumen[resumen['total'] >= 1]

carreras = []

for carrera, grupo in resumen.groupby('CarreraHomologada.1'):
    grupo = grupo.sort_values('Periodo')
    tasas = grupo['tasa'].values

    min_tasa = tasas.min()
    if len(grupo) >= 2:
        X = np.arange(len(grupo)).reshape(-1, 1)
        y = tasas
        modelo = LinearRegression().fit(X, y)
        pendiente = modelo.coef_[0]
    else:
        pendiente = 0

    alerta_tasa = min_tasa < umbral
    alerta_trend = pendiente < 0

    if alerta_tasa or alerta_trend:
        if alerta_tasa and alerta_trend:
            tipo = "Ambas"
        elif alerta_tasa:
            tipo = "Tasa baja"
        else:
            tipo = "Tendencia descendente"

        carreras.append({
            "Carrera": carrera,
            "MinTasa": min_tasa,
            "Pendiente": pendiente,
            "Tipo": tipo
        })

# --------------------------
# MOSTRAR RESULTADOS
# --------------------------
if not carreras:
    st.info("⚠ No se encontraron carreras críticas con los filtros y umbral actuales.")
else:
    df_alertas = pd.DataFrame(carreras)
    df_alertas.sort_values(by="MinTasa", inplace=True)

    def format_pct(x):
        return f"{x:.1%}" if pd.notnull(x) else ""

    def style_table(df):
        return df.style\
            .format({"MinTasa": format_pct, "Pendiente": "{:.2f}"})\
            .map(lambda v: 'background-color: #ffe6e6' if isinstance(v, float) and v < umbral else '', subset=['MinTasa'])\
            .map(lambda v: 'background-color: #fff0cc' if isinstance(v, float) and v < 0 else '', subset=['Pendiente'])

    st.dataframe(style_table(df_alertas), use_container_width=True)
