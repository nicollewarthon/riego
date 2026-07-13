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
from reportlab.pdfgen import canvas
from reportlab.platypus import Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

import charts
import membership


TITULO_PROYECTO = "Sistema Inteligente para el Riego Automatico mediante Logica Difusa Mamdani"
AUTORES_PREDETERMINADOS = "Grupo X"
CARPETA_REPORTES = Path("assets") / "reports"
RUTA_LOGO = Path("assets") / "logo.png"


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
    """Define estilos para el reporte tecnico institucional."""
    estilos_base = getSampleStyleSheet()
    return {
        "titulo": ParagraphStyle(
            "TituloProyecto",
            parent=estilos_base["Title"],
            fontName="Helvetica-Bold",
            fontSize=18,
            leading=23,
            textColor=colors.HexColor("#14532d"),
            alignment=1,
            spaceAfter=12,
        ),
        "portada_subtitulo": ParagraphStyle(
            "PortadaSubtitulo",
            parent=estilos_base["Heading2"],
            fontName="Helvetica",
            fontSize=13,
            leading=17,
            textColor=colors.HexColor("#1f6f9f"),
            alignment=1,
            spaceAfter=18,
        ),
        "subtitulo": ParagraphStyle(
            "Subtitulo",
            parent=estilos_base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=13,
            leading=16,
            textColor=colors.HexColor("#14532d"),
            spaceBefore=14,
            spaceAfter=8,
        ),
        "normal": ParagraphStyle(
            "NormalReporte",
            parent=estilos_base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13.5,
            textColor=colors.HexColor("#334155"),
            spaceAfter=7,
        ),
        "formula": ParagraphStyle(
            "Formula",
            parent=estilos_base["BodyText"],
            fontName="Helvetica",
            fontSize=11,
            leading=16,
            alignment=1,
            textColor=colors.HexColor("#0f172a"),
            backColor=colors.HexColor("#f8fafc"),
            borderColor=colors.HexColor("#dbe7e1"),
            borderWidth=0.5,
            borderPadding=7,
            spaceAfter=9,
        ),
        "card_titulo": ParagraphStyle(
            "CardTitulo",
            parent=estilos_base["Heading3"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=colors.HexColor("#12372a"),
            spaceAfter=5,
        ),
        "pequeno": ParagraphStyle(
            "Pequeno",
            parent=estilos_base["BodyText"],
            fontName="Helvetica",
            fontSize=8,
            leading=10,
            textColor=colors.HexColor("#64748b"),
            spaceAfter=3,
        ),
    }


class _CanvasNumerado(canvas.Canvas):
    """Canvas de dos pasadas para imprimir Pagina X de Y."""

    def __init__(self, *args: Any, fecha_hora: str = "", autores: str = "", **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._estados_paginas: list[dict[str, Any]] = []
        self.fecha_hora = fecha_hora
        self.autores = autores

    def showPage(self) -> None:  # noqa: N802 - API de ReportLab
        self._estados_paginas.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        total_paginas = len(self._estados_paginas)
        for estado in self._estados_paginas:
            self.__dict__.update(estado)
            self._dibujar_encabezado_pie(total_paginas)
            canvas.Canvas.showPage(self)
        canvas.Canvas.save(self)

    def _dibujar_encabezado_pie(self, total_paginas: int) -> None:
        numero = self._pageNumber
        if numero == 1:
            return
        ancho, alto = A4
        verde = colors.HexColor("#14532d")
        gris = colors.HexColor("#64748b")
        self.saveState()
        self.setStrokeColor(colors.HexColor("#dbe7e1"))
        self.setLineWidth(0.6)
        self.line(1.5 * cm, alto - 1.05 * cm, ancho - 1.5 * cm, alto - 1.05 * cm)
        self.setFont("Helvetica-Bold", 8.5)
        self.setFillColor(verde)
        self.drawString(1.5 * cm, alto - 0.78 * cm, "Sistema Inteligente de Riego mediante Logica Difusa Mamdani")
        self.line(1.5 * cm, 1.05 * cm, ancho - 1.5 * cm, 1.05 * cm)
        self.setFont("Helvetica", 8)
        self.setFillColor(gris)
        self.drawString(1.5 * cm, 0.72 * cm, self.autores)
        self.drawCentredString(ancho / 2, 0.72 * cm, f"Pagina {numero} de {total_paginas}")
        self.drawRightString(ancho - 1.5 * cm, 0.72 * cm, self.fecha_hora)
        self.restoreState()


def _tabla(datos: list[list[Any]], anchos: list[float] | None = None) -> Table:
    """Crea una tabla ReportLab con estilo uniforme."""
    estilo_celda = ParagraphStyle(
        "CeldaTabla",
        fontName="Helvetica",
        fontSize=7.4,
        leading=9.3,
        textColor=colors.HexColor("#334155"),
    )
    estilo_encabezado = ParagraphStyle(
        "EncabezadoTabla",
        parent=estilo_celda,
        fontName="Helvetica-Bold",
        textColor=colors.HexColor("#14532d"),
    )
    datos_procesados: list[list[Any]] = []
    for indice_fila, fila in enumerate(datos):
        fila_procesada = []
        for celda in fila:
            if isinstance(celda, str):
                estilo = estilo_encabezado if indice_fila == 0 else estilo_celda
                fila_procesada.append(Paragraph(celda, estilo))
            else:
                fila_procesada.append(celda)
        datos_procesados.append(fila_procesada)

    tabla = Table(datos_procesados, colWidths=anchos, repeatRows=1)
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


def _seccion(elementos: list[Any], titulo: str, descripcion: str, estilos: dict[str, ParagraphStyle]) -> None:
    """Agrega un titulo de seccion con explicacion breve."""
    elementos.append(Paragraph(titulo, estilos["subtitulo"]))
    elementos.append(Paragraph(descripcion, estilos["normal"]))


def _tarjeta(contenido: list[Any], ancho: float = 17.0 * cm, fondo: str = "#ffffff") -> Table:
    """Crea una tarjeta de ancho completo para evitar tablas comprimidas."""
    tabla = Table([[contenido]], colWidths=[ancho])
    tabla.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(fondo)),
                ("BOX", (0, 0), (-1, -1), 0.45, colors.HexColor("#dbe7e1")),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 9),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )
    return tabla


