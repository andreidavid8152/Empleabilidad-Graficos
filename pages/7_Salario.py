import streamlit as st
import plotly.express as px
import pandas as pd
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

aplicar_tema_plotly()
st.title("Distribución de Salarios por Periodo")

# 🌀 Cargar datos
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# ----------------------------------------
# 🚀 PROCESAMIENTO
# ----------------------------------------

# 1. Asegurar que SALARIO.1 sea numérico
df_base["SALARIO.1"] = pd.to_numeric(df_base["SALARIO.1"], errors="coerce")

# 2. Marcar si estuvo alguna vez empleado
df_base["Esta_empleado"] = (
    df_base["SALARIO.1"].notnull() | df_base["RUCEMP.1"].notnull()
)

# 3. Mapear Mes.1 → Quimestre y filtrar
mapa_quimestres = {2: "Q1", 5: "Q2", 9: "Q3", 11: "Q4"}
df_base["Quimestre"] = df_base["Mes.1"].map(mapa_quimestres)
df_base = df_base[df_base["Quimestre"].notnull()]

# 4. Construir Periodo y quedarnos solo con empleados
df_base["Periodo"] = df_base["Anio.1"].astype(str) + " " + df_base["Quimestre"]
df_empleados = df_base[df_base["Esta_empleado"]].copy()

# 5. Agrupar por graduado y trimestre, conservando todas las columnas de filtro
group_cols = [
    "IdentificacionBanner.1",
    "AnioGraduacion.1",
    "regimen.1",
    "Oferta actual",
    "FACULTAD",
    "CarreraHomologada.1",
    "Empleo formal",
    "Anio.1",
    "Quimestre",
    "Periodo",
]
df_quarter = df_empleados.groupby(group_cols, as_index=False)["SALARIO.1"].max()

# ----------------------------------------
# FILTROS
# ----------------------------------------
df_fil, selecciones = aplicar_filtros(
    df_quarter,
    incluir=[
        "Nivel",
        "Oferta Actual",
        "Facultad",
        "Carrera",
        "Cohorte",
        "Trabajo Formal",
    ],
)

# ----------------------------------------
# ORDENAR PERIODOS
# ----------------------------------------
orden_qu = {"Q1": 1, "Q2": 2, "Q3": 3, "Q4": 4}
df_fil["__rank"] = df_fil["Anio.1"].astype(str) + df_fil["Quimestre"].map(
    orden_qu
).astype(str).str.zfill(2)
orden_periodos = df_fil.sort_values("__rank")["Periodo"].drop_duplicates().tolist()
df_fil["Periodo"] = pd.Categorical(
    df_fil["Periodo"], categories=orden_periodos, ordered=True
)

# ----------------------------------------
# 5.1 TARJETA DE INSIGHT: Salario promedio anual
# ----------------------------------------
if not df_fil.empty:
    # calcular promedio de cada trimestre
    quarter_means = df_fil.groupby("Quimestre")["SALARIO.1"].mean()
    # garantizar Q1–Q4 y sacar la media de esos cuatro promedios
    ordered_qs = ["Q1", "Q2", "Q3", "Q4"]
    values = [quarter_means.get(q, 0) for q in ordered_qs]
    mean_salary = sum(values) / len(ordered_qs)

    # construir sujeto según filtros activos
    car = selecciones.get("Carrera")
    fac = selecciones.get("Facultad")
    coh = selecciones.get("Cohorte")

    if car and car != "Todas":
        context = f"los egresados de {car}"
    elif fac and fac != "Todas":
        context = f"los egresados de la facultad {fac}"
    else:
        context = "los egresados"

    if coh and coh != "Todas":
        context = f"{context} de la cohorte {coh}"

    sujeto = f"El salario promedio anual de {context}"
    texto_insight = (
        f"{sujeto} es de <strong>${mean_salary:,.2f}</strong> mensuales")

    st.markdown(
            f"""
    <div style="
        background-color: #fdf0f6;
        border-left: 6px solid #d8b4e2;
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1.5rem;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    ">
        <p style="margin: 0; font-size: 1.05rem;">
            <strong>📊 Insight:</strong><br>{texto_insight}
        </p>
    </div>
    """,
            unsafe_allow_html=True,
        )

# ----------------------------------------
# BOXPLOT Y RESUMEN
# ----------------------------------------
if df_fil.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
else:
    fig = px.box(
        df_fil,
        x="Periodo",
        y="SALARIO.1",
        title="Distribución de Salarios por Trimestre (máximo por graduado)",
        labels={"SALARIO.1": "Salario mensual", "Periodo": "Año-Quimestre"},
        points="outliers",
        category_orders={"Periodo": orden_periodos},
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

# ----------------------------------------
# NOTA INFORMATIVA
# ----------------------------------------
mostrar_tarjeta_nota(
    texto_principal="""
    <strong>📌 Nota:</strong><br>
    Se toma el salario máximo por graduado en cada uno de los cuatro trimestres (febrero, mayo, septiembre, noviembre).<br>
    La tarjeta de insight muestra el salario promedio anual calculado como promedio de los cuatro promedios trimestrales.
    """,
    nombre_filtro="Trabajo Formal",
    descripcion_filtro="""
    <strong>Relación de Dependencia:</strong> Empleo formal con vínculo.<br>
    <strong>Afiliado Voluntario:</strong> Autónomos o emprendedores.<br>
    <strong>Desconocido:</strong> Sin registro laboral formal.
    """,
)