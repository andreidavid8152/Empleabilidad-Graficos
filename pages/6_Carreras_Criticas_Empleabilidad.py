import streamlit as st
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

import plotly.express as px

aplicar_tema_plotly()
st.title("Carreras en Estado Crítico de Empleabilidad")

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
df_fil, selecciones = aplicar_filtros(df, incluir=["Nivel", "Oferta Actual", "Facultad"])

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

# --------------------------
# NOTA
# --------------------------
mostrar_tarjeta_nota(
    texto_principal="""
    <strong>📌 Nota aclaratoria:</strong><br>
    Esta visualización identifica las carreras con empleabilidad crítica, tomando en cuenta dos factores:<br>
    <ul>
    <li>Tasa de empleabilidad más baja registrada en los últimos periodos (<em>MinTasa</em>).</li>
    <li>Tendencia de la empleabilidad: si la inserción laboral está mejorando, empeorando o permanece estable (<em>Pendiente</em>).</li>
    </ul>
    <strong>Se considera alerta cuando la empleabilidad cae por debajo del umbral definido.</strong><br><br>
    <strong>¿Qué se considera empleo formal?</strong><br>
    Graduados afiliados, ya sea:
    <ul>
    <li>Con contrato laboral (relación de dependencia), o</li>
    <li>Afiliados por cuenta propia (emprendedores, independientes, etc.).</li>
    </ul>
    <strong>¿Cómo interpretar esta visualización?</strong><br>
    Una carrera con baja empleabilidad y tendencia negativa requiere atención prioritaria, ya que combina un bajo nivel de inserción laboral con una dinámica que empeora con el tiempo.<br>
    En cambio, una carrera con baja empleabilidad, pero tendencia positiva podría estar en proceso de recuperación.
    """
)
