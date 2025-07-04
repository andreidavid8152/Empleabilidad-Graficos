import streamlit as st
import pandas as pd
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

aplicar_tema_plotly()
st.title("🏢 Conexiones con Empresas Clave")

# 🌀 Cargar datos
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# Preprocesamiento
df = df_base.copy()
df["SALARIO.1"] = pd.to_numeric(df["SALARIO.1"], errors="coerce")
df["Empleo formal"] = df["Empleo formal"].astype(str).str.strip().str.upper()
df["NOMEMP.1"] = df["NOMEMP.1"].fillna("SIN EMPRESA")
df["Cantidad de empleados"] = pd.to_numeric(
    df["Cantidad de empleados"], errors="coerce"
).fillna(0)

# --------------------------
# Excluir 'DESCONOCIDO' en Trabajo Formal ANTES de construir filtros
# --------------------------
df = df[df["Empleo formal"] != "DESCONOCIDO"]

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
# FILTROS ADICIONALES
# --------------------------
sector_sel = st.selectbox(
    "Sector Económico", ["Todos"] + sorted(df_fil["SECTOR"].dropna().unique())
)
if sector_sel != "Todos":
    df_fil = df_fil[df_fil["SECTOR"] == sector_sel]

tam_min = int(df_fil["Cantidad de empleados"].min())
tam_max = int(df_fil["Cantidad de empleados"].max())
tamano_rango = st.slider(
    "Tamaño de empresa (Cantidad de empleados)",
    min_value=tam_min,
    max_value=tam_max,
    value=(tam_min, tam_max),
    step=1,
)
df_fil = df_fil[
    (df_fil["Cantidad de empleados"] >= tamano_rango[0])
    & (df_fil["Cantidad de empleados"] <= tamano_rango[1])
]

# --------------------------
# LÓGICA DE ÚNICO POR GRADUADO
# --------------------------
df_emp_unicos = df_fil.sort_values(
    ["IdentificacionBanner.1", "Mes.1", "SALARIO.1"], ascending=[True, False, False]
).drop_duplicates(subset="IdentificacionBanner.1", keep="first")

# --------------------------
# CÁLCULO DEL TOP Y PORCENTAJES
# --------------------------
top_empresas = df_emp_unicos["NOMEMP.1"].value_counts().nlargest(10).reset_index()
top_empresas.columns = ["Empresa", "Contrataciones"]

total_unicos = df_emp_unicos.shape[0]
top_empresas["PorcentajeTexto"] = (
    top_empresas["Contrataciones"] / total_unicos * 100
).round(2).astype(str) + "%"

# --------------------------
# GRÁFICO DE EMPRESAS (con texto en %)
# --------------------------
fig = px.bar(
    top_empresas,
    x="Empresa",
    y="Contrataciones",
    text="PorcentajeTexto",
    title="Top 10 empresas que contratan graduados",
    hover_data={"PorcentajeTexto": False},
)
fig.update_layout(
    yaxis_title="Número de graduados contratados",
    xaxis={"categoryorder": "total descending"},
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
    Las etiquetas en las barras representan el porcentaje que cada empresa 
    aporta al total de graduados considerados. 
    """,
    nombre_filtro="Trabajo Formal",
    descripcion_filtro="""
    <strong>Relación de Dependencia:</strong> Graduados contratados formalmente.<br>
    <strong>Afiliación Voluntaria:</strong> Autoempleo formal.<br>
    """,
)
