import pandas as pd
from dateutil.relativedelta import relativedelta
import plotly.express as px
import streamlit as st
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

aplicar_tema_plotly()
st.title("🔄 Índice de Rotación en el Primer Año")

# === Carga de datos ===
with st.spinner("Cargando datos..."):
    df = cargar_datos_empleabilidad()

df['FECINGAFI.1'] = pd.to_datetime(df['FECINGAFI.1'], errors='coerce')
df = df.dropna(subset=['FECINGAFI.1', 'IdentificacionBanner.1', 'NOMEMP.1'])
df = df.sort_values(by=['IdentificacionBanner.1', 'FECINGAFI.1'])

# === Filtros interdependientes ===
df_fil, _ = aplicar_filtros(df)

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
if df_fil.empty:
    st.warning("No hay datos para esta combinación de filtros.")
else:
    resumen = calcular_rotacion(df_fil)

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

# --------------------------
# NOTA
# --------------------------
mostrar_tarjeta_nota(
    texto_principal="""
    <strong>📌 Nota:</strong><br>
    Esta visualización muestra el número promedio de cambios de empleador por graduado en un periodo.
    """,
    nombre_filtro="Trabajo Formal",
    descripcion_filtro="""
    <strong>Relación de Dependencia: </strong>Graduados contratados formalmente por un empleador.<br>
    <strong>Afiliado Voluntario: </strong>Personas que se autoafiliaron al IESS. Esto puede incluir emprendedores, profesionales independientes, o personas con ingresos propios no derivados de relación laboral.<br>
    <strong>Desconocido: </strong>Graduados sin información laboral registrada. Esto incluye personas sin empleo formal, inactivas, trabajando fuera del país, o en sectores no registrados en la seguridad social.<br>
    """,
)
