import streamlit as st
import pandas as pd
import plotly.express as px
import unicodedata
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota
from utils.filtros import aplicar_filtros


def quitar_acentos(s: str) -> str:
    return "".join(
        c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c)
    )


aplicar_tema_plotly()
st.title("🔄 Transiciones de Empleo por Trimestre")

# 🌀 1) Cargar datos
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# —————————————————————————————
# 2) Preprocesamiento
# —————————————————————————————
df = df_base.copy()
df["SALARIO.1"] = pd.to_numeric(df["SALARIO.1"], errors="coerce")

meses_validos = [2, 5, 9, 11]
df = df[df["Mes.1"].isin(meses_validos)]

df = df.sort_values(
    ["IdentificacionBanner.1", "Mes.1", "SALARIO.1"], ascending=[True, True, False]
).drop_duplicates(subset=["IdentificacionBanner.1", "Mes.1"], keep="first")

df["Empleo formal"] = (
    df["Empleo formal"]
    .astype(str)
    .str.strip()
    .apply(quitar_acentos)
    .str.upper()
    .replace({"SIN RELACION DE DEPENDENCIA": "AFILIACION VOLUNTARIA"})
)
df["Empleo formal"] = df["Empleo formal"].where(
    df["Empleo formal"].isin(
        ["DESCONOCIDO", "AFILIACION VOLUNTARIA", "RELACION DE DEPENDENCIA"]
    ),
    "DESCONOCIDO",
)

# —————————————————————————————
# 3) FILTROS (sin Trabajo Formal)
# —————————————————————————————
df_fil, selecciones = aplicar_filtros(
    df, incluir=["Nivel", "Oferta Actual", "Facultad", "Carrera", "Cohorte"]
)

# —————————————————————————————
# 4) SELECTBOX manual para Trabajo Formal
# —————————————————————————————
opc_formal = [
    "Todos",
    "DESCONOCIDO",
    "AFILIACION VOLUNTARIA",
    "RELACION DE DEPENDENCIA",
]
seleccion_formal = st.selectbox("Trabajo Formal", opc_formal, index=0)

# —————————————————————————————
# 5) Pivot: uno por graduado y trimestre
# —————————————————————————————
if df_fil.empty:
    st.warning("No hay datos disponibles con esos filtros.")
else:
    pivot = df_fil.pivot(
        index="IdentificacionBanner.1", columns="Mes.1", values="Empleo formal"
    )[meses_validos].fillna("DESCONOCIDO")
    pivot.columns = ["Feb", "May", "Sep", "Nov"]

    # —————————————————————————————
    # 6) Calcular transiciones
    # —————————————————————————————
    trans = []
    if seleccion_formal != "Todos":
        for antes, despues, label in [
            ("Feb", "May", "Q1→Q2"),
            ("May", "Sep", "Q2→Q3"),
            ("Sep", "Nov", "Q3→Q4"),
        ]:
            temp = pivot[[antes, despues]].copy()
            temp = temp[temp[despues] == seleccion_formal]
            temp = temp[temp[antes] != seleccion_formal]
            temp["Trimestre"] = label
            temp["Desde"] = temp[antes]
            trans.append(temp[["Trimestre", "Desde"]])
        df_trans = pd.concat(trans, ignore_index=True)
        conteo = (
            df_trans.groupby(["Trimestre", "Desde"]).size().reset_index(name="Cantidad")
        )
    else:
        for antes, despues, label in [
            ("Feb", "May", "Q1→Q2"),
            ("May", "Sep", "Q2→Q3"),
            ("Sep", "Nov", "Q3→Q4"),
        ]:
            temp = pivot[[antes, despues]].copy()
            temp = temp[temp[antes] != temp[despues]]
            temp["Trimestre"] = label
            temp["Transición"] = temp[antes] + " → " + temp[despues]
            trans.append(temp[["Trimestre", "Transición"]])
        df_trans = pd.concat(trans, ignore_index=True)
        conteo = (
            df_trans.groupby(["Trimestre", "Transición"])
            .size()
            .reset_index(name="Cantidad")
        )

    # —————————————————————————————
    # 7) Calcular porcentaje por trimestre
    # —————————————————————————————
    total_por_trim = conteo.groupby("Trimestre")["Cantidad"].transform("sum")
    conteo["PorcentajeTexto"] = (conteo["Cantidad"] / total_por_trim * 100).round(
        2
    ).astype(str) + "%"

    # —————————————————————————————
    # 8) Graficar con porcentaje en la barra, tooltip con COUNT
    # —————————————————————————————
    if seleccion_formal != "Todos":
        fig = px.bar(
            conteo,
            x="Trimestre",
            y="Cantidad",
            color="Desde",
            text="PorcentajeTexto",
            hover_data={"Cantidad": True, "Desde": True, "PorcentajeTexto": False},
            title=f"Transiciones → {seleccion_formal} por trimestre",
        )
    else:
        fig = px.bar(
            conteo,
            x="Trimestre",
            y="Cantidad",
            color="Transición",
            text="PorcentajeTexto",
            hover_data={"Cantidad": True, "Transición": True, "PorcentajeTexto": False},
            title="Transiciones de empleo por trimestre (solo cambios)",
        )

    fig.update_layout(
        barmode="stack", xaxis_title="Trimestre", yaxis_title="Número de graduados"
    )
    fig.update_traces(textposition="inside")
    st.plotly_chart(fig, use_container_width=True)

# —————————————————————————————
# 9) Nota
# —————————————————————————————
mostrar_tarjeta_nota(
    texto_principal="""
    <strong>📌 Nota:</strong><br>
    Ahora los números dentro de las barras son porcentajes
    (por trimestre), y el tooltip muestra la cuenta absoluta.
    """,
    nombre_filtro="Trabajo Formal",
    descripcion_filtro="""
    <strong>Relación de Dependencia:</strong> Empleo formal bajo contrato.<br>
    <strong>Afiliación Voluntaria:</strong> Independientes/emprendedores en IESS.<br>
    <strong>Desconocido:</strong> Sin registro formal en ese trimestre.
    """,
)
