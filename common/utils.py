"""
Utilidades: botón de imprimir y generación de informes PDF (manual, apartado 9.3).

- Imprimir: Streamlit no trae este botón, así que se crea uno en HTML que llama a
  window.print() del navegador. Un poco de CSS oculta el menú y los botones al imprimir.
- PDF: se maqueta con ReportLab. Los gráficos de Plotly no se pueden meter en un PDF
  sin instalar programas extra, así que para el PDF se dibujan con Matplotlib.
"""

from datetime import datetime
from io import BytesIO

import matplotlib

matplotlib.use("Agg")  # dibujar sin pantalla
import matplotlib.pyplot as plt
import streamlit as st
import streamlit.components.v1 as components
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

VERDE = "#1f7a4d"

CSS_IMPRESION = """
<style>
@media print {
    section[data-testid="stSidebar"], header[data-testid="stHeader"],
    div[data-testid="stDownloadButton"], div[data-testid="stButton"], iframe {
        display: none !important;
    }
}
</style>
"""


def grafico_barras(etiquetas, valores, titulo):
    """Gráfico de barras horizontales con Matplotlib (para el PDF)."""
    etiquetas, valores = list(etiquetas), list(valores)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(etiquetas[::-1], valores[::-1], color=VERDE)   # el primero arriba
    ax.set_title(titulo, loc="left", fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    return fig


def generar_pdf(titulo, subtitulo, tabla, figura=None, max_filas=30):
    """Crea un PDF con título, subtítulo, un gráfico opcional y una tabla. Devuelve los bytes."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), title=titulo,
                            leftMargin=1.5 * cm, rightMargin=1.5 * cm,
                            topMargin=1.5 * cm, bottomMargin=1.5 * cm)
    estilos = getSampleStyleSheet()
    elementos = [
        Paragraph(titulo, estilos["Title"]),
        Paragraph(subtitulo, estilos["Normal"]),
        Paragraph(f"Generado el {datetime.now():%d/%m/%Y a las %H:%M}", estilos["Normal"]),
        Spacer(1, 12),
    ]

    if figura is not None:
        imagen = BytesIO()
        figura.savefig(imagen, format="png", dpi=150, bbox_inches="tight")
        plt.close(figura)
        imagen.seek(0)
        elementos += [Image(imagen, width=22 * cm, height=11 * cm), Spacer(1, 12)]

    datos = [list(tabla.columns)] + tabla.head(max_filas).round(2).astype(str).values.tolist()
    t = Table(datos, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(VERDE)),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f5f3")]),
        ("GRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
    ]))
    elementos.append(t)
    if len(tabla) > max_filas:
        elementos.append(Paragraph(f"Se muestran las primeras {max_filas} de {len(tabla)} filas.",
                                   estilos["Italic"]))

    doc.build(elementos)
    return buffer.getvalue()


def boton_imprimir():
    """Botón HTML que abre el diálogo de impresión del navegador."""
    components.html(
        """
        <button onclick="window.parent.print()"
            style="width:100%; height:40px; border-radius:8px; border:1px solid #cdd5df;
                   background:white; font-size:15px; cursor:pointer;">
            🖨️ Imprimir página
        </button>
        """,
        height=48,
    )


def barra_acciones(pdf_bytes, nombre_archivo):
    """Muestra los botones de imprimir y exportar a PDF uno al lado del otro."""
    st.markdown(CSS_IMPRESION, unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    with col1:
        boton_imprimir()
    with col2:
        st.download_button("📄 Exportar a PDF", data=pdf_bytes,
                           file_name=f"{nombre_archivo}_{datetime.now():%Y%m%d_%H%M}.pdf",
                           mime="application/pdf", use_container_width=True, type="primary")