import streamlit as st
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

aplicar_tema_plotly()
st.title("Tasa de ocupación laboral")

# Cargar datos sin procesar
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# Procesamiento específico de esta página
df = df_base.copy()

def asignar_trimestre(mes):
    return {2: 'Q1', 5: 'Q2', 9: 'Q3', 11: 'Q4'}.get(mes, None)

df['Trimestre'] = df['Mes.1'].apply(asignar_trimestre)
df['Esta_empleado'] = df['SALARIO.1'].notnull() | df['RUCEMP.1'].notnull()
df = df[df["Trimestre"].notnull()]
df["Periodo"] = df["Anio.1"].astype(str) + " " + df["Trimestre"]

# --------------------------
# FILTROS
# --------------------------
df_fil, selecciones = aplicar_filtros(df, incluir=["Nivel", "Oferta Actual", "Facultad", "Carrera", "Cohorte_multi", "Trabajo Formal"])

# --------------------------
# AGRUPACIÓN Y GRÁFICO
# --------------------------
if df_fil.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
else:
    # Si hay múltiples años seleccionados, agrupar por Periodo y Cohorte
    if isinstance(selecciones.get('Cohorte_multi'), list) and len(selecciones['Cohorte_multi']) > 1:
        
        # Total de graduados únicos por cohorte
        totales_cohorte = df_fil.groupby('AnioGraduacion.1')['IdentificacionBanner.1'].nunique().to_dict()

        # Empleados por cohorte y periodo (mes observado)
        resumen = df_fil[df_fil['Esta_empleado']].groupby(['Periodo', 'AnioGraduacion.1'])['IdentificacionBanner.1'].nunique().reset_index()
        resumen = resumen.rename(columns={'IdentificacionBanner.1': 'empleados'})

        # Añadir total de graduados por cohorte (fijo)
        resumen['total'] = resumen['AnioGraduacion.1'].map(totales_cohorte)
        resumen['tasa_empleabilidad'] = resumen['empleados'] / resumen['total']
        
        fig = px.line(
            resumen,
            x='Periodo',
            y='tasa_empleabilidad',
            color='AnioGraduacion.1',
            title='Tasa de Empleabilidad por Cohorte',
            markers=True,
            labels={'tasa_empleabilidad': 'Tasa de empleo', 'AnioGraduacion.1': 'Cohorte'}
        )
        fig.update_layout(xaxis_tickangle=-45)
    else:
        # Si solo hay un año o no se usa el multiselect, agrupar solo por Periodo
        # Obtener cohorte seleccionada
        cohorte = selecciones.get('Cohorte_multi')
        if isinstance(cohorte, list):
            cohorte = cohorte[0]

        # Total de graduados de esa cohorte
        total = df_fil['IdentificacionBanner.1'].nunique()

        # Empleados por periodo
        resumen = df_fil[df_fil['Esta_empleado']].groupby(['Periodo'])['IdentificacionBanner.1'].nunique().reset_index()
        resumen = resumen.rename(columns={'IdentificacionBanner.1': 'empleados'})
        resumen['total'] = total
        resumen['tasa_empleabilidad'] = resumen['empleados'] / resumen['total']
        
        fig = px.line(
            resumen,
            x='Periodo',
            y='tasa_empleabilidad',
            title='Tasa de Empleabilidad',
            markers=True,
            labels={'tasa_empleabilidad': 'Tasa de empleo'}
        )
        fig.update_layout(xaxis_tickangle=-45)

    st.plotly_chart(fig, use_container_width=True)

# --------------------------
# NOTA
# --------------------------
mostrar_tarjeta_nota(
    texto_principal="""
        <strong>📌 Nota:</strong><br>
        Este gráfico muestra la tasa de ocupación laboral: el porcentaje de graduados que tienen empleo formal en relación con el total de graduados de cada cohorte.
        <br><br>
        <strong>¿Qué se considera empleo formal?</strong><br>
        Una persona se considera empleada formalmente si cumple al menos una de estas condiciones:
        <ul>
        <li>Relación de dependencia: trabaja bajo contrato y está registrada por un empleador en el IESS.</li>
        <li>Afiliación voluntaria: está afiliada por cuenta propia al IESS, como trabajador independiente, emprendedor, profesional autónomo, etc.</li>
        </ul>
        <strong>¿Y los que no tienen empleo formal?</strong><br>
        Se consideran sin empleo formal aquellos graduados que no tienen ningún tipo de afiliación al IESS. Esto puede incluir personas que:
        <ul>
        <li>Están desempleadas o sin actividad laboral.</li>
        <li>Trabajan en el sector informal (sin registro en seguridad social).</li>
        <li>Residen o trabajan en el exterior.</li>
        </ul>
        <strong>Importante:</strong><br>
        Cada cohorte anual de graduación (por ejemplo, 2020, 2021, 2022...) es observada en cada uno de los trimestres del año 2024.
        <br><br>
        <strong>¿Cómo interpretar esta tasa?</strong><br>
        Una tasa más alta indica que una mayor proporción de graduados ha logrado integrarse al empleo formal. Una tasa más baja puede reflejar dificultades de inserción, informalidad, migración o falta de información.
    """
)
