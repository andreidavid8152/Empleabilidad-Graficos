import streamlit as st
import pandas as pd
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

# Aplicar tema y título
aplicar_tema_plotly()
st.title("🏆 Ranking de Cargos Ocupados por Graduados")

# 🌀 Cargar datos
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# --------------------------
# Limpieza y exclusión de 'DESCONOCIDO'
# --------------------------
df = df_base.copy()
df["Empleo formal"] = df["Empleo formal"].astype(str).str.strip().str.upper()
df = df[df["Empleo formal"] != "DESCONOCIDO"]  # excluye 'DESCONOCIDO'
df["SALARIO.1"] = pd.to_numeric(df["SALARIO.1"], errors="coerce")
df["OCUAFI.1"] = df["OCUAFI.1"].fillna("SIN INFORMACIÓN")

# --------------------------
# FILTROS
# --------------------------
df_fil, selecciones = aplicar_filtros(
    df,
    incluir=[
        "Nivel",
        "Oferta Actual",
        "Facultad",
        "Carrera",
        "Cohorte",
        "Trabajo Formal",
    ],
)

# --------------------------
# LÓGICA DE ÚNICO POR GRADUADO
# --------------------------
# Para cada graduado, tomar su registro del mes más reciente (mayor Mes.1)
# y, en caso de empate en Mes.1, el de mayor SALARIO.1.
df_emp_unicos = df_fil.sort_values(
    ["IdentificacionBanner.1", "Mes.1", "SALARIO.1"], ascending=[True, False, False]
).drop_duplicates(subset="IdentificacionBanner.1", keep="first")

# --------------------------
# CÁLCULO DE TOTALES, PORCENTAJES Y SALARIO PROMEDIO
# --------------------------
total_unicos = df_emp_unicos.shape[0]

resumen = (
    df_emp_unicos.groupby("OCUAFI.1")
    .agg(Total=("OCUAFI.1", "count"), SalarioPromedio=("SALARIO.1", "mean"))
    .reset_index()
    .sort_values("Total", ascending=False)
    .head(15)
)
resumen["Porcentaje"] = resumen["Total"] / total_unicos * 100
resumen["PorcentajeTexto"] = resumen["Porcentaje"].round(2).astype(str) + "%"

# --------------------------
# GRÁFICO
# --------------------------
if resumen.empty:
    st.warning("No hay datos disponibles para esta combinación de filtros.")
else:
    fig = px.bar(
        resumen,
        x="OCUAFI.1",
        y="Porcentaje",
        text="PorcentajeTexto",
        hover_data={
            "Total": True,  # muestra la cantidad
            "SalarioPromedio": ":.2f",  # muestra salario promedio con 2 decimales
            "PorcentajeTexto": False,  # oculta el porcentaje en el tooltip
            "Porcentaje": False
        },
        title="Top 15 cargos ocupados por graduados",
    )
    fig.update_layout(
        xaxis_title="Cargo", yaxis_title="Porcentaje de graduados", xaxis_tickangle=-45
    )
    fig.update_traces(textposition="outside")
    st.plotly_chart(fig, use_container_width=True)

# --------------------------
# NOTA
# --------------------------
mostrar_tarjeta_nota(
    texto_principal="""
    <strong>📌 Nota:</strong><br>
    Para cada graduado se toma su registro del mes más reciente de empleo; 
    si en ese mes hay duplicados, se elige el de mayor salario. 
    Esta visualización muestra el porcentaje que cada cargo aporta 
    al total de graduados considerados.
    """,
    nombre_filtro="Trabajo Formal",
    descripcion_filtro="""
    <strong>Relación de Dependencia: </strong>Graduados contratados formalmente por un empleador.<br>
    <strong>Afiliado Voluntario: </strong>Personas autoafiliadas al IESS, como emprendedores o profesionales independientes.<br>
    """,
)
