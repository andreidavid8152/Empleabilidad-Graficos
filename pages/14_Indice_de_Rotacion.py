import pandas as pd
from dateutil.relativedelta import relativedelta
import plotly.express as px
import streamlit as st
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly

aplicar_tema_plotly()
st.title("🔄 Índice de Rotación en el Primer Año")

# === Carga de datos ===
with st.spinner("Cargando datos..."):
    df = cargar_datos_empleabilidad()

df['FECINGAFI.1'] = pd.to_datetime(df['FECINGAFI.1'], errors='coerce')
df = df.dropna(subset=['FECINGAFI.1', 'IdentificacionBanner.1', 'NOMEMP.1'])
df = df.sort_values(by=['IdentificacionBanner.1', 'FECINGAFI.1'])

# === Filtros interdependientes ===
nivel = st.selectbox("Nivel", ["Todos"] + sorted(df['regimen.1'].dropna().unique()))
df_f = df if nivel == "Todos" else df[df['regimen.1'] == nivel]

oferta = st.selectbox("Oferta Actual", ["Todos"] + sorted(df_f['Oferta actual'].dropna().unique()))
df_f = df_f if oferta == "Todos" else df_f[df_f['Oferta actual'] == oferta]

facultad = st.selectbox("Facultad", ["Todas"] + sorted(df_f['FACULTAD'].dropna().unique()))
df_f = df_f if facultad == "Todas" else df_f[df_f['FACULTAD'] == facultad]

carrera = st.selectbox("Carrera", ["Todas"] + sorted(df_f['CarreraHomologada.1'].dropna().unique()))
df_f = df_f if carrera == "Todas" else df_f[df_f['CarreraHomologada.1'] == carrera]

cohorte = st.selectbox("Cohorte", ["Todos"] + sorted(df_f['AnioGraduacion.1'].dropna().unique()))
df_f = df_f if cohorte == "Todos" else df_f[df_f['AnioGraduacion.1'] == cohorte]

tipo_empleo = st.selectbox("Trabajo Formal", ["Todos", "EMPLEO FORMAL", "EMPLEO NO FORMAL"])
if tipo_empleo != "Todos":
    df_f = df_f[df_f['Empleo formal'].str.strip().str.upper() == tipo_empleo]

# === Cálculo de rotación ===
def calcular_rotacion(df_filtrado):
    rotaciones = []
    for pid, grupo in df_filtrado.groupby('IdentificacionBanner.1'):
        empresas = grupo['NOMEMP.1'].tolist()
        fechas = grupo['FECINGAFI.1'].tolist()
        carrera = grupo['CarreraHomologada.1'].iloc[0]

        rotado = 0
        if len(empresas) > 1:
            primera_fecha = fechas[0]
            for i in range(1, len(empresas)):
                if empresas[i] != empresas[i - 1]:
                    delta = relativedelta(fechas[i], primera_fecha)
                    meses = delta.years * 12 + delta.months
                    if meses <= 12:
                        rotado = 1
                        break

        rotaciones.append({
            'IdentificacionBanner.1': pid,
            'CarreraHomologada.1': carrera,
            'Rotacion': rotado
        })

    df_rot = pd.DataFrame(rotaciones)
    resumen = df_rot.groupby('CarreraHomologada.1').agg(
        Total=('IdentificacionBanner.1', 'count'),
        ConRotacion=('Rotacion', 'sum')
    ).reset_index()
    resumen['TasaRotacion'] = resumen['ConRotacion'] / resumen['Total'] * 100
    return resumen.sort_values('TasaRotacion', ascending=False)

# === Mostrar gráfico ===
if df_f.empty:
    st.warning("No hay datos para esta combinación de filtros.")
else:
    resumen = calcular_rotacion(df_f)

    if resumen.empty:
        st.warning("No hay datos de rotación disponibles.")
    else:
        fig = px.bar(
            resumen,
            x='CarreraHomologada.1',
            y='TasaRotacion',
            text='TasaRotacion',
            title="Tasa de rotación en el primer año por carrera",
            labels={'CarreraHomologada.1': 'Carrera', 'TasaRotacion': 'Rotación (%)'}
        )
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside')
        fig.update_layout(xaxis_tickangle=-45, yaxis_title="Rotación (%)", height=600)
        st.plotly_chart(fig, use_container_width=True)
