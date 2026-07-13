"""Generacion de reportes PDF del sistema de riego con ReportLab."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any
import unicodedata

import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import charts
import membership


TITULO_PROYECTO = "Sistema Inteligente para el Riego Automatico mediante Logica Difusa Mamdani"
AUTORES_PREDETERMINADOS = "Jose Alejandro Romero Aguirre"
CARPETA_REPORTES = Path("assets") / "reports"


def _validar_resultado(resultado: dict[str, Any]) -> None:
    """Valida que exista una evaluacion real para generar el reporte."""
    campos = [
        "tiempo_riego",
        "frecuencia_riego",
        "caudal_agua",
        "grados_pertenencia",
        "reglas_activadas",
        "conjuntos_agregados",
        "pasos_matematicos",
        "interpretacion",
    ]
    faltantes = [campo for campo in campos if campo not in resultado]
    if faltantes:
        raise ValueError(f"Resultado incompleto para reporte: {', '.join(faltantes)}")
    if not resultado["reglas_activadas"]:
        raise ValueError("No existen reglas activadas para documentar en el reporte.")


def _crear_ruta_reporte(ruta_salida: Path | None) -> Path:
    """Crea la ruta final con el nombre requerido por el proyecto."""
    nombre = f"reporte_riego_mamdani_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    if ruta_salida is None:
        ruta = CARPETA_REPORTES / nombre
    elif ruta_salida.suffix.lower() == ".pdf":
        ruta = ruta_salida
    else:
        ruta = ruta_salida / nombre
    ruta.parent.mkdir(parents=True, exist_ok=True)
    return ruta


def _estilos() -> dict[str, ParagraphStyle]:
    """Define estilos simples para el reporte academico."""
    estilos_base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle(
            "TituloProyecto",
            parent=estilos_base["Title"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=colors.HexColor("#14532d"),
            alignment=1,
            spaceAfter=12,
        ),
        "subtitulo": ParagraphStyle(
            "Subtitulo",
            parent=estilos_base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#1f6f9f"),
            spaceBefore=8,
            spaceAfter=6,
        ),
        "normal": ParagraphStyle(
            "NormalReporte",
            parent=estilos_base["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            spaceAfter=5,
        ),
        "formula": ParagraphStyle(
            "Formula",
            parent=estilos_base["Code"],
            fontName="Courier",
            fontSize=8,
            leading=10,
            backColor=colors.HexColor("#f8fafc"),
            borderColor=colors.HexColor("#cbd5e1"),
            borderWidth=0.4,
            borderPadding=5,
            spaceAfter=6,
        ),
    }


def _tabla(datos: list[list[Any]], anchos: list[float] | None = None) -> Table:
    """Crea una tabla ReportLab con estilo uniforme."""
    tabla = Table(datos, colWidths=anchos, repeatRows=1)
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8f5ed")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.HexColor("#14532d")),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#cbd5e1")),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 7.2),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )
    return tabla


def _guardar_figura(fig, ruta: Path) -> Path:
    """Guarda una figura Matplotlib para incluirla en el PDF."""
    ruta.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return ruta


def _generar_graficos(
    resultado: dict[str, Any],
    entradas: dict[str, Any],
    carpeta: Path,
) -> list[Path]:
    """Genera graficos de pertenencia y salida agregada para el reporte."""
    graficos: list[Path] = []
    cultivo = str(entradas.get("tipo_cultivo", "tomate"))
    cultivo_normalizado = unicodedata.normalize("NFKD", cultivo).encode("ascii", "ignore").decode("ascii")
    valores_variables = {
        "humedad_suelo": entradas.get("humedad_suelo"),
        "temperatura_ambiental": entradas.get("temperatura"),
        "humedad_ambiental": entradas.get("humedad_ambiental"),
        "velocidad_viento": entradas.get("velocidad_viento"),
        "tipo_cultivo": membership.codificar_cultivo(cultivo_normalizado),
    }

    for nombre_variable, valor in valores_variables.items():
        fig = charts.graficar_variable(nombre_variable, float(valor))
        graficos.append(_guardar_figura(fig, carpeta / f"membresia_{nombre_variable}.png"))

    for nombre_salida in ("tiempo_riego", "frecuencia_riego", "caudal_agua"):
        datos = resultado["conjuntos_agregados"][nombre_salida]
        fig = charts.graficar_salida_agregada(
            nombre_salida=nombre_salida,
            universo=datos["universo"],
            funcion_agregada=datos["membresia"],
            centroide=float(resultado[nombre_salida]),
        )
        graficos.append(_guardar_figura(fig, carpeta / f"agregada_{nombre_salida}.png"))

    return graficos


def _agregar_imagenes(elementos: list[Any], rutas: list[Path], estilos: dict[str, ParagraphStyle]) -> None:
    """Agrega imagenes al documento en tamano compatible con A4."""
    for indice, ruta in enumerate(rutas, start=1):
        elementos.append(Paragraph(f"Grafico {indice}: {ruta.stem.replace('_', ' ')}", estilos["normal"]))
        elementos.append(Image(str(ruta), width=16 * cm, height=8.2 * cm, kind="proportional"))
        elementos.append(Spacer(1, 0.25 * cm))


def _tabla_grados(resultado: dict[str, Any]) -> Table:
    """Crea tabla de grados de pertenencia."""
    filas = [["Variable", "Conjunto", "Grado"]]
    for variable, conjuntos in resultado["grados_pertenencia"].items():
        for conjunto, grado in conjuntos.items():
            filas.append([variable, conjunto, f"{float(grado):.4f}"])
    return _tabla(filas, [5 * cm, 6 * cm, 3 * cm])


def _tabla_reglas(resultado: dict[str, Any]) -> Table:
    """Crea tabla de reglas activadas."""
    filas = [["ID", "Regla linguistica", "Activacion", "Tiempo", "Frecuencia", "Caudal"]]
    for regla in resultado["reglas_activadas"]:
        consecuentes = regla["consecuentes"]
        filas.append(
            [
                regla["id"],
                regla["texto"],
                f"{float(regla['grado_activacion']):.4f}",
                consecuentes["tiempo_riego"],
                consecuentes["frecuencia_riego"],
                consecuentes["caudal_agua"],
            ]
        )
    return _tabla(filas, [1.3 * cm, 8.2 * cm, 2 * cm, 2 * cm, 2 * cm, 2 * cm])


def generar_reporte_pdf(
    resultado: dict[str, Any],
    ruta_salida: Path | None = None,
    entradas: dict[str, Any] | None = None,
    autores: str = AUTORES_PREDETERMINADOS,
) -> Path:
    """Genera un reporte PDF academico con resultados reales del motor Mamdani."""
    _validar_resultado(resultado)
    entradas = entradas or {}
    ruta_pdf = _crear_ruta_reporte(ruta_salida)
    carpeta_graficos = ruta_pdf.parent / f"{ruta_pdf.stem}_graficos"
    estilos = _estilos()

    documento = SimpleDocTemplate(
        str(ruta_pdf),
        pagesize=A4,
        rightMargin=1.5 * cm,
        leftMargin=1.5 * cm,
        topMargin=1.3 * cm,
        bottomMargin=1.3 * cm,
    )
    elementos: list[Any] = []

    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    elementos.append(Paragraph(TITULO_PROYECTO, estilos["titulo"]))
    elementos.append(Paragraph(f"Fecha y hora: {fecha_hora}", estilos["normal"]))
    elementos.append(Paragraph(f"Autores: {autores}", estilos["normal"]))

    elementos.append(Paragraph("Entradas", estilos["subtitulo"]))
    entradas_tabla = [
        ["Variable", "Valor"],
        ["Humedad del suelo", f"{entradas.get('humedad_suelo', 'N/D')} %"],
        ["Temperatura ambiental", f"{entradas.get('temperatura', 'N/D')} C"],
        ["Humedad ambiental", f"{entradas.get('humedad_ambiental', 'N/D')} %"],
        ["Velocidad del viento", f"{entradas.get('velocidad_viento', 'N/D')} km/h"],
        ["Tipo de cultivo", str(entradas.get("tipo_cultivo", "N/D"))],
    ]
    elementos.append(_tabla(entradas_tabla, [7 * cm, 7 * cm]))

    elementos.append(Paragraph("Resultados", estilos["subtitulo"]))
    resultados_tabla = [
        ["Salida", "Valor crisp"],
        ["Tiempo de riego", f"{float(resultado['tiempo_riego']):.4f} minutos"],
        ["Frecuencia de riego", f"{float(resultado['frecuencia_riego']):.4f} dias"],
        ["Caudal de agua", f"{float(resultado['caudal_agua']):.4f} L/min"],
    ]
    elementos.append(_tabla(resultados_tabla, [7 * cm, 7 * cm]))
    elementos.append(Paragraph("Interpretacion", estilos["subtitulo"]))
    elementos.append(Paragraph(str(resultado["interpretacion"]), estilos["normal"]))

    elementos.append(Paragraph("Formulas del sistema Mamdani", estilos["subtitulo"]))
    elementos.append(Paragraph("Fuzzificacion triangular: mu(x;a,b,c)=max(min((x-a)/(b-a),(c-x)/(c-b)),0)", estilos["formula"]))
    elementos.append(Paragraph("Fuzzificacion trapezoidal: mu(x;a,b,c,d)=max(min((x-a)/(b-a),1,(d-x)/(d-c)),0)", estilos["formula"]))
    elementos.append(Paragraph("Inferencia Mamdani: alpha=min(mu1,mu2,...,mun); implicacion mu'_B(z)=min(alpha,mu_B(z))", estilos["formula"]))
    elementos.append(Paragraph("Agregacion: mu_agregada(z)=max(mu'_B1(z),mu'_B2(z),...)", estilos["formula"]))
    elementos.append(Paragraph("Centroide: z*=Sum[z_i*mu(z_i)]/Sum[mu(z_i)]", estilos["formula"]))

    elementos.append(Paragraph("Grados de pertenencia", estilos["subtitulo"]))
    elementos.append(_tabla_grados(resultado))

    elementos.append(Paragraph("Reglas activadas", estilos["subtitulo"]))
    elementos.append(_tabla_reglas(resultado))

    elementos.append(Paragraph("Resultado del centroide", estilos["subtitulo"]))
    elementos.append(
        Paragraph(
            f"Centroide tiempo={float(resultado['tiempo_riego']):.4f}, "
            f"frecuencia={float(resultado['frecuencia_riego']):.4f}, "
            f"caudal={float(resultado['caudal_agua']):.4f}.",
            estilos["normal"],
        )
    )

    elementos.append(PageBreak())
    elementos.append(Paragraph("Graficos de pertenencia y salidas agregadas", estilos["subtitulo"]))
    if entradas:
        rutas_graficos = _generar_graficos(resultado, entradas, carpeta_graficos)
        _agregar_imagenes(elementos, rutas_graficos, estilos)
    else:
        elementos.append(Paragraph("No se recibieron entradas para graficar los valores ingresados.", estilos["normal"]))

    elementos.append(Paragraph("Conclusion breve del escenario", estilos["subtitulo"]))
    regla_principal = max(resultado["reglas_activadas"], key=lambda regla: float(regla["grado_activacion"]))
    elementos.append(
        Paragraph(
            "El escenario evaluado fue procesado mediante fuzzificacion, activacion de reglas, "
            "recorte Mamdani, agregacion por maximo y desfuzzificacion por centroide. "
            f"La regla predominante fue {regla_principal['id']} con activacion "
            f"{float(regla_principal['grado_activacion']):.4f}, lo que sustenta la recomendacion final.",
            estilos["normal"],
        )
    )

    documento.build(elementos)
    return ruta_pdf