def _agregar_portada(
    elementos: list[Any],
    fecha_hora: str,
    autores: str,
    estilos: dict[str, ParagraphStyle],
) -> None:
    """Agrega una portada institucional limpia."""
    elementos.append(Spacer(1, 1.2 * cm))
    if RUTA_LOGO.exists():
        elementos.append(Image(str(RUTA_LOGO), width=3.0 * cm, height=3.0 * cm, kind="proportional"))
        elementos[-1].hAlign = "CENTER"
        elementos.append(Spacer(1, 0.5 * cm))
    elementos.append(Paragraph(TITULO_PROYECTO, estilos["titulo"]))
    elementos.append(Paragraph("Reporte Tecnico de Evaluacion del Sistema", estilos["portada_subtitulo"]))
    linea = Table([[""]], colWidths=[13 * cm], rowHeights=[0.08 * cm])
    linea.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#14532d"))]))
    linea.hAlign = "CENTER"
    elementos.append(linea)
    elementos.append(Spacer(1, 1.0 * cm))
    datos = [
        ["Autor", autores],
        ["Fecha y hora de generacion", fecha_hora],
        ["Universidad", "Universidad Cesar Vallejo"],
        ["Escuela Profesional", "Ingenieria de Sistemas"],
    ]
    elementos.append(_tabla(datos, [6 * cm, 9 * cm]))
    elementos.append(Spacer(1, 6.5 * cm))
    elementos.append(Paragraph("Sistema Inteligente de Apoyo al Riego", estilos["portada_subtitulo"]))
    elementos.append(PageBreak())


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
    """Crea tabla de grados de pertenencia resaltando valores activos."""
    filas = [["Variable", "Conjunto", "Grado"]]
    estilos_filas = []
    indice = 1
    for variable, conjuntos in resultado["grados_pertenencia"].items():
        for conjunto, grado in conjuntos.items():
            grado_float = float(grado)
            filas.append([variable, conjunto, f"{grado_float:.4f}"])
            if grado_float > 0:
                estilos_filas.extend(
                    [
                        ("BACKGROUND", (0, indice), (-1, indice), colors.HexColor("#ecfdf5")),
                        ("TEXTCOLOR", (0, indice), (-1, indice), colors.HexColor("#14532d")),
                        ("FONTNAME", (0, indice), (-1, indice), "Helvetica-Bold"),
                    ]
                )
            else:
                estilos_filas.extend(
                    [
                        ("BACKGROUND", (0, indice), (-1, indice), colors.HexColor("#f8fafc")),
                        ("TEXTCOLOR", (0, indice), (-1, indice), colors.HexColor("#94a3b8")),
                    ]
                )
            indice += 1
    tabla = _tabla(filas, [5 * cm, 6 * cm, 3 * cm])
    tabla.setStyle(TableStyle(estilos_filas))
    return tabla


def _agregar_tarjetas_reglas(
    elementos: list[Any],
    resultado: dict[str, Any],
    estilos: dict[str, ParagraphStyle],
) -> None:
    """Agrega cada regla activada como tarjeta independiente."""
    for regla in resultado["reglas_activadas"]:
        consecuentes = regla["consecuentes"]
        contenido = [
            Paragraph(f"Regla {regla['id']}", estilos["card_titulo"]),
            Paragraph("<b>Condicion</b>", estilos["normal"]),
            Paragraph(str(regla["texto"]).split(" ENTONCES ")[0], estilos["normal"]),
            Paragraph("<b>ENTONCES</b>", estilos["normal"]),
            Paragraph(
                f"Tiempo de riego -> {consecuentes['tiempo_riego']}<br/>"
                f"Frecuencia -> {consecuentes['frecuencia_riego']}<br/>"
                f"Caudal -> {consecuentes['caudal_agua']}",
                estilos["normal"],
            ),
            Paragraph("<b>Grado de activacion</b>", estilos["normal"]),
            Paragraph(f"{float(regla['grado_activacion']):.4f}", estilos["formula"]),
            Paragraph("<b>Interpretacion</b>", estilos["normal"]),
            Paragraph(str(regla["explicacion"]), estilos["normal"]),
        ]
        elementos.append(KeepTogether([_tarjeta(contenido), Spacer(1, 0.25 * cm)]))


