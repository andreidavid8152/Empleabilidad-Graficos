import streamlit as st
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

aplicar_tema_plotly()
st.title("Tasa de Ocupacion por Trimestre - 2024")

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
    <strong> Nota:</strong><br>
    Esta visualización muestra la proporción de graduados con ocupación sobre el total de graduados.
    """,
    nombre_filtro="Trabajo Formal",
    descripcion_filtro="""
    <strong>Relación de Dependencia: </strong>Graduados contratados formalmente por un empleador.<br>
    <strong>Afiliado Voluntario: </strong>Personas que se autoafiliaron al IESS. Esto puede incluir emprendedores, profesionales independientes, o personas con ingresos propios no derivados de relación laboral.<br>
    <strong>Desconocido: </strong>Graduados sin información laboral registrada. Esto incluye personas sin empleo formal, inactivas, trabajando fuera del país, o en sectores no registrados en la seguridad social.<br>
    """,
)
