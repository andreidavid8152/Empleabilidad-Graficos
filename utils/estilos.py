import plotly.io as pio
import streamlit as st

# Definir la paleta personalizada (rosa y morado pastel)
PALETA_PASTEL = ["#f7c6d9", "#d7bde2"]  # rosa pastel, morado pastel


def aplicar_tema_plotly():
    tema_personalizado = dict(
        layout=dict(
            colorway=PALETA_PASTEL,
            plot_bgcolor="white",
            paper_bgcolor="white",
            font=dict(family="Arial", size=14, color="#333333"),
            title=dict(font=dict(size=20, color="#333333")),
            xaxis=dict(showgrid=True, gridcolor="#eeeeee"),
            yaxis=dict(showgrid=True, gridcolor="#eeeeee"),
        )
    )
    pio.templates["tema_pastel"] = tema_personalizado
    pio.templates.default = "tema_pastel"

def mostrar_tarjeta_nota(texto_principal: str,
                        nombre_filtro: str = None,
                        descripcion_filtro: str = None):
    # Preparo el HTML mínimo, sin indentación en ninguna línea
    partes = [
        '<div style="'
        'background-color: #f9f2fc; '
        'border-left: 6px solid #c084fc; '
        'padding: 1rem; '
        'border-radius: 10px; '
        'box-shadow: 0 4px 6px rgba(0,0,0,0.05); '
        'margin-top: 2rem;'
        '">'
    ]
    # Nota principal (ya viene con sus <strong><br> etc.)
    partes.append(texto_principal)
    # Sección de filtro, si existe
    if nombre_filtro and descripcion_filtro:
        partes.append(
            '<hr style="border:none;border-top:1px solid #ddd;margin:1rem 0;">'
            f'<p><strong>🔎 Filtro: {nombre_filtro}</strong><br>'
            f'{descripcion_filtro}</p>'
        )
    partes.append('</div>')

    html = "".join(partes)
    st.markdown(html, unsafe_allow_html=True)