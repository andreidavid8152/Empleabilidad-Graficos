import streamlit as st
import pandas as pd
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

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

# Clasificar empleo formal según nuevos valores
df['Empleo formal'] = df['Empleo formal'].astype(str).str.strip().str.upper()

def clasificar_formalidad(valor):
    if valor == 'RELACION DE DEPENDENCIA':
        return 1  # Formal
    elif valor in ['SIN RELACION DE DEPENDENCIA', 'AFILIACION VOLUNTARIA']:
        return 0  # No formal
    elif valor == 'DESCONOCIDO':
        return None
    else:
        return None

df['Formal'] = df['Empleo formal'].apply(clasificar_formalidad)

# --------------------------
# FILTROS INTERDEPENDIENTES
# --------------------------
df_fil, _ = aplicar_filtros(df)

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
        # Calcular porcentaje por trimestre
        conteo = df_trans.groupby(['Trimestre', 'Transición']).size().reset_index(name='Cantidad')
        total_por_trimestre = conteo.groupby('Trimestre')['Cantidad'].transform('sum')
        conteo['Porcentaje'] = (conteo['Cantidad'] / total_por_trimestre * 100).round(1)

        fig = px.bar(
            conteo,
            x='Trimestre',
            y='Porcentaje',
            color='Transición',
            text='Porcentaje',
            title='Transiciones de empleo por trimestre (%)'
        )
        fig.update_layout(
            barmode='stack',
            yaxis_title='Porcentaje de graduados',
            xaxis_title='Trimestre',
            yaxis_ticksuffix='%'
        )
        fig.update_traces(textposition="inside")
        st.plotly_chart(fig, use_container_width=True)

# --------------------------
# NOTA
# --------------------------
mostrar_tarjeta_nota(
    texto_principal="""
    <strong>📌 Nota:</strong><br>
    Esta visualización muestra el cambio de sector económico o tipo de empleador en el tiempo por parte del graduado.
    """,
    nombre_filtro="Trabajo Formal",
    descripcion_filtro="""
    <strong>Relación de Dependencia: </strong>Graduados contratados formalmente por un empleador.<br>
    <strong>Afiliado Voluntario: </strong>Personas que se autoafiliaron al IESS. Esto puede incluir emprendedores, profesionales independientes, o personas con ingresos propios no derivados de relación laboral.<br>
    <strong>Desconocido: </strong>Graduados sin información laboral registrada. Esto incluye personas sin empleo formal, inactivas, trabajando fuera del país, o en sectores no registrados en la seguridad social.<br>
    """,
)
