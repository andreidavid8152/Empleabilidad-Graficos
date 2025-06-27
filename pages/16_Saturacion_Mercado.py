import pandas as pd
import numpy as np
import streamlit as st
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly

# === Configuración inicial ===
aplicar_tema_plotly()
st.title("🚨 Alerta de Saturación del Mercado Laboral")

# === Cargar datos ===
with st.spinner("Cargando datos..."):
    df = cargar_datos_empleabilidad()

df['TieneSalario'] = df['SALARIO.1'].notna()
df['Periodo'] = df['AnioGraduacion.1'].astype(str)
df['Empleo formal'] = df['Empleo formal'].str.upper().str.strip()

# === Filtros globales (ordenado) ===
niveles = ["Todos"] + sorted(df['regimen.1'].dropna().unique())
nivel = st.selectbox("Nivel", niveles)
if nivel != "Todos":
    df = df[df['regimen.1'] == nivel]

ofertas = ["Todas"] + sorted(df['Oferta actual'].dropna().unique())
oferta = st.selectbox("Oferta Actual", ofertas)
if oferta != "Todas":
    df = df[df['Oferta actual'] == oferta]

facultades = ["Todas"] + sorted(df['FACULTAD'].dropna().unique())
facultad = st.selectbox("Facultad", facultades)
if facultad != "Todas":
    df = df[df['FACULTAD'] == facultad]

carreras = ["Todas"] + sorted(df['CarreraHomologada.1'].dropna().unique())
carrera = st.selectbox("Carrera", carreras)
if carrera != "Todas":
    df = df[df['CarreraHomologada.1'] == carrera]

cohortes = ["Todas"] + sorted(df['AnioGraduacion.1'].dropna().unique())
cohorte = st.selectbox("Cohorte", cohortes)
if cohorte != "Todas":
    df = df[df['AnioGraduacion.1'] == cohorte]

tipos_empleo = ["TODOS", "EMPLEO FORMAL", "EMPLEO NO FORMAL"]
tipo_empleo = st.selectbox("Trabajo Formal", tipos_empleo)
if tipo_empleo != "TODOS":
    df = df[df['Empleo formal'] == tipo_empleo]

# === Calcular resumen ===
if df.empty:
    st.warning("No hay datos disponibles para los filtros seleccionados.")
else:
    resumen = df.groupby(['CarreraHomologada.1', 'Periodo']).agg({
        'IdentificacionBanner.1': 'nunique',
        'TieneSalario': lambda x: np.mean(x) * 100,
        'SALARIO.1': 'mean',
        'Empleo formal': lambda x: df.loc[x.index][x == 'EMPLEO FORMAL']['IdentificacionBanner.1'].nunique()
    }).reset_index()

    resumen.rename(columns={
        'IdentificacionBanner.1': 'Cantidad Graduados',
        'SALARIO.1': 'Salario Promedio'
    }, inplace=True)

    resumen['Formales'] = resumen['Empleo formal']
    resumen['No Formales'] = resumen['Cantidad Graduados'] - resumen['Formales']
    resumen['Con salario (%)'] = resumen['TieneSalario'].round(1)

    # === Calcular alerta de saturación ===
    def alerta(row):
        if row['Cantidad Graduados'] > 50 and row['No Formales'] / row['Cantidad Graduados'] > 0.5:
            return '🔴 Alta Saturación'
        elif row['Cantidad Graduados'] > 30 and row['No Formales'] / row['Cantidad Graduados'] > 0.3:
            return '🟡 Media Saturación'
        else:
            return '🟢 Sin Alerta'

    resumen['Alerta Saturación'] = resumen.apply(alerta, axis=1)

    resumen = resumen[[
        'CarreraHomologada.1', 'Periodo', 'Cantidad Graduados',
        'Con salario (%)', 'Salario Promedio', 'Formales',
        'No Formales', 'Alerta Saturación'
    ]]

    st.dataframe(resumen, use_container_width=True)
