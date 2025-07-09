import streamlit as st
import plotly.express as px
from utils.carga_datos import cargar_datos_empleabilidad
from utils.estilos import aplicar_tema_plotly, mostrar_tarjeta_nota, PALETA_PASTEL
from utils.filtros import aplicar_filtros

aplicar_tema_plotly()
st.title("Ranking de Carreras con más Empleabilidad")

# 🌀 Cargar datos sin procesar
with st.spinner("Cargando datos..."):
    df_base = cargar_datos_empleabilidad()

# Procesamiento específico
df = df_base.copy()
df['Esta_empleado'] = df['SALARIO.1'].notnull() | df['RUCEMP.1'].notnull()

def asignar_quimestre(mes):
    return {2: 'Q1', 5: 'Q2', 9: 'Q3', 11: 'Q4'}.get(mes, None)

df['Quimestre'] = df['Mes.1'].apply(asignar_quimestre)
df = df[df['Quimestre'].notnull()]
df['Periodo'] = df['Anio.1'].astype(str) + ' ' + df['Quimestre']

# --------------------------
# FILTROS
# --------------------------
df_fil, selecciones = aplicar_filtros(
    df,
    incluir=["Nivel", "Oferta Actual", "Facultad", "Cohorte_multi", "Trabajo Formal"]
)

# Obtener cohortes seleccionadas
cohortes_seleccionadas = selecciones.get('Cohorte_multi', [])
if isinstance(cohortes_seleccionadas, list):
    cohortes_seleccionadas = [c for c in cohortes_seleccionadas if c is not None]
else:
    cohortes_seleccionadas = []

# --------------------------
# CÁLCULO DE RANKING POR CARRERA Y COHORTE
# --------------------------
if df_fil.empty:
    st.warning("No hay datos disponibles con los filtros seleccionados.")