def _agregar_formulas_mamdani(elementos: list[Any], estilos: dict[str, ParagraphStyle]) -> None:
    """Agrega formulas limpias y explicaciones sin sintaxis de codigo."""
    _seccion(
        elementos,
        "Formulas del Sistema Mamdani",
        "Esta seccion resume las etapas matematicas del sistema en lenguaje tecnico pero legible. "
        "Las ecuaciones representan el proceso usado por el motor difuso para transformar entradas "
        "en recomendaciones de riego.",
        estilos,
    )
    bloques = [
        (
            "Fuzzificacion",
            "En esta etapa el sistema determina el grado de pertenencia de cada variable de entrada "
            "a sus conjuntos linguisticos.",
            "&mu;<sub>triangular</sub>(x) = { (x-a) / (b-a) } o { (c-x) / (c-b) } segun el tramo",
            "x es el valor medido; a, b y c definen el inicio, centro y fin de la funcion triangular.",
        ),
        (
            "Funcion trapezoidal",
            "Se utiliza en conjuntos extremos para representar zonas de saturacion baja o alta.",
            "&mu;<sub>trapezoidal</sub>(x) = { (x-a) / (b-a) }, 1, o { (d-x) / (d-c) } segun el tramo",
            "a y d delimitan el soporte; b y c delimitan la zona donde la pertenencia es maxima.",
        ),
        (
            "Inferencia Mamdani",
            "Para reglas tipo AND se utiliza el operador minimo.",
            "&alpha; = min(&mu;<sub>1</sub>, &mu;<sub>2</sub>, ..., &mu;<sub>n</sub>)",
            "El grado de activacion de una regla corresponde al menor grado de pertenencia de sus antecedentes.",
        ),
        (
            "Agregacion",
            "Todas las reglas activadas se unen mediante el operador maximo para formar una sola salida difusa.",
            "&mu;<sub>agregada</sub>(z) = max(&mu;'<sub>1</sub>(z), &mu;'<sub>2</sub>(z), ..., &mu;'<sub>n</sub>(z))",
            "Cada termino representa una funcion consecuente recortada por una regla activa.",
        ),
        (
            "Desfuzzificacion",
            "Despues de combinar las reglas, el sistema obtiene un unico valor numerico con el centroide.",
            "z* = &Sigma;(z<sub>i</sub> &middot; &mu;(z<sub>i</sub>)) / &Sigma;&mu;(z<sub>i</sub>)",
            "El resultado es el punto de equilibrio del area difusa agregada.",
        ),
    ]
    for titulo, texto, formula, explicacion in bloques:
        contenido = [
            Paragraph(titulo, estilos["card_titulo"]),
            Paragraph(texto, estilos["normal"]),
            Paragraph(formula, estilos["formula"]),
            Paragraph(explicacion, estilos["normal"]),
        ]
        elementos.append(_tarjeta(contenido, fondo="#f8fafc"))
        elementos.append(Spacer(1, 0.25 * cm))


