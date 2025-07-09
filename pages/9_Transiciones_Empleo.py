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
st.title("Transiciones de Empleo")

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

    # 6) Calcular transiciones (incluyendo permanencias)
    trans = []

    if seleccion_formal != "Todos":
        for antes, despues, label in [
            ("Feb", "May", "Q1→Q2"),
            ("May", "Sep", "Q2→Q3"),
            ("Sep", "Nov", "Q3→Q4"),
        ]:
            temp = pivot[[antes, despues]].copy()

            # cambios hacia el estado seleccionado
            cambios = temp[
                (temp[despues] == seleccion_formal) & (temp[antes] != seleccion_formal)
            ].copy()
            cambios["Trimestre"] = label
            cambios["Desde"] = cambios[antes]

            # permanencias en el mismo estado
            perm = temp[
                (temp[despues] == seleccion_formal) & (temp[antes] == seleccion_formal)
            ].copy()
            perm["Trimestre"] = label
            perm["Desde"] = "PERMANECE"

            trans.append(pd.concat([cambios, perm])[["Trimestre", "Desde"]])

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

            # cambios entre diferentes estados
            cambios = temp[temp[antes] != temp[despues]].copy()
            cambios["Trimestre"] = label
            cambios["Transición"] = cambios[antes] + " → " + cambios[despues]

            # permanencias (mismo estado)
            perm = temp[temp[antes] == temp[despues]].copy()
            perm["Trimestre"] = label
            perm["Transición"] = perm[antes] + " → " + perm[despues]

            trans.append(pd.concat([cambios, perm])[["Trimestre", "Transición"]])

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
    Esta visualización muestra la dinámica del empleo formal de los graduados entre trimestres del año 2024, incluyendo tanto:
    <ul>
    <li>Los casos donde hubo transición entre estados laborales (por ejemplo, de independiente a empleo con contrato), como</li>
    <li>Aquellos que mantuvieron el mismo estado de un trimestre a otro.</li>
    </ul>
    Cada barra representa los cambios ocurridos entre dos trimestres consecutivos. Está desglosada por tipo de transición.<br>
    Los valores dentro de las barras indican el porcentaje de cada cambio respecto al total de movimientos observados en ese periodo.<br>
    Al pasar el cursor sobre cada sección se muestra la cantidad exacta de graduados involucrados.<br>
    Estados laborales considerados:
    <ul>
    <li><strong>Relación de Dependencia:</strong> empleo formal con contrato.</li>
    <li><strong>Afiliación Voluntaria:</strong> trabajadores independientes afiliados.</li>
    <li><strong>Desconocido:</strong> sin afiliación formal registrada (desempleo, informalidad, inactividad o trabajo fuera del país).</li>
    </ul>
    <strong>¿Cómo interpretar este gráfico?</strong><br>
    Permite identificar qué tan estables son las trayectorias laborales, cuántos egresados entran o salen del empleo formal, y qué rutas laborales son más frecuentes a lo largo del año.
    """,
)
