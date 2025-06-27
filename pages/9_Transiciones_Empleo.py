import streamlit as st
import pandas as pd
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly

aplicar_tema_plotly()
st.title("🔄 Transiciones de Empleo por Trimestre")

# 🌀 Cargar datos
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# === Preprocesamiento específico ===
df = df_base.copy()
df['SALARIO.1'] = pd.to_numeric(df['SALARIO.1'], errors='coerce')
df = df[df['Mes.1'].isin([2, 5, 9, 11])]  # Solo meses válidos

# Mantener por persona y mes el salario más alto
duplicados = df.duplicated(subset=['IdentificacionBanner.1', 'Mes.1'], keep=False)
df_multi = df[duplicados].copy().sort_values('SALARIO.1', ascending=False)
df_multi = df_multi.drop_duplicates(subset=['IdentificacionBanner.1', 'Mes.1'], keep='first')
df_uniq = df[~duplicados].copy()
df = pd.concat([df_uniq, df_multi], ignore_index=True)

# Clasificar empleo formal
df['Empleo formal'] = df['Empleo formal'].astype(str).str.strip().str.upper()
df['Formal'] = df['Empleo formal'].map({'EMPLEO FORMAL': 1, 'EMPLEO NO FORMAL': 0})

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
# GENERAR GRÁFICO DE TRANSICIONES
# --------------------------
if df_fil.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
else:
    pivot = df_fil.pivot(index='IdentificacionBanner.1', columns='Mes.1', values='Formal')

    if not set([2, 5, 9, 11]).issubset(pivot.columns):
        st.warning("No hay suficientes datos para calcular las transiciones.")
    else:
        pivot = pivot[[2, 5, 9, 11]]
        pivot.columns = ['Feb', 'May', 'Sep', 'Nov']

        def clasificar(ant, act):
            if pd.isna(ant) or pd.isna(act):
                return 'Desconocido'
            elif ant == 1 and act == 1:
                return 'Permanece Formal'
            elif ant == 0 and act == 0:
                return 'Permanece Informal'
            elif ant == 1 and act == 0:
                return 'Pasa a Informal'
            elif ant == 0 and act == 1:
                return 'Pasa a Formal'
            return 'Desconocido'

        transiciones = []
        for (a, b), q in zip([('Feb', 'May'), ('May', 'Sep'), ('Sep', 'Nov')], ['Q1→Q2', 'Q2→Q3', 'Q3→Q4']):
            temp = pivot[[a, b]].copy()
            temp['Trimestre'] = q
            temp['Transición'] = temp.apply(lambda row: clasificar(row[a], row[b]), axis=1)
            transiciones.append(temp[['Trimestre', 'Transición']])

        df_trans = pd.concat(transiciones)
        conteo = df_trans.groupby(['Trimestre', 'Transición']).size().reset_index(name='Cantidad')

        fig = px.bar(
            conteo,
            x='Trimestre',
            y='Cantidad',
            color='Transición',
            text='Cantidad',
            title='Transiciones de empleo por trimestre'
        )
        fig.update_layout(barmode='stack', yaxis_title='Número de graduados', xaxis_title='Trimestre')
        st.plotly_chart(fig, use_container_width=True)
