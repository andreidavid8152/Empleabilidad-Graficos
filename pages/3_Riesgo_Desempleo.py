import streamlit as st
import pandas as pd
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

aplicar_tema_plotly()
st.title("Riesgo de Desempleo")

# 🌀 Cargar datos
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# 🏷️ Añadir columna de empleo
df_base['Esta_empleado'] = df_base['SALARIO.1'].notnull() | df_base['RUCEMP.1'].notnull()

# --------------------------
# 1️⃣ FILTROS (incluye Trabajo Formal, sin Cohorte)
# --------------------------
df_filtrado, selecciones = aplicar_filtros(
    df_base.copy(),
    incluir=["Nivel", "Oferta Actual", "Facultad", "Carrera", "Trabajo Formal"]
)

tipo_grafico = st.radio("Tipo de gráfico", options=["Líneas", "Barras"], horizontal=True)

# --------------------------
# 2️⃣ CÁLCULO DE DESEMPLEO
# --------------------------
if df_filtrado.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
else:
    # 2.1 Numerador: filtrado por Trabajo Formal y empleo
    df_empleados = df_filtrado[df_filtrado["Esta_empleado"]]

    # Si se aplicó filtro de "Trabajo Formal", respetarlo aquí
    if selecciones['Trabajo Formal'] != "Todos":
        df_empleados = df_empleados[df_empleados["Empleo formal"].astype(str) == selecciones['Trabajo Formal']]

    empleados = (
        df_empleados
        .groupby("AnioGraduacion.1")["IdentificacionBanner.1"]
        .nunique()
    )

    # 2.2 Denominador: todos los graduados según filtros, sin Trabajo Formal
    df_total = df_base.copy()
    if selecciones['Nivel'] != "Todos":
        df_total = df_total[df_total['regimen.1'] == selecciones['Nivel']]
    if selecciones['Oferta Actual'] != "Todos":
        df_total = df_total[df_total['Oferta actual'] == selecciones['Oferta Actual']]
    if selecciones['Facultad'] != "Todas":
        df_total = df_total[df_total['FACULTAD'] == selecciones['Facultad']]
    if selecciones['Carrera'] != "Todas":
        df_total = df_total[df_total['CarreraHomologada.1'] == selecciones['Carrera']]

    total = (
        df_total
        .groupby("AnioGraduacion.1")["IdentificacionBanner.1"]
        .nunique()
    )

    # 2.3 Construcción del resumen
    resumen = (
        pd.DataFrame({'empleados': empleados, 'total': total})
        .reset_index()
        .query("total > 0")
        .assign(desempleo=lambda d: 1 - (d['empleados'] / d['total']))
        .sort_values('AnioGraduacion.1')
    )

    titulo = "Tasa de desempleo por cohorte"

    # 2.4 Gráfico
    if tipo_grafico == 'Barras':
        fig = px.bar(
            resumen,
            x='AnioGraduacion.1',
            y='desempleo',
            labels={'AnioGraduacion.1': 'Año de graduación', 'desempleo': 'Tasa de desempleo'},
            title=titulo,
            text_auto='.1%'
        )
    else:
        fig = px.line(
            resumen,
            x='AnioGraduacion.1',
            y='desempleo',
            labels={'AnioGraduacion.1': 'Año de graduación', 'desempleo': 'Tasa de desempleo'},
            title=titulo,
            markers=True
        )
        fig.update_traces(mode='lines+markers')
        fig.update_xaxes(dtick=1)
        fig.update_yaxes(tickformat=".0%")

    st.plotly_chart(fig, use_container_width=True)

# --------------------------
# 3️⃣ NOTA
# --------------------------
mostrar_tarjeta_nota(
    texto_principal="""
    <strong>📌 Nota:</strong><br>
    Este gráfico muestra la tasa de desempleo: es decir, el porcentaje de graduados de cada cohorte sin afiliación al sistema de seguridad social durante el año 2024, en relación con el total de graduados de esa cohorte.<br><br>
    <strong>¿Qué significa “sin afiliación”?</strong><br>
    Se consideran desempleados (en sentido amplio) quienes no tienen ningún registro formal de empleo, lo que puede incluir:<br>
    <ul>
    <li>Personas desempleadas o sin actividad laboral.</li>
    <li>Quienes trabajan en el sector informal (sin contrato ni afiliación).</li>
    <li>Personas que residen o trabajan fuera del país.</li>
    <li>Graduados con información laboral no reportada o no registrada.</li>
    </ul>
    <strong>¿Qué se excluye de esta categoría?</strong><br>
    No se consideran desempleados quienes tienen algún tipo de afiliación al IESS, ya sea por contrato laboral (relación de dependencia) o por cuenta propia (afiliación voluntaria, como en el caso de emprendedores o trabajadores independientes).<br><br>
    <strong>Importante:</strong><br>
    Cada punto representa la situación de una cohorte de graduados (según su año de graduación), medida en el año 2024.<br><br
    <strong>¿Cómo interpretar esta tasa?</strong><br>
    Una tasa más alta indica que una mayor proporción de graduados de esa cohorte no está registrada en empleo formal. Esto puede sugerir menor inserción laboral formal, más informalidad, migración o inactividad.
    """
)
