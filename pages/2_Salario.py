import streamlit as st
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly

aplicar_tema_plotly()
st.title("Distribución de Salarios por Periodo")

# 🌀 Cargar datos sin procesar
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# Procesamiento específico
df = df_base.copy()
df = df[df['SALARIO.1'].notnull()]
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

facultad_sel = st.selectbox("Facultad", ["Todas"] + sorted(df_fil['FACULTAD'].dropna().unique()))
df_fil = df_fil if facultad_sel == "Todas" else df_fil[df_fil['FACULTAD'] == facultad_sel]

carrera_sel = st.selectbox("Carrera", ["Todas"] + sorted(df_fil['CarreraHomologada.1'].dropna().unique()))
df_fil = df_fil if carrera_sel == "Todas" else df_fil[df_fil['CarreraHomologada.1'] == carrera_sel]

cohorte_sel = st.selectbox("Cohorte (Año Graduación)", ["Todos"] + sorted(df_fil['AnioGraduacion.1'].dropna().unique()))
df_fil = df_fil if cohorte_sel == "Todos" else df_fil[df_fil['AnioGraduacion.1'] == cohorte_sel]

formal_sel = st.selectbox("Trabajo Formal", ["Todos"] + sorted(df_fil['Empleo formal'].dropna().astype(str).unique()))
df_fil = df_fil if formal_sel == "Todos" else df_fil[df_fil['Empleo formal'].astype(str) == formal_sel]

# --------------------------
# BOXPLOT Y RESUMEN
# --------------------------
if df_fil.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
else:
    fig = px.box(
        df_fil,
        x='Periodo',
        y='SALARIO.1',
        title='Distribución de Salarios por Periodo',
        labels={'SALARIO.1': 'Salario', 'Periodo': 'Año-Quimestre'},
        points='outliers'
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    resumen = df_fil['SALARIO.1'].describe()
    st.subheader("Resumen estadístico del salario")
    st.markdown(f"""
    - **Media:** ${resumen['mean']:.2f}  
    - **Mediana:** ${df_fil['SALARIO.1'].median():.2f}  
    - **Desviación estándar:** ${resumen['std']:.2f}  
    - **Q1 (percentil 25):** ${resumen['25%']:.2f}  
    - **Q3 (percentil 75):** ${resumen['75%']:.2f}  
    - **Máximo:** ${resumen['max']:.2f}  
    - **Mínimo:** ${resumen['min']:.2f}  
    - **Número de observaciones:** {int(resumen['count'])}
    """)