else:
    try:
        cohortes = sorted(int(c) for c in cohortes_seleccionadas) if cohortes_seleccionadas else sorted(df_fil["AnioGraduacion.1"].dropna().unique())
    except:
        cohortes = sorted(cohortes_seleccionadas)

    # 1. Denominador: todos los graduados (sin filtro Trabajo Formal)
    df_total = (
        df[df["AnioGraduacion.1"].isin(cohortes)]
        .groupby(["CarreraHomologada.1", "AnioGraduacion.1", "IdentificacionBanner.1"], as_index=False)
        .agg(total_registro=("IdentificacionBanner.1", "count"))
    )

    # 2. Numerador: solo empleados con filtro aplicado
    df_fil_empleados = df_fil[df_fil["Esta_empleado"]]  # ya viene filtrado

    df_empleado = (
        df_fil_empleados
        .groupby(["CarreraHomologada.1", "AnioGraduacion.1", "IdentificacionBanner.1"], as_index=False)
        .agg(esta_empleado=("Esta_empleado", "max"))
    )

    # 3. Unir y calcular tasa
    df_merge = df_total.merge(
        df_empleado,
        on=["CarreraHomologada.1", "AnioGraduacion.1", "IdentificacionBanner.1"],
        how="left"
    )
    df_merge["esta_empleado"] = df_merge["esta_empleado"].fillna(0)

    resumen = (
        df_merge
        .groupby(["CarreraHomologada.1", "AnioGraduacion.1"], as_index=False)
        .agg(
            empleados=("esta_empleado", "sum"),
            total=("IdentificacionBanner.1", "nunique")
        )
    )
    resumen = resumen[resumen["total"] > 0]
    resumen["TasaEmpleabilidad"] = resumen["empleados"] / resumen["total"]

    top_n = 10
    colores = PALETA_PASTEL

    if len(cohortes) > 1:
        for i, coh in enumerate(cohortes):
            df_c = (
                resumen[resumen["AnioGraduacion.1"] == coh]
                .sort_values("TasaEmpleabilidad", ascending=False)
                .head(top_n)
            )
            fig = px.bar(
                df_c,
                x="TasaEmpleabilidad",
                y="CarreraHomologada.1",
                orientation="h",
                title=f"Ranking Cohorte {coh} (Top {top_n})",
                labels={
                    "CarreraHomologada.1": "Carrera",
                    "TasaEmpleabilidad": "Tasa de empleo",
                },
                text="TasaEmpleabilidad",
                hover_data={"empleados": True, "total": True, "TasaEmpleabilidad": ":.2%"},
                color_discrete_sequence=[colores[i % len(colores)]],
            )
            fig.update_traces(texttemplate="%{text:.1%}", textposition="outside")
            fig.update_yaxes(autorange="reversed", automargin=True, title_text="Carrera")
            fig.update_xaxes(title_text="Tasa de empleo", tickformat=".0%")
            fig.update_layout(margin=dict(t=60, r=20, l=20))
            st.plotly_chart(fig, use_container_width=True, key=f"ranking_coh_{coh}")

        # Combinado
        resumen_comb = (
            resumen
            .groupby("CarreraHomologada.1", as_index=False)
            .agg(
                empleados=("empleados", "sum"),
                total=("total", "sum")
            )
        )
        resumen_comb = resumen_comb[resumen_comb["total"] > 0]
        resumen_comb["TasaEmpleabilidad"] = resumen_comb["empleados"] / resumen_comb["total"]
        resumen_comb = (
            resumen_comb
            .sort_values("TasaEmpleabilidad", ascending=False)
            .head(top_n)
        )

        fig_comb = px.bar(
            resumen_comb,
            x="TasaEmpleabilidad",
            y="CarreraHomologada.1",
            orientation="h",
            title=f"Ranking Combinado Cohortes {', '.join(map(str, cohortes))} (Top {top_n})",
            labels={
                "CarreraHomologada.1": "Carrera",
                "TasaEmpleabilidad": "Tasa de empleo",
            },
            text="TasaEmpleabilidad",
            hover_data={"empleados": True, "total": True, "TasaEmpleabilidad": ":.2%"},
            color_discrete_sequence=[colores[len(cohortes) % len(colores)]],
        )
        fig_comb.update_traces(texttemplate="%{text:.1%}", textposition="outside")
        fig_comb.update_yaxes(autorange="reversed", automargin=True, title_text="Carrera")
        fig_comb.update_xaxes(title_text="Tasa de empleo", tickformat=".0%")
        fig_comb.update_layout(margin=dict(t=80, r=20, l=20))
        st.plotly_chart(fig_comb, use_container_width=True, key="ranking_combined")

    else:
        ranking = (
            resumen
            .sort_values("TasaEmpleabilidad", ascending=False)
            .head(top_n)
        )

        fig = px.bar(
            ranking,
            x="TasaEmpleabilidad",
            y="CarreraHomologada.1",
            orientation="h",
            title=f"Ranking de Carreras por Empleabilidad (Top {top_n})",
            labels={
                "CarreraHomologada.1": "Carrera",
                "TasaEmpleabilidad": "Tasa de empleo",
            },
            text="TasaEmpleabilidad",
            hover_data={"empleados": True, "total": True, "TasaEmpleabilidad": ":.2%"},
            color_discrete_sequence=[PALETA_PASTEL[0]],
        )
        fig.update_traces(texttemplate="%{text:.1%}", textposition="outside")
        fig.update_yaxes(autorange="reversed", automargin=True, title_text="Carrera")
        fig.update_xaxes(title_text="Tasa de empleo", tickformat=".0%")
        fig.update_layout(margin=dict(t=60, r=20, l=20), showlegend=False)
        st.plotly_chart(fig, use_container_width=True, key="ranking_simple_top10")

# --------------------------
# NOTA
# --------------------------
mostrar_tarjeta_nota(
    texto_principal="""
    <strong>📌 Nota:</strong><br>
    Esta visualización muestra el ranking de carreras según el porcentaje de graduados con empleo formal, considerando a las promociones de 2023 y 2024.<br><br>
    Se toma en cuenta a todos los graduados de cada carrera y se calcula qué porcentaje de ellos tiene un empleo formal, según los criterios definidos más abajo.<br><br>
    <strong>¿Qué se considera empleo formal?</strong><br>
    Se incluye a quienes:<br>
    <ul>
    <li><strong>Trabajan con contrato</strong>, registrados por un empleador en el IESS.</li>
    <li><strong>Están afiliados por cuenta propia</strong> al IESS, como trabajadores independientes, emprendedores o profesionales autónomos.</li>
    </ul>
    <strong>¿Y los que no se consideran empleados formales?</strong><br>
    Aquellos que no tienen registro en el sistema de seguridad social. Esto puede incluir personas desempleadas, inactivas, trabajando fuera del país o en el sector informal.<br><br>
    <strong>¿Cómo interpretar este ranking?</strong><br>
    Las carreras que aparecen en los primeros lugares son aquellas donde una mayor proporción de graduados ha logrado insertarse en el empleo formal. Las que tienen 0% no muestran registros formales de empleo para estas cohortes en 2024.
    """
)
