import streamlit as st
import pandas as pd
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

aplicar_tema_plotly()
st.title("📉 Riesgo de Desempleo por Cohorte")

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
    Esta visualización muestra la proporción de graduados sin afiliación en un periodo determinado, respecto al total de la cohorte.
    """,
    nombre_filtro="Trabajo Formal",
    descripcion_filtro="""
    <strong>Relación de Dependencia: </strong>Graduados contratados formalmente por un empleador.<br>
    <strong>Afiliado Voluntario: </strong>Personas que se autoafiliaron al IESS. Esto puede incluir emprendedores, profesionales independientes, o personas con ingresos propios no derivados de relación laboral.<br>
    <strong>Desconocido: </strong>Graduados sin información laboral registrada. Esto incluye personas sin empleo formal, inactivas, trabajando fuera del país, o en sectores no registrados en la seguridad social.<br>
    """,
)
