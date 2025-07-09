import streamlit as st
import pandas as pd
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

aplicar_tema_plotly()
st.title("Tasa de Ocupación Laboral por Cohortes")

# 🌀 Cargar datos
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# 🏷️ Marcar quién está empleado
df_base['Esta_empleado'] = df_base['SALARIO.1'].notnull() | df_base['RUCEMP.1'].notnull()

# --------------------------
# 1️⃣ FILTROS (UNA SOLA VEZ)
# --------------------------
# Aquí incluimos "Trabajo Formal", para que el usuario seleccione.
df_filtrado, selecciones = aplicar_filtros(
    df_base.copy(),
    incluir=["Nivel", "Oferta Actual", "Facultad", "Carrera", "Trabajo Formal"]
)

tipo_grafico = st.radio("Tipo de gráfico", options=["Líneas", "Barras"], horizontal=True)

# --------------------------
# 2️⃣ CÁLCULO DE TASA POR COHORTE
# --------------------------
if df_filtrado.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
else:
    # 2.1 Numerador: graduados empleados (ya filtrado por Trabajo Formal)
    df_empleados = df_filtrado[df_filtrado['Esta_empleado']]
    empleados = (
        df_empleados
        .groupby("AnioGraduacion.1")["IdentificacionBanner.1"]
        .nunique()
    )

    # 2.2 Denominador: totales por cohorte, aplicando manualmente
    #      todos los filtros excepto "Trabajo Formal"
    df_total = df_base.copy()
    # Nivel
    if selecciones['Nivel'] != "Todos":
        df_total = df_total[df_total['regimen.1'] == selecciones['Nivel']]
    # Oferta Actual
    if selecciones['Oferta Actual'] != "Todos":
        df_total = df_total[df_total['Oferta actual'] == selecciones['Oferta Actual']]
    # Facultad
    if selecciones['Facultad'] != "Todas":
        df_total = df_total[df_total['FACULTAD'] == selecciones['Facultad']]
    # Carrera
    if selecciones['Carrera'] != "Todas":
        df_total = df_total[df_total['CarreraHomologada.1'] == selecciones['Carrera']]
    # (NO filtramos por 'Trabajo Formal' aquí)
    total = (
        df_total
        .groupby("AnioGraduacion.1")["IdentificacionBanner.1"]
        .nunique()
    )

    # 2.3 Armar el resumen y calcular la tasa
    resumen = (
        pd.DataFrame({'empleados': empleados, 'total': total})
          .reset_index()
          .query("total > 0")
          .assign(tasa=lambda d: d['empleados'] / d['total'])
          .sort_values('AnioGraduacion.1')
    )

    # 2.4 Graficar
    titulo = "Tasa de ocupación por cohorte"
    if tipo_grafico == 'Barras':
        fig = px.bar(
            resumen,
            x='AnioGraduacion.1',
            y='tasa',
            labels={'AnioGraduacion.1': 'Año de graduación', 'tasa': 'Tasa de empleo'},
            title=titulo,
            text_auto='.1%'
        )
    else:
        fig = px.line(
            resumen,
            x='AnioGraduacion.1',
            y='tasa',
            labels={'AnioGraduacion.1': 'Año de graduación', 'tasa': 'Tasa de empleo'},
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
    Este gráfico muestra la tasa de ocupación laboral: el porcentaje de graduados que tienen empleo formal en relación con el total de graduados de cada cohorte.<br><br>
    <strong>¿Qué se considera empleo formal?</strong><br>
    Una persona se considera empleada formalmente si cumple al menos una de estas condiciones:<br>
    <ul>
    <li>Relación de dependencia: trabaja bajo contrato y está registrada por un empleador en el IESS.</li>
    <li>Afiliación voluntaria: está afiliada por cuenta propia al IESS, como trabajador independiente, emprendedor, profesional autónomo, etc.</li>
    </ul>
    <strong>¿Y los que no tienen empleo formal?</strong><br>
    Se consideran sin empleo formal aquellos graduados que no tienen ningún tipo de afiliación al IESS. Esto puede incluir personas que:<br>
    <ul>
    <li>Están desempleadas o sin actividad laboral.</li>
    <li>Trabajan en el sector informal (sin registro en seguridad social).</li>
    <li>Residen o trabajan en el exterior.</li>
    </ul>
    <strong>Importante:</strong><br>
    Cada cohorte anual de graduación (por ejemplo, 2020, 2021, 2022...) es observada en cada uno de los trimestres del año 2024.<br><br>
    <strong>¿Cómo interpretar esta tasa?</strong><br>
    Una tasa más alta indica que una mayor proporción de graduados ha logrado integrarse al empleo formal. Una tasa más baja puede reflejar dificultades de inserción, informalidad, migración o falta de información.
    """
)