def _agregar_recomendacion_final(
    elementos: list[Any],
    resultado: dict[str, Any],
    estilos: dict[str, ParagraphStyle],
) -> None:
    """Agrega tarjeta final con la recomendacion principal."""
    tiempo = float(resultado["tiempo_riego"])
    frecuencia = float(resultado["frecuencia_riego"])
    caudal = float(resultado["caudal_agua"])
    tabla = _tabla(
        [
            ["Salida", "Recomendacion"],
            ["Tiempo de riego", f"{tiempo:.2f} minutos"],
            ["Frecuencia", f"{frecuencia:.2f} dias"],
            ["Caudal", f"{caudal:.2f} L/min"],
        ],
        [7 * cm, 8 * cm],
    )
    contenido = [
        Paragraph("RECOMENDACION FINAL DEL SISTEMA", estilos["card_titulo"]),
        tabla,
        Paragraph(
            f"De acuerdo con las condiciones actuales del cultivo, el sistema recomienda realizar "
            f"un riego durante {tiempo:.2f} minutos, repetirlo cada {frecuencia:.2f} dias y "
            f"utilizar un caudal aproximado de {caudal:.2f} L/min. Esta recomendacion fue obtenida "
            "mediante el proceso de inferencia difusa Mamdani.",
            estilos["normal"],
        )
    ]
    elementos.append(_tarjeta(contenido, fondo="#ecfdf5"))


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
        topMargin=1.8 * cm,
        bottomMargin=1.6 * cm,
    )
    elementos: list[Any] = []

    fecha_hora = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    _agregar_portada(elementos, fecha_hora, autores, estilos)

    _seccion(
        elementos,
        "Entradas",
        "Estas son las condiciones evaluadas por el sistema antes de iniciar el proceso de inferencia difusa.",
        estilos,
    )
    entradas_tabla = [
        ["Variable", "Valor"],
        ["Humedad del suelo", f"{entradas.get('humedad_suelo', 'N/D')} %"],
        ["Temperatura ambiental", f"{entradas.get('temperatura', 'N/D')} C"],
        ["Humedad ambiental", f"{entradas.get('humedad_ambiental', 'N/D')} %"],
        ["Velocidad del viento", f"{entradas.get('velocidad_viento', 'N/D')} km/h"],
        ["Tipo de cultivo", str(entradas.get("tipo_cultivo", "N/D"))],
    ]
    elementos.append(_tabla(entradas_tabla, [7 * cm, 7 * cm]))
    elementos.append(Spacer(1, 0.25 * cm))

    _seccion(
        elementos,
        "Resultados",
        "El motor Mamdani produce tres salidas numericas que representan la recomendacion de riego.",
        estilos,
    )
    resultados_tabla = [
        ["Salida", "Valor crisp"],
        ["Tiempo de riego", f"{float(resultado['tiempo_riego']):.4f} minutos"],
        ["Frecuencia de riego", f"{float(resultado['frecuencia_riego']):.4f} dias"],
        ["Caudal de agua", f"{float(resultado['caudal_agua']):.4f} L/min"],
    ]
    elementos.append(_tabla(resultados_tabla, [7 * cm, 7 * cm]))
    elementos.append(Spacer(1, 0.25 * cm))

    _seccion(
        elementos,
        "Interpretacion",
        "La siguiente lectura resume la recomendacion emitida por el sistema inteligente.",
        estilos,
    )
    elementos.append(Paragraph(str(resultado["interpretacion"]), estilos["normal"]))

    elementos.append(PageBreak())
    _agregar_formulas_mamdani(elementos, estilos)

    _seccion(
        elementos,
        "Grados de pertenencia",
        "En esta etapa el sistema determina que tan representativa es cada condicion de entrada "
        "respecto a sus conjuntos linguisticos. Los valores activos se resaltan en verde.",
        estilos,
    )
    elementos.append(_tabla_grados(resultado))
    elementos.append(Spacer(1, 0.3 * cm))

    elementos.append(PageBreak())
    _seccion(
        elementos,
        "Reglas activadas",
        "Solo se muestran las reglas cuya activacion fue mayor que cero. Cada tarjeta indica "
        "la condicion, los consecuentes, el grado de activacion y una interpretacion breve.",
        estilos,
    )
    _agregar_tarjetas_reglas(elementos, resultado, estilos)

    _seccion(
        elementos,
        "Resultado del centroide",
        "Despues de combinar todas las reglas activadas, el sistema obtiene un unico valor numerico "
        "para cada salida mediante el metodo del centroide.",
        estilos,
    )
    elementos.append(
        Paragraph(
            f"Centroide tiempo={float(resultado['tiempo_riego']):.4f}, "
            f"frecuencia={float(resultado['frecuencia_riego']):.4f}, "
            f"caudal={float(resultado['caudal_agua']):.4f}.",
            estilos["normal"],
        )
    )

    elementos.append(PageBreak())
    _seccion(
        elementos,
        "Graficos",
        "Los graficos permiten observar visualmente las funciones de pertenencia evaluadas y "
        "las salidas agregadas utilizadas para calcular el centroide.",
        estilos,
    )
    if entradas:
        rutas_graficos = _generar_graficos(resultado, entradas, carpeta_graficos)
        _agregar_imagenes(elementos, rutas_graficos, estilos)
    else:
        elementos.append(Paragraph("No se recibieron entradas para graficar los valores ingresados.", estilos["normal"]))

    elementos.append(PageBreak())
    _seccion(
        elementos,
        "Recomendacion final",
        "Finalmente el sistema genera la recomendacion de riego considerando todas las condiciones analizadas.",
        estilos,
    )
    _agregar_recomendacion_final(elementos, resultado, estilos)
    elementos.append(Spacer(1, 0.35 * cm))
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

    documento.build(
        elementos,
        canvasmaker=lambda *args, **kwargs: _CanvasNumerado(
            *args,
            fecha_hora=fecha_hora,
            autores=autores,
            **kwargs,
        ),
    )
    return ruta_pdf
