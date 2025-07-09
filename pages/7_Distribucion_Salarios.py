import streamlit as st
import plotly.express as px
import pandas as pd
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

aplicar_tema_plotly()
st.title("Distribución de Salarios")

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
    # construir mensaje según filtros activos
    fac = selecciones.get("Facultad")
    car = selecciones.get("Carrera")
    coh = selecciones.get("Cohorte")
    detalle = ""
    if (
        coh and coh != "Todas" and coh != "Todos"
    ):  # <- CAMBIO AQUÍ: agregamos coh != "Todos"
        # Cuando está filtrado por cohorte, la cohorte siempre tiene prioridad
        if fac and fac != "Todas" and car and car != "Todas":
            detalle = f"de la cohorte <strong>{coh}</strong> de la Facultad <strong>{fac}</strong> de la carrera <strong>{car}</strong>"
        elif fac and fac != "Todas":
            detalle = f"de la cohorte <strong>{coh}</strong> de la Facultad <strong>{fac}</strong>"
        elif car and car != "Todas":
            detalle = f"de la cohorte <strong>{coh}</strong> de la carrera <strong>{car}</strong>"
        else:
            detalle = f"de la cohorte <strong>{coh}</strong>"
    elif fac and fac != "Todas" and car and car != "Todas":
        detalle = f"de la Facultad <strong>{fac}</strong> de la carrera <strong>{car}</strong>"
    elif fac and fac != "Todas":
        detalle = f"de la Facultad <strong>{fac}</strong>"
    elif car and car != "Todas":
        detalle = f"de la carrera <strong>{car}</strong>"
    else:
        detalle = ""
    texto_insight = (
        f"<strong>📊 El salario</strong> promedio mensual de un graduado "
        f"{detalle + ' ' if detalle else ''}con empleo formal "
        f"<strong>es de ${mean_salary:,.2f}</strong>."
    )
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
                {texto_insight}
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
        title="Distribución de Salarios por Trimestre",
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
    Esta visualización utiliza un <em>boxplot</em> para mostrar la distribución de salarios mensuales por trimestre durante el año 2024.<br>
    <ul>
    <li>La caja representa la concentración de los salarios en el rango central.</li>
    <li>Los outliers (valores atípicos) están señalados como puntos fuera del rango típico.</li>
    <li>Al pasar el mouse por encima de la caja, se pueden consultar estadísticos descriptivos como la media o valores mínimos y máximos.</li>
    </ul>
    Solo se incluyen personas con empleo formal, afiliadas al IESS (ya sea con contrato laboral o por cuenta propia).
    """
)
