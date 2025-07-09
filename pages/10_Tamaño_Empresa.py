import streamlit as st
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros

aplicar_tema_plotly()
st.title("Distribución de Graduados por el Tamaño de la Empresa")

# 🌀 Cargar datos
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# —————————————————————————————
# Preprocesamiento
# —————————————————————————————
df = df_base.copy()
df["Esta_empleado"] = df["SALARIO.1"].notnull() | df["RUCEMP.1"].notnull()
df = df[df["Esta_empleado"] & df["Cantidad de empleados"].notnull()]


# Clasificación por tamaño de empresa
def clasificar_tamano(n):
    if n <= 10:
        return "Microempresa (1–10)"
    elif n <= 50:
        return "Pequeña (11–50)"
    elif n <= 200:
        return "Mediana (51–200)"
    else:
        return "Grande (200+)"


df["Tamaño Empresa"] = df["Cantidad de empleados"].apply(clasificar_tamano)

# Mapeo de meses a trimestres
df["Trimestre"] = df["Mes.1"].map({2: "Q1", 5: "Q2", 9: "Q3", 11: "Q4"})

# —————————————————————————————
# FILTROS (sin Trimestre en aplicar_filtros)
# —————————————————————————————
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

# —————————————————————————————
# Filtro manual de Trimestre
# —————————————————————————————
opciones_trimestre = ["Todos", "Q1", "Q2", "Q3", "Q4"]
trimestre_sel = st.selectbox(
    "Trimestre",
    opciones_trimestre,
    index=(
        0
        if "Trimestre" not in selecciones
        else opciones_trimestre.index(selecciones["Trimestre"])
    ),
)
if trimestre_sel != "Todos":
    df_fil = df_fil[df_fil["Trimestre"] == trimestre_sel]

# —————————————————————————————
# Cálculo de empleados únicos y porcentajes
# —————————————————————————————
if df_fil.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
else:
    # Reducir a un registro por graduado
    df_emp_unicos = df_fil.sort_values(
        ["IdentificacionBanner.1", "Mes.1", "SALARIO.1"],
        ascending=[True, False, False],
    ).drop_duplicates(subset="IdentificacionBanner.1", keep="first")

    # Conteo absoluto por tamaño de empresa
    conteo = (
        df_emp_unicos["Tamaño Empresa"]
        .value_counts()
        .reindex(
            [
                "Microempresa (1–10)",
                "Pequeña (11–50)",
                "Mediana (51–200)",
                "Grande (200+)",
            ]
        )
        .dropna()
        .reset_index()
    )
    conteo.columns = ["Tamaño Empresa", "Número de Graduados"]

    # Porcentaje sobre total de graduados únicos
    total_unicos = df_emp_unicos["IdentificacionBanner.1"].nunique()
    conteo["PorcentajeTexto"] = (
        conteo["Número de Graduados"] / total_unicos * 100
    ).round(2).astype(str) + "%"

    # —————————————————————————————
    # Insight card dinámico
    # —————————————————————————————
    top_row = conteo.loc[conteo["Número de Graduados"].idxmax()]
    tipo_raw = top_row["Tamaño Empresa"].split(" (")[
        0
    ]  # "Microempresa", "Pequeña", etc.
    num_graduados_top = int(top_row["Número de Graduados"])
    tipo_lower = tipo_raw.lower()

    # Frase adicional según la categoría principal
    if tipo_raw == "Grande":
        frase_extra = (
            "Aunque las grandes empresas lideran, también hay presencia "
            "relevante en otros tamaños."
        )
    elif tipo_raw == "Microempresa":
        frase_extra = (
            "A pesar de su predominio, muchos graduados también se desempeñan "
            "en empresas de mayor tamaño."
        )
    elif tipo_raw == "Pequeña":
        frase_extra = (
            "Las pequeñas empresas destacan como principal empleador, "
            "aunque no son la única opción."
        )
    elif tipo_raw == "Mediana":
        frase_extra = (
            "Las empresas medianas son la opción dominante, "
            "pero existe reparto significativo en extremos."
        )
    else:
        frase_extra = ""

    texto_insight = (
        f"📊<strong>{num_graduados_top} de cada {total_unicos} graduados</strong> con empleo formal "
        f"trabaja en {tipo_lower}. {frase_extra}"
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

    # —————————————————————————————
    # Gráfico de barras
    # —————————————————————————————
    fig = px.bar(
        conteo,
        x="Tamaño Empresa",
        y="Número de Graduados",
        color="Tamaño Empresa",
        text="PorcentajeTexto",
        hover_data={"Número de Graduados": True, "PorcentajeTexto": False},
        title="Distribución de Graduados por Tamaño de Empresa",
    )
    fig.update_layout(
        xaxis={
            "categoryorder": "array",
            "categoryarray": [
                "Microempresa (1–10)",
                "Pequeña (11–50)",
                "Mediana (51–200)",
                "Grande (200+)",
            ],
        },
        showlegend=False,
        yaxis_title="Número de Graduados",
    )
    fig.update_traces(textposition="inside")
    st.plotly_chart(fig, use_container_width=True)

# —————————————————————————————
# Nota explicativa
# —————————————————————————————
mostrar_tarjeta_nota(
    texto_principal="""
    <strong>📌 Nota aclaratoria:</strong><br>
    Esta visualización muestra la distribución de graduados con empleo formal según el tamaño de la empresa en la que están trabajando, clasificada por número de trabajadores registrados:<br>
    <ul>
      <li><strong>Microempresa:</strong> 1 a 10 afiliados</li>
      <li><strong>Pequeña empresa:</strong> 11 a 50 afiliados</li>
      <li><strong>Mediana empresa:</strong> 51 a 200 afiliados</li>
      <li><strong>Gran empresa:</strong> más de 200 afiliados</li>
    </ul>
    Los porcentajes en las barras indican la proporción de graduados que trabajan en empresas de cada tamaño.
    """
)
