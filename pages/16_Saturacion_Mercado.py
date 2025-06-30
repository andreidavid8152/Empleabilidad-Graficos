import pandas as pd
import numpy as np
import streamlit as st
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly
from utils.filtros import aplicar_filtros

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
df_fil, _ = aplicar_filtros(df)

# === Calcular resumen ===
if df_fil.empty:
    st.warning("No hay datos disponibles para los filtros seleccionados.")
else:
    resumen = df_fil.groupby(['CarreraHomologada.1', 'Periodo']).agg({
        'IdentificacionBanner.1': 'nunique',
        'TieneSalario': lambda x: np.mean(x) * 100,
        'SALARIO.1': 'mean',
        'Empleo formal': lambda x: df_fil.loc[x.index][x == 'EMPLEO FORMAL']['IdentificacionBanner.1'].nunique()
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
