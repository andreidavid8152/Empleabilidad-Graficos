import plotly.io as pio

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
