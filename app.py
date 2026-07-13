"""Interfaz web profesional para el sistema de riego difuso Mamdani.

Aplicacion preparada para CPU basica y despliegue como servicio web en Render.
"""

from __future__ import annotations

import os
import base64
import html
import io
from pathlib import Path
from uuid import uuid4
from typing import Any

import gradio as gr
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

import charts
import fuzzy_engine
import history
import membership
import report
import rules


TITULO = "Sistema Inteligente para el Riego Automatico mediante Logica Difusa Mamdani"
RUTA_HISTORIAL = Path("data") / "historial.csv"
RUTA_CSS_TEMA = Path("assets") / "theme.css"
CULTIVOS = ["Lechuga", "Tomate", "Maíz", "Papa", "Fresa"]
SALIDAS = {
    "Tiempo de riego": "tiempo_riego",
    "Frecuencia de riego": "frecuencia_riego",
    "Caudal de agua": "caudal_agua",
}
SUPERFICIES_3D = {
    "Humedad del suelo vs temperatura ambiental -> tiempo de riego": {
        "x": "humedad_suelo",
        "y": "temperatura",
        "z": "tiempo_riego",
        "x_label": "Humedad del suelo (%)",
        "y_label": "Temperatura ambiental (C)",
        "z_label": "Tiempo de riego (min)",
        "x_rango": (0, 100),
        "y_rango": (0, 45),
    },
    "Humedad del suelo vs velocidad del viento -> caudal": {
        "x": "humedad_suelo",
        "y": "velocidad_viento",
        "z": "caudal_agua",
        "x_label": "Humedad del suelo (%)",
        "y_label": "Velocidad del viento (km/h)",
        "z_label": "Caudal de agua (L/min)",
        "x_rango": (0, 100),
        "y_rango": (0, 40),
    },
    "Humedad del suelo vs humedad ambiental -> frecuencia": {
        "x": "humedad_suelo",
        "y": "humedad_ambiental",
        "z": "frecuencia_riego",
        "x_label": "Humedad del suelo (%)",
        "y_label": "Humedad ambiental (%)",
        "z_label": "Frecuencia de riego (dias)",
        "x_rango": (0, 100),
        "y_rango": (0, 100),
    },
    "Temperatura vs velocidad del viento -> tiempo de riego": {
        "x": "temperatura",
        "y": "velocidad_viento",
        "z": "tiempo_riego",
        "x_label": "Temperatura ambiental (C)",
        "y_label": "Velocidad del viento (km/h)",
        "z_label": "Tiempo de riego (min)",
        "x_rango": (0, 45),
        "y_rango": (0, 40),
    },
}


def crear_tema_claro() -> gr.Theme:
    """Crea un tema claro para evitar acentos oscuros o morados de Gradio."""
    return gr.themes.Soft(
        primary_hue="blue",
        secondary_hue="cyan",
        neutral_hue="blue",
    ).set(
        body_background_fill="#ffffff",
        block_background_fill="#ffffff",
        block_border_color="#bfdbfe",
        block_label_background_fill="#dbeafe",
        block_label_text_color="#1e3a8a",
        button_primary_background_fill="#0f766e",
        button_primary_background_fill_hover="#0d9488",
        button_primary_text_color="#ffffff",
        button_secondary_background_fill="#ffffff",
        button_secondary_background_fill_hover="#eff6ff",
        button_secondary_text_color="#2563eb",
        input_background_fill="#ffffff",
        input_border_color="#d1d5db",
    )


CSS = """
:root {
    --verde: #1f7a4d;
    --verde-claro: #e8f5ed;
    --azul: #2563eb;
    --azul-claro: #eff6ff;
    --cian-claro: #ecfeff;
    --texto: #1e3a8a;
    --texto-suave: #1e40af;
    --borde: #bfdbfe;
    --borde-fuerte: #93c5fd;
    --superficie: #ffffff;
}
.gradio-container {
    max-width: 1180px !important;
    margin: 0 auto !important;
    background: linear-gradient(180deg, #f7fbf8 0%, #ffffff 45%) !important;
    color: var(--texto) !important;
}
.gradio-container,
.gradio-container p,
.gradio-container span,
.gradio-container label,
.gradio-container li,
.gradio-container td,
.gradio-container th,
.gradio-container textarea,
.gradio-container input,
.gradio-container select,
.gradio-container .prose,
.gradio-container .markdown,
.gradio-container .table-wrap {
    color: var(--texto) !important;
}
.gradio-container h1,
.gradio-container h2,
.gradio-container h3,
.gradio-container h4 {
    color: var(--texto) !important;
}
.gradio-container *,
.gradio-container *::before,
.gradio-container *::after {
    color: var(--texto) !important;
}
.gradio-container .block,
.gradio-container .form,
.gradio-container .panel,
.gradio-container textarea,
.gradio-container input,
.gradio-container select {
    background: var(--superficie) !important;
}
.gradio-container textarea,
.gradio-container input,
.gradio-container select {
    border-color: var(--borde) !important;
}
.hero {
    padding: 34px;
    border-radius: 10px;
    background: linear-gradient(135deg, #f8fafc 0%, #ecfdf5 100%);
    border: 1px solid #dbe7e1;
    text-align: left;
    box-shadow: 0 8px 22px rgba(15, 118, 110, 0.08);
}
.hero h1 {
    color: #12372a !important;
    margin: 0 0 12px;
    font-size: clamp(1.8rem, 3vw, 2.5rem);
    letter-spacing: 0;
}
.hero p, .texto-suave {
    color: var(--texto-suave) !important;
}
.hero p {
    max-width: 860px;
    margin: 0;
    font-size: 1rem;
    line-height: 1.65;
}
.site-brandbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    min-height: 76px;
    padding: 14px 18px;
    background: #ffffff;
    border: 1px solid #dbe7e1;
    border-radius: 10px;
    margin-bottom: 14px;
}
.brand-lockup {
    display: flex;
    align-items: center;
    gap: 12px;
}
.brand-mark {
    width: 48px;
    height: 48px;
    border-radius: 50%;
    background: linear-gradient(135deg, #d1fae5, #dbeafe);
    border: 1px solid #b7e4d1;
    display: grid;
    place-items: center;
    font-weight: 800;
    color: #0f766e !important;
}
.brand-name {
    color: #12372a !important;
    font-weight: 800;
    letter-spacing: 0;
}
.brand-subtitle {
    color: #64748b !important;
    font-size: 12px;
    margin-top: 2px;
}
.academic-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 14px;
    margin: 18px 0;
}
.academic-card {
    padding: 18px;
    border-radius: 10px;
    background: #ffffff;
    border: 1px solid #dbe7e1;
    box-shadow: 0 8px 18px rgba(37, 99, 235, 0.06);
}
.academic-card h3 {
    color: #12372a !important;
    font-size: 15px;
    font-weight: 700;
    margin-bottom: 8px;
}
.academic-card p,
.academic-card li {
    color: #475569 !important;
    font-size: 13px;
    line-height: 1.55;
    margin: 0;
}
.section-heading {
    margin: 22px 0 14px;
    color: #12372a !important;
    font-size: 18px;
    font-weight: 700;
}
.module-grid {
    display: grid;
    grid-template-columns: repeat(4, minmax(0, 1fr));
    gap: 14px;
}
.module-card {
    border: 1px solid #dbe7e1;
    border-radius: 10px;
    background: #ffffff;
    padding: 16px;
    box-shadow: 0 8px 18px rgba(37, 99, 235, 0.06);
}
.module-card h3 {
    color: #12372a !important;
    font-size: 14px;
    margin: 0 0 8px;
}
.module-card p {
    color: #64748b !important;
    font-size: 12px;
    line-height: 1.45;
    margin: 0;
}
.metric-card {
    padding: 18px;
    border-radius: 8px;
    background: var(--superficie);
    border: 1px solid #dbeafe;
    box-shadow: 0 8px 20px rgba(37, 99, 235, 0.08);
}
.metric-label {
    color: var(--texto) !important;
    font-size: 0.9rem;
    font-weight: 700;
}
.metric-value {
    color: #0f766e !important;
    font-size: 1.7rem;
    font-weight: 800;
}
.status-box {
    padding: 14px;
    border-radius: 8px;
    background: #f8fafc;
    border: 1px solid #dbeafe;
}
.ok {
    color: #0f766e !important;
    font-weight: 700;
}
.pending {
    color: var(--texto-suave) !important;
}
.rule-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.92rem;
}
.rule-table th {
    background: #dbeafe;
    color: var(--texto) !important;
    text-align: left;
    padding: 8px;
    border: 1px solid var(--borde);
}
.rule-table td {
    padding: 8px;
    border: 1px solid #dbeafe;
    vertical-align: top;
    background: var(--superficie);
    color: var(--texto) !important;
}
.rule-table tr.rule-max {
    background: #eff6ff;
    font-weight: 700;
}
button.primary {
    background: #0f766e !important;
    color: #ffffff !important;
    border-color: #0f766e !important;
}
button.primary span,
.gradio-container button.primary span {
    color: #ffffff !important;
}
.gradio-container button:not(.primary) {
    background: #ffffff !important;
    color: var(--azul) !important;
    border: 1px solid var(--borde-fuerte) !important;
    box-shadow: none !important;
}
.gradio-container button:not(.primary):hover {
    background: var(--azul-claro) !important;
    color: var(--texto) !important;
}
@keyframes tabFadeSlide {
    from {
        opacity: 0;
        transform: translateY(6px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
@keyframes dropdownFadeSlide {
    from {
        opacity: 0;
        transform: translateY(-6px);
    }
    to {
        opacity: 1;
        transform: translateY(0);
    }
}
.gradio-container .tab-nav {
    display: flex !important;
    align-items: center !important;
    gap: 6px !important;
    min-height: 48px !important;
    padding: 0 2px !important;
    border-bottom: 1px solid #dbeafe !important;
    background: transparent !important;
    overflow-x: auto !important;
    scrollbar-width: thin !important;
}
.gradio-container .tab-nav button,
.gradio-container .tabs button,
.gradio-container button[role="tab"],
.gradio-container .tab-nav button[aria-haspopup="menu"],
.gradio-container .tab-nav button[aria-haspopup="true"] {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    flex: 0 0 auto !important;
    box-sizing: border-box !important;
    min-height: 44px !important;
    height: 44px !important;
    padding: 0 16px !important;
    margin: 0 !important;
    border: 0 !important;
    border-bottom: 3px solid transparent !important;
    border-radius: 8px 8px 0 0 !important;
    background: transparent !important;
    box-shadow: none !important;
    color: var(--texto) !important;
    font-weight: 600 !important;
    line-height: 1 !important;
    white-space: nowrap !important;
    transition: color 0.25s ease, background-color 0.25s ease, border-color 0.25s ease !important;
}
.gradio-container .tab-nav button span,
.gradio-container .tabs button span,
.gradio-container button[role="tab"] span {
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    line-height: 1 !important;
}
.gradio-container .tab-nav button:hover,
.gradio-container .tabs button:hover,
.gradio-container button[role="tab"]:hover {
    background: #eff6ff !important;
    color: var(--texto) !important;
}
.gradio-container .tab-nav button.selected,
.gradio-container .tab-nav button.active,
.gradio-container .tab-nav button[aria-selected="true"],
.gradio-container .tabs button.selected,
.gradio-container .tabs button.active,
.gradio-container .tabs button[aria-selected="true"],
.gradio-container button[role="tab"].selected,
.gradio-container button[role="tab"].active,
.gradio-container button[role="tab"][aria-selected="true"],
.gradio-container [role="tab"][aria-selected="true"] {
    background: transparent !important;
    background-color: transparent !important;
    color: #0f766e !important;
    border-bottom: 3px solid #0f766e !important;
    border-radius: 8px 8px 0 0 !important;
    box-shadow: none !important;
    font-weight: 600 !important;
}
.gradio-container .tab-nav button.selected span,
.gradio-container .tab-nav button.active span,
.gradio-container .tab-nav button[aria-selected="true"] span,
.gradio-container .tabs button.selected span,
.gradio-container .tabs button.active span,
.gradio-container .tabs button[aria-selected="true"] span,
.gradio-container button[role="tab"][aria-selected="true"] span {
    color: #0f766e !important;
}
.gradio-container .tab-nav button.selected:hover,
.gradio-container .tab-nav button.active:hover,
.gradio-container .tab-nav button[aria-selected="true"]:hover,
.gradio-container .tabs button.selected:hover,
.gradio-container .tabs button.active:hover,
.gradio-container .tabs button[aria-selected="true"]:hover,
.gradio-container button[role="tab"][aria-selected="true"]:hover {
    background: #ecfeff !important;
    color: #0f766e !important;
}
.gradio-container .tabitem,
.gradio-container [role="tabpanel"],
.gradio-container [data-testid="tabitem"] {
    animation: tabFadeSlide 0.25s ease both !important;
}
.gradio-container .tab-nav [role="menu"],
.gradio-container .tabs [role="menu"],
.gradio-container [role="listbox"],
.gradio-container .tab-nav ul,
.gradio-container .tabs ul {
    border-radius: 12px !important;
    border: 1px solid var(--borde) !important;
    background: var(--superficie) !important;
    box-shadow: 0 12px 28px rgba(37, 99, 235, 0.14) !important;
    padding: 6px !important;
    animation: dropdownFadeSlide 0.22s ease both !important;
}
.gradio-container .tab-nav [role="menu"] button,
.gradio-container .tabs [role="menu"] button,
.gradio-container [role="listbox"] button,
.gradio-container .tab-nav ul button,
.gradio-container .tabs ul button {
    width: 100% !important;
    height: 40px !important;
    min-height: 40px !important;
    justify-content: flex-start !important;
    padding: 0 12px !important;
    border-radius: 8px !important;
    border-bottom: 0 !important;
    color: var(--texto) !important;
    background: transparent !important;
}
.gradio-container .tab-nav [role="menu"] button:hover,
.gradio-container .tabs [role="menu"] button:hover,
.gradio-container [role="listbox"] button:hover,
.gradio-container .tab-nav ul button:hover,
.gradio-container .tabs ul button:hover {
    background: #eff6ff !important;
}
.gradio-container code,
.gradio-container pre,
.gradio-container pre code,
.gradio-container .prose code,
.gradio-container .markdown code {
    background: #eef6ff !important;
    color: #1e40af !important;
    border: 1px solid #bfdbfe !important;
    border-radius: 8px !important;
    padding: 2px 6px !important;
    box-shadow: none !important;
}
.gradio-container pre {
    padding: 12px !important;
    white-space: pre-wrap !important;
}
.gradio-container .label-wrap,
.gradio-container .label-wrap *,
.gradio-container .block label,
.gradio-container .block-title,
.gradio-container .block-title *,
.gradio-container .plot label,
.gradio-container .output-class label {
    background: #dbeafe !important;
    color: #1e3a8a !important;
    border: 1px solid #93c5fd !important;
    border-radius: 10px !important;
}
.gradio-container .label-wrap,
.gradio-container .block-title {
    display: inline-flex !important;
    align-items: center !important;
    gap: 6px !important;
    padding: 4px 10px !important;
    margin-bottom: 6px !important;
}
.gradio-container .badge,
.gradio-container .token,
.gradio-container .chip,
.gradio-container .dataframe td span,
.gradio-container .table-wrap td span {
    background: #eff6ff !important;
    color: #2563eb !important;
    border: 1px solid #bfdbfe !important;
    border-radius: 8px !important;
    padding: 2px 6px !important;
}
.gradio-container table,
.gradio-container .dataframe,
.gradio-container .table-wrap,
.gradio-container .dataframe table {
    background: #ffffff !important;
    border-color: #bfdbfe !important;
    color: var(--texto) !important;
}
.gradio-container table thead,
.gradio-container table thead tr,
.gradio-container table th,
.gradio-container .dataframe th,
.gradio-container .table-wrap th {
    background: #dbeafe !important;
    color: #1e3a8a !important;
    border-color: #93c5fd !important;
    font-weight: 700 !important;
}
.gradio-container table tbody tr,
.gradio-container table tbody td,
.gradio-container .dataframe td,
.gradio-container .table-wrap td {
    background: #ffffff !important;
    color: var(--texto) !important;
    border-color: #dbeafe !important;
}
.gradio-container table tbody tr:hover,
.gradio-container .dataframe tr:hover,
.gradio-container .table-wrap tr:hover,
.gradio-container .dataframe tr:hover td,
.gradio-container .table-wrap tr:hover td {
    background: #eff6ff !important;
}
.gradio-container select,
.gradio-container input,
.gradio-container textarea,
.gradio-container [role="combobox"],
.gradio-container .dropdown,
.gradio-container .dropdown input {
    background: #ffffff !important;
    color: var(--texto) !important;
    border-color: #d1d5db !important;
    border-radius: 10px !important;
    box-shadow: none !important;
}
.gradio-container select:hover,
.gradio-container input:hover,
.gradio-container textarea:hover,
.gradio-container [role="combobox"]:hover,
.gradio-container .dropdown:hover {
    background: #eff6ff !important;
    border-color: #93c5fd !important;
}
.gradio-container .dropdown svg,
.gradio-container .dropdown svg *,
.gradio-container [role="combobox"] svg,
.gradio-container [role="combobox"] svg *,
.gradio-container .tab-nav svg,
.gradio-container .tab-nav svg * {
    color: #64748b !important;
    stroke: #64748b !important;
}
@media (max-width: 760px) {
    .site-brandbar {
        padding-left: 12px;
        padding-right: 12px;
    }
    .academic-grid,
    .module-grid {
        grid-template-columns: 1fr;
    }
    .site-brandbar {
        align-items: flex-start;
        gap: 12px;
        flex-direction: column;
    }
    .hero {
        padding: 18px;
    }
    .hero h1 {
        font-size: 1.8rem;
    }
    .metric-value {
        font-size: 1.35rem;
    }
}
"""


def cargar_css() -> str:
    """Carga el CSS base y las reglas visuales externas del proyecto."""
    try:
        css_tema = RUTA_CSS_TEMA.read_text(encoding="utf-8")
    except OSError:
        css_tema = ""
    return f"{CSS}\n{css_tema}"


def formatear_tarjeta(etiqueta: str, valor: str, unidad: str) -> str:
    """Crea una tarjeta HTML compacta para resultados."""
    return (
        "<div class='metric-card'>"
        f"<div class='metric-label'>{etiqueta}</div>"
        f"<div class='metric-value'>{valor}</div>"
        f"<div class='texto-suave'>{unidad}</div>"
        "</div>"
    )


def limitar_valor_control(valor: float | int | None, minimo: float, maximo: float, decimales: int) -> float:
    """Normaliza un valor de Slider/Number dentro del rango permitido."""
    if valor is None:
        return float(minimo)
    try:
        valor_normalizado = float(valor)
    except (TypeError, ValueError):
        valor_normalizado = float(minimo)
    valor_limitado = min(max(valor_normalizado, minimo), maximo)
    return round(valor_limitado, decimales)


def crear_control_numerico(
    titulo: str,
    minimo: float,
    maximo: float,
    valor: float,
    paso: float,
    decimales: int,
) -> tuple[gr.Slider, gr.Number]:
    """Crea una fila limpia con titulo, slider y caja numerica sincronizable."""
    with gr.Column(elem_classes=["input-card"]):
        gr.HTML(f"<div class='field-title'>{titulo}</div>")
        with gr.Row(elem_classes=["slider-row"]):
            with gr.Column(scale=8, min_width=220, elem_classes=["slider-column"]):
                slider = gr.Slider(
                    minimum=minimo,
                    maximum=maximo,
                    value=valor,
                    step=paso,
                    show_label=False,
                    buttons=[],
                    elem_classes=["clean-slider"],
                )
                gr.HTML(
                    "<div class='range-hints'>"
                    f"<span>{minimo:g}</span>"
                    f"<span>{maximo:g}</span>"
                    "</div>"
                )
            with gr.Column(scale=2, min_width=110, elem_classes=["number-column"]):
                numero = gr.Number(
                    value=valor,
                    show_label=False,
                    minimum=minimo,
                    maximum=maximo,
                    step=paso,
                    precision=decimales,
                    elem_classes=["clean-number"],
                )
    return slider, numero


def estado_proceso(etapa: str) -> str:
    """Devuelve indicadores visuales del proceso de inferencia."""
    etapas = [
        "Analizando condiciones",
        "Evaluando reglas",
        "Desfuzzificando",
        "Calculo finalizado",
    ]
    marcas = []
    etapa_encontrada = False
    for nombre in etapas:
        activo = not etapa_encontrada
        clase = "ok" if activo else "pending"
        prefijo = "[OK]" if activo else "[ ]"
        marcas.append(f"<span class='{clase}'>{prefijo} {nombre}</span>")
        if nombre == etapa:
            etapa_encontrada = True
    return "<div class='status-box'>" + "<br>".join(marcas) + "</div>"


def ejecutar_calculo(
    humedad_suelo: float,
    temperatura: float,
    humedad_ambiental: float,
    velocidad_viento: float,
    tipo_cultivo: str,
) -> tuple[str, str, str, str, str, dict[str, Any]]:
    """Ejecuta el motor Mamdani y devuelve datos listos para la interfaz."""
    try:
        resultado = fuzzy_engine.calcular_riego_mamdani(
            humedad_suelo=humedad_suelo,
            temperatura=temperatura,
            humedad_ambiental=humedad_ambiental,
            velocidad_viento=velocidad_viento,
            tipo_cultivo=tipo_cultivo,
        )
    except Exception as error:
        mensaje = f"No se pudo calcular el riego: {error}"
        return (
            formatear_tarjeta("Tiempo de riego", "-", "minutos"),
            formatear_tarjeta("Frecuencia de riego", "-", "dias"),
            formatear_tarjeta("Caudal", "-", "L/min"),
            mensaje,
            estado_proceso("Analizando condiciones"),
            {},
        )

    tiempo = formatear_tarjeta("Tiempo de riego", f"{resultado['tiempo_riego']:.2f}", "minutos")
    frecuencia = formatear_tarjeta("Frecuencia de riego", f"{resultado['frecuencia_riego']:.2f}", "dias")
    caudal = formatear_tarjeta("Caudal", f"{resultado['caudal_agua']:.2f}", "L/min")

    return (
        tiempo,
        frecuencia,
        caudal,
        resultado["interpretacion"],
        estado_proceso("Calculo finalizado"),
        resultado,
    )


def formatear_diccionario_grados(grados: dict[str, dict[str, float]]) -> str:
    """Convierte grados de pertenencia en Markdown."""
    lineas = []
    for variable, conjuntos in grados.items():
        lineas.append(f"**{variable}**")
        for conjunto, grado in conjuntos.items():
            lineas.append(f"- {conjunto}: `{grado:.4f}`")
    return "\n".join(lineas)


NOMBRES_ENTRADAS = {
    "humedad_suelo": "Humedad del suelo",
    "temperatura_ambiental": "Temperatura ambiental",
    "humedad_ambiental": "Humedad ambiental",
    "velocidad_viento": "Velocidad del viento",
    "tipo_cultivo": "Tipo de cultivo",
}

NOMBRES_SALIDAS = {
    "tiempo_riego": ("Tiempo de riego", "minutos"),
    "frecuencia_riego": ("Frecuencia de riego", "dias"),
    "caudal_agua": ("Caudal de agua", "L/min"),
}


def limpiar_texto(texto: str) -> str:
    """Escapa texto para insertarlo en bloques HTML seguros."""
    return html.escape(str(texto), quote=True)


def construir_tabla_entradas_html(
    humedad_suelo: float,
    temperatura: float,
    humedad_ambiental: float,
    velocidad_viento: float,
    tipo_cultivo: str,
) -> str:
    """Crea una tabla HTML elegante con los valores ingresados."""
    codigo = fuzzy_engine.resolver_tipo_cultivo(tipo_cultivo)
    filas = [
        ("Humedad del suelo", f"{humedad_suelo:.2f}", "%"),
        ("Temperatura ambiental", f"{temperatura:.2f}", "C"),
        ("Humedad ambiental", f"{humedad_ambiental:.2f}", "%"),
        ("Velocidad del viento", f"{velocidad_viento:.2f}", "km/h"),
        ("Tipo de cultivo", f"{limpiar_texto(tipo_cultivo)} (codigo {codigo:g})", "categoria"),
    ]
    cuerpo = "".join(
        f"<tr><td>{variable}</td><td>{valor}</td><td>{unidad}</td></tr>"
        for variable, valor, unidad in filas
    )
    return (
        "<table class='mamdani-table'>"
        "<thead><tr><th>Variable</th><th>Valor</th><th>Unidad</th></tr></thead>"
        f"<tbody>{cuerpo}</tbody></table>"
    )


def valores_entrada_para_procedimiento(
    humedad_suelo: float,
    temperatura: float,
    humedad_ambiental: float,
    velocidad_viento: float,
    tipo_cultivo: str,
) -> dict[str, float]:
    """Devuelve las entradas con los nombres tecnicos usados por membership.py."""
    return {
        "humedad_suelo": float(humedad_suelo),
        "temperatura_ambiental": float(temperatura),
        "humedad_ambiental": float(humedad_ambiental),
        "velocidad_viento": float(velocidad_viento),
        "tipo_cultivo": float(fuzzy_engine.resolver_tipo_cultivo(tipo_cultivo)),
    }


def explicar_cero_membresia(valor: float, definicion: membership.DefinicionMembresia) -> str:
    """Explica brevemente por que un conjunto tiene grado cero."""
    parametros = definicion.parametros
    if definicion.tipo == "triangular":
        a, _, c = parametros
        if valor <= a or valor >= c:
            return f"El valor x={valor:g} esta fuera del soporte [{a:g}, {c:g}], por eso su pertenencia es 0."
    else:
        a, _, _, d = parametros
        if valor < a or valor > d:
            return f"El valor x={valor:g} esta fuera del soporte [{a:g}, {d:g}], por eso su pertenencia es 0."
    return "El valor cae en un punto limite de la funcion donde la pertenencia es 0."


def formula_membresia_latex(
    valor: float,
    definicion: membership.DefinicionMembresia,
    grado: float,
) -> str:
    """Construye la explicacion LaTeX de una funcion de membresia."""
    x = float(valor)
    parametros = definicion.parametros
    nombre = limpiar_texto(definicion.nombre.replace("_", " "))
    if grado <= 0:
        return (
            f"<p><strong>{nombre}</strong>: {explicar_cero_membresia(x, definicion)}</p>"
            f"<p class='mamdani-result'>\\(\\mu_{{{definicion.nombre}}}({x:g}) = 0.0000\\)</p>"
        )

    if definicion.tipo == "triangular":
        a, b, c = parametros
        if a < x < b:
            expresion = (
                "\\[\\mu(x)=\\frac{x-a}{b-a}\\]"
                f"\\[\\mu({x:g})=\\frac{{{x:g}-{a:g}}}{{{b:g}-{a:g}}}"
                f"=\\frac{{{x-a:g}}}{{{b-a:g}}}={grado:.4f}\\]"
            )
            tramo = "tramo ascendente de la funcion triangular"
        elif b < x < c:
            expresion = (
                "\\[\\mu(x)=\\frac{c-x}{c-b}\\]"
                f"\\[\\mu({x:g})=\\frac{{{c:g}-{x:g}}}{{{c:g}-{b:g}}}"
                f"=\\frac{{{c-x:g}}}{{{c-b:g}}}={grado:.4f}\\]"
            )
            tramo = "tramo descendente de la funcion triangular"
        else:
            expresion = f"\\[\\mu({x:g})=1.0000\\]"
            tramo = "pico de la funcion triangular"
        parametros_html = f"a={a:g}, b={b:g}, c={c:g}"
        tipo = "Triangular"
    else:
        a, b, c, d = parametros
        if a < x < b:
            expresion = (
                "\\[\\mu(x)=\\frac{x-a}{b-a}\\]"
                f"\\[\\mu({x:g})=\\frac{{{x:g}-{a:g}}}{{{b:g}-{a:g}}}"
                f"=\\frac{{{x-a:g}}}{{{b-a:g}}}={grado:.4f}\\]"
            )
            tramo = "tramo ascendente de la funcion trapezoidal"
        elif c < x < d:
            expresion = (
                "\\[\\mu(x)=\\frac{d-x}{d-c}\\]"
                f"\\[\\mu({x:g})=\\frac{{{d:g}-{x:g}}}{{{d:g}-{c:g}}}"
                f"=\\frac{{{d-x:g}}}{{{d-c:g}}}={grado:.4f}\\]"
            )
            tramo = "tramo descendente de la funcion trapezoidal"
        else:
            expresion = f"\\[\\mu({x:g})=1.0000\\]"
            tramo = "meseta de pertenencia maxima de la funcion trapezoidal"
        parametros_html = f"a={a:g}, b={b:g}, c={c:g}, d={d:g}"
        tipo = "Trapezoidal"

    return f"""
<div class='mamdani-subcard'>
<p><strong>Conjunto linguistico:</strong> {nombre}</p>
<p><strong>Funcion utilizada:</strong> {tipo}. Parametros: {parametros_html}.</p>
<p><strong>Tramo aplicado:</strong> {tramo}.</p>
{expresion}
<p class='mamdani-result'>Resultado: \\(\\mu_{{{definicion.nombre}}}={grado:.4f}\\)</p>
</div>
"""


def construir_fuzzificacion_html(
    resultado: dict[str, Any],
    valores_entrada: dict[str, float],
) -> str:
    """Explica matematicamente la fuzzificacion de cada entrada."""
    bloques = []
    for nombre_variable, conjuntos in resultado["grados_pertenencia"].items():
        variable = membership.obtener_variable(nombre_variable)
        valor = valores_entrada[nombre_variable]
        detalles = []
        for definicion in variable.conjuntos:
            grado = float(conjuntos[definicion.nombre])
            if grado > 0:
                detalles.append(formula_membresia_latex(valor, definicion, grado))
        ceros = [
            f"<li><strong>{limpiar_texto(definicion.nombre.replace('_', ' '))}</strong>: "
            f"{explicar_cero_membresia(valor, definicion)}</li>"
            for definicion in variable.conjuntos
            if float(conjuntos[definicion.nombre]) == 0
        ]
        ceros_html = ""
        if ceros:
            ceros_html = (
                "<details class='mamdani-details'><summary>Conjuntos con pertenencia cero</summary>"
                f"<ul>{''.join(ceros)}</ul></details>"
            )
        bloques.append(
            "<div class='mamdani-subcard'>"
            f"<h4>{limpiar_texto(variable.nombre)}</h4>"
            f"<p><strong>Valor ingresado:</strong> {valor:g} {limpiar_texto(variable.unidad)}</p>"
            f"{''.join(detalles)}{ceros_html}</div>"
        )
    return "".join(bloques)


def construir_reglas_activadas_html(resultado: dict[str, Any]) -> str:
    """Muestra el procedimiento de activacion de todas las reglas activadas."""
    bloques = []
    grados = resultado["grados_pertenencia"]
    for regla in resultado["reglas_activadas"]:
        antecedentes = regla["antecedentes"]
        valores = [
            float(grados[antecedente["variable"]][antecedente["conjunto"]])
            for antecedente in antecedentes
        ]
        operador = regla["operador"].upper()
        funcion = "min" if operador == "AND" else "max"
        simbolo = "\\min" if operador == "AND" else "\\max"
        antecedentes_html = "".join(
            f"<li>{limpiar_texto(a['variable'])} = <strong>{limpiar_texto(a['conjunto'])}</strong> "
            f"con \\(\\mu={v:.4f}\\)</li>"
            for a, v in zip(antecedentes, valores)
        )
        consecuentes = regla["consecuentes"]
        consecuentes_html = "".join(
            f"<li>{limpiar_texto(nombre)} = <strong>{limpiar_texto(valor)}</strong></li>"
            for nombre, valor in consecuentes.items()
        )
        valores_latex = ", ".join(f"{valor:.4f}" for valor in valores)
        resultado_alpha = float(regla["grado_activacion"])
        bloques.append(
            "<div class='mamdani-subcard'>"
            f"<h4>Regla {limpiar_texto(regla['id'])}</h4>"
            f"<p>{limpiar_texto(regla['texto'])}</p>"
            f"<p><strong>Antecedentes:</strong></p><ul>{antecedentes_html}</ul>"
            f"<p><strong>Consecuentes:</strong></p><ul>{consecuentes_html}</ul>"
            f"\\[\\alpha_{{{regla['id']}}}={simbolo}(\\mu_1,\\mu_2,\\ldots,\\mu_n)\\]"
            f"\\[\\alpha_{{{regla['id']}}}={funcion}({valores_latex})={resultado_alpha:.4f}\\]"
            f"<p>Se usa <strong>{funcion.upper()}</strong> porque la regla tiene operador logico "
            f"<strong>{operador}</strong>.</p>"
            "</div>"
        )
    return "".join(bloques)


def construir_agregacion_html(resultado: dict[str, Any]) -> str:
    """Explica implicacion y agregacion Mamdani para las salidas."""
    bloques = []
    reglas = resultado["reglas_activadas"]
    for salida, (nombre_visible, _) in NOMBRES_SALIDAS.items():
        terminos = []
        detalle = []
        for regla in reglas:
            conjunto = regla["consecuentes"][salida]
            rid = regla["id"]
            alpha = float(regla["grado_activacion"])
            terminos.append(f"\\mu'_{{{rid}}}(z)")
            detalle.append(
                f"<li>Regla {limpiar_texto(rid)}: conjunto <strong>{limpiar_texto(conjunto)}</strong>, "
                f"\\(\\mu'_{{{rid}}}(z)=\\min({alpha:.4f},\\mu_{{{conjunto}}}(z))\\)</li>"
            )
        formula_max = ", ".join(terminos)
        bloques.append(
            "<div class='mamdani-subcard'>"
            f"<h4>{nombre_visible}</h4>"
            "<p>Cada regla activa genera un consecuente recortado mediante implicacion Mamdani.</p>"
            f"<ul>{''.join(detalle)}</ul>"
            "\\[\\mu_{agregada}(z)=\\max(\\mu'_1(z),\\mu'_2(z),\\ldots,\\mu'_n(z))\\]"
            f"\\[\\mu_{{agregada}}(z)=\\max({formula_max})\\]"
            "<p>El operador MAX conserva, para cada punto del universo, el mayor grado aportado por las reglas activadas.</p>"
            "</div>"
        )
    return "".join(bloques)


def construir_grafica_agregacion_base64(resultado: dict[str, Any]) -> str:
    """Genera una grafica embebida de las salidas agregadas."""
    agregados = resultado["conjuntos_agregados"]
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.2))
    for ax, (salida, (nombre_visible, unidad)) in zip(axes, NOMBRES_SALIDAS.items()):
        universo = np.asarray(agregados[salida]["universo"], dtype=float)
        membresia = np.asarray(agregados[salida]["membresia"], dtype=float)
        centroide = float(resultado[salida])
        ax.plot(universo, membresia, color="#0f766e", linewidth=2)
        ax.fill_between(universo, membresia, color="#99f6e4", alpha=0.65)
        ax.axvline(centroide, color="#1d4ed8", linestyle="--", linewidth=1.8)
        ax.set_title(nombre_visible)
        ax.set_xlabel(unidad)
        ax.set_ylabel("mu")
        ax.grid(alpha=0.25)
    fig.tight_layout()
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=150, bbox_inches="tight")
    plt.close(fig)
    imagen = base64.b64encode(buffer.getvalue()).decode("ascii")
    return f"<img class='mamdani-plot' src='data:image/png;base64,{imagen}' alt='Grafica de agregacion Mamdani'/>"


def construir_desfuzzificacion_html(resultado: dict[str, Any]) -> str:
    """Explica el calculo del centroide de cada salida usando agregados reales."""
    filas = []
    bloques = []
    for salida, (nombre_visible, unidad) in NOMBRES_SALIDAS.items():
        datos = resultado["conjuntos_agregados"][salida]
        universo = np.asarray(datos["universo"], dtype=float)
        membresia = np.asarray(datos["membresia"], dtype=float)
        numerador = float(np.sum(universo * membresia))
        denominador = float(np.sum(membresia))
        centroide = float(resultado[salida])
        filas.append(
            f"<tr><td>{nombre_visible}</td><td>{numerador:.4f}</td><td>{denominador:.4f}</td>"
            f"<td>{centroide:.4f} {unidad}</td></tr>"
        )
        bloques.append(
            "<div class='mamdani-subcard'>"
            f"<h4>{nombre_visible}</h4>"
            "\\[z^*=\\frac{\\sum_i z_i\\mu(z_i)}{\\sum_i\\mu(z_i)}\\]"
            f"\\[z^*=\\frac{{{numerador:.4f}}}{{{denominador:.4f}}}={centroide:.4f}\\;{limpiar_texto(unidad)}\\]"
            "<p>El universo de salida se discretiza; para cada punto se multiplica "
            "\\(z_i\\) por su grado agregado \\(\\mu(z_i)\\), y luego se divide entre la suma total de grados.</p>"
            "</div>"
        )
    tabla = (
        "<table class='mamdani-table'><thead><tr><th>Salida</th><th>Numerador</th>"
        "<th>Denominador</th><th>Centroide</th></tr></thead>"
        f"<tbody>{''.join(filas)}</tbody></table>"
    )
    return tabla + "".join(bloques)


def construir_conclusion_html(resultado: dict[str, Any]) -> str:
    """Construye una conclusion educativa a partir de los resultados reales."""
    reglas = resultado["reglas_activadas"]
    regla_principal = max(reglas, key=lambda regla: regla["grado_activacion"])
    grados_activos = []
    for variable, conjuntos in resultado["grados_pertenencia"].items():
        activos = [(nombre, grado) for nombre, grado in conjuntos.items() if grado > 0]
        if activos:
            principal = max(activos, key=lambda item: item[1])
            grados_activos.append(
                f"<li>{limpiar_texto(NOMBRES_ENTRADAS.get(variable, variable))}: "
                f"<strong>{limpiar_texto(principal[0])}</strong> con \\(\\mu={principal[1]:.4f}\\)</li>"
            )
    return f"""
<ul>{''.join(grados_activos)}</ul>
<p>Se activaron <strong>{len(reglas)}</strong> reglas. La regla dominante fue
<strong>{limpiar_texto(regla_principal['id'])}</strong> con
\\(\\alpha={float(regla_principal['grado_activacion']):.4f}\\).</p>
<p>Tras la agregacion por MAX y la desfuzzificacion por centroide, el sistema obtuvo:
<strong>{resultado['tiempo_riego']:.2f} minutos</strong>,
<strong>{resultado['frecuencia_riego']:.2f} dias</strong> y
<strong>{resultado['caudal_agua']:.2f} L/min</strong>.</p>
<p>{limpiar_texto(resultado['interpretacion'])}</p>
"""


def generar_procedimiento(
    resultado: dict[str, Any] | None,
    humedad_suelo: float,
    temperatura: float,
    humedad_ambiental: float,
    velocidad_viento: float,
    tipo_cultivo: str,
) -> str:
    """Genera un visor educativo del procedimiento Mamdani paso a paso."""
    if not resultado:
        _, _, _, _, _, resultado = ejecutar_calculo(
            humedad_suelo,
            temperatura,
            humedad_ambiental,
            velocidad_viento,
            tipo_cultivo,
        )
    if not resultado:
        return "No hay resultados disponibles para mostrar el procedimiento."

    valores_entrada = valores_entrada_para_procedimiento(
        humedad_suelo,
        temperatura,
        humedad_ambiental,
        velocidad_viento,
        tipo_cultivo,
    )
    tabla_entradas = construir_tabla_entradas_html(
        humedad_suelo,
        temperatura,
        humedad_ambiental,
        velocidad_viento,
        tipo_cultivo,
    )
    grafica_agregacion = construir_grafica_agregacion_base64(resultado)
    return f"""
<div class="mamdani-viewer">
<section class="mamdani-card">
<h2>Procedimiento Mamdani paso a paso</h2>
<p>Este visor muestra como el motor difuso transforma las entradas crisp en grados de pertenencia,
evalua reglas linguisticas, agrega consecuentes y obtiene salidas numericas mediante el centroide.</p>
</section>

<section class="mamdani-card">
<h3>Paso 1. Valores ingresados</h3>
<p>Estos son los valores crisp proporcionados por el usuario antes de iniciar la fuzzificacion.</p>
{tabla_entradas}
</section>

<section class="mamdani-card">
<h3>Paso 2. Fuzzificacion</h3>
<p>La fuzzificacion convierte cada entrada numerica en grados de pertenencia
\\(\\mu(x)\\) sobre conjuntos linguisticos.</p>
\\[\\mu_{{triangular}}(x;a,b,c)=\\max\\left(\\min\\left(\\frac{{x-a}}{{b-a}},\\frac{{c-x}}{{c-b}}\\right),0\\right)\\]
\\[\\mu_{{trapezoidal}}(x;a,b,c,d)=\\max\\left(\\min\\left(\\frac{{x-a}}{{b-a}},1,\\frac{{d-x}}{{d-c}}\\right),0\\right)\\]
{construir_fuzzificacion_html(resultado, valores_entrada)}
</section>

<section class="mamdani-card">
<h3>Paso 3. Activacion de reglas</h3>
<p>En reglas con operador AND se usa el minimo porque todos los antecedentes deben cumplirse simultaneamente.
En reglas OR se usa el maximo porque basta con que un antecedente tenga mayor evidencia.</p>
\\[\\alpha_{{AND}}=\\min(\\mu_1,\\mu_2,\\ldots,\\mu_n)\\]
\\[\\alpha_{{OR}}=\\max(\\mu_1,\\mu_2,\\ldots,\\mu_n)\\]
{construir_reglas_activadas_html(resultado)}
</section>

<section class="mamdani-card">
<h3>Paso 4. Implicacion y agregacion</h3>
<p>Cada regla activa recorta sus consecuentes con el grado de activacion \\(\\alpha\\).
Luego todas las funciones recortadas se unen mediante MAX.</p>
\\[\\mu'_B(z)=\\min(\\alpha,\\mu_B(z))\\]
{construir_agregacion_html(resultado)}
<div class="mamdani-plot-wrap">{grafica_agregacion}</div>
</section>

<section class="mamdani-card">
<h3>Paso 5. Desfuzzificacion por centroide</h3>
<p>El metodo del centroide calcula el punto de equilibrio del area difusa agregada.</p>
\\[z^*=\\frac{{\\sum_i z_i\\mu(z_i)}}{{\\sum_i\\mu(z_i)}}\\]
{construir_desfuzzificacion_html(resultado)}
</section>

<section class="mamdani-card">
<h3>Paso 6. Salidas crisp</h3>
<div class="crisp-grid">
<div><strong>Tiempo de riego</strong><span>{resultado["tiempo_riego"]:.4f} minutos</span></div>
<div><strong>Frecuencia de riego</strong><span>{resultado["frecuencia_riego"]:.4f} dias</span></div>
<div><strong>Caudal de agua</strong><span>{resultado["caudal_agua"]:.4f} L/min</span></div>
</div>
<p>No se aplica una conversion adicional: cada salida ya esta expresada en su universo original
despues de la desfuzzificacion.</p>
</section>

<section class="mamdani-card conclusion-card">
<h3>Paso 7. Interpretacion del sistema</h3>
{construir_conclusion_html(resultado)}
</section>
</div>
"""


def mostrar_procedimiento_evaluacion(
    resultado: dict[str, Any] | None,
    humedad_suelo: float,
    temperatura: float,
    humedad_ambiental: float,
    velocidad_viento: float,
    tipo_cultivo: str,
) -> tuple[str, gr.update]:
    """Genera el procedimiento y muestra su seccion independiente."""
    procedimiento = generar_procedimiento(
        resultado,
        humedad_suelo,
        temperatura,
        humedad_ambiental,
        velocidad_viento,
        tipo_cultivo,
    )
    return procedimiento, gr.update(visible=True)


def tabla_funciones_pertenencia() -> pd.DataFrame:
    """Devuelve tabla de parametros de membresia."""
    return pd.DataFrame(membership.obtener_tabla_parametros())


VARIABLES_MEMBRESIA = [
    ("Humedad del suelo", "humedad_suelo"),
    ("Temperatura ambiental", "temperatura_ambiental"),
    ("Humedad ambiental", "humedad_ambiental"),
    ("Velocidad del viento", "velocidad_viento"),
    ("Tipo de cultivo", "tipo_cultivo"),
]


NOMBRES_VARIABLES_MEMBRESIA = {
    "humedad_suelo": "Humedad del suelo",
    "temperatura_ambiental": "Temperatura ambiental",
    "humedad_ambiental": "Humedad ambiental",
    "velocidad_viento": "Velocidad del viento",
    "tipo_cultivo": "Tipo de cultivo",
}


def tabla_parametros_variable(nombre_variable: str) -> pd.DataFrame:
    """Devuelve parametros de membresia filtrados por variable y con titulos legibles."""
    tabla = tabla_funciones_pertenencia()
    if nombre_variable:
        tabla = tabla[tabla["variable"] == nombre_variable].copy()

    tabla = tabla.rename(
        columns={
            "variable": "Variable",
            "conjunto": "Conjunto linguistico",
            "tipo": "Tipo de funcion",
            "parametros": "Parametros",
            "universo": "Rango",
        }
    )
    tabla["Variable"] = tabla["Variable"].map(NOMBRES_VARIABLES_MEMBRESIA).fillna(tabla["Variable"])
    return tabla


def tabla_parametros_variable_html(nombre_variable: str) -> str:
    """Renderiza los mismos parametros como una tabla HTML legible tipo hoja de calculo."""
    tabla = tabla_parametros_variable(nombre_variable)
    encabezados = {
        "Variable": "Variable",
        "Conjunto linguistico": "Conjunto lingüístico",
        "Tipo de funcion": "Tipo de función",
        "Parametros": "Parámetros",
        "Rango": "Rango",
    }
    columnas = list(encabezados.keys())

    filas_html = []
    for _, fila in tabla.iterrows():
        celdas = "".join(
            f"<td>{html.escape(str(fila[columna]))}</td>"
            for columna in columnas
        )
        filas_html.append(f"<tr>{celdas}</tr>")

    encabezados_html = "".join(f"<th>{html.escape(etiqueta)}</th>" for etiqueta in encabezados.values())
    cuerpo = "".join(filas_html) or (
        "<tr><td colspan='5'>No hay parametros disponibles para la variable seleccionada.</td></tr>"
    )
    return f"""
<div class="membership-table-shell">
    <div class="membership-table-scroll" role="region" aria-label="Tabla de parametros de pertenencia">
        <table class="excel-membership-table">
            <thead>
                <tr>{encabezados_html}</tr>
            </thead>
            <tbody>{cuerpo}</tbody>
        </table>
    </div>
</div>
"""


def tabla_reglas() -> pd.DataFrame:
    """Devuelve tabla de reglas difusas."""
    return pd.DataFrame(rules.obtener_tabla_reglas())


def opciones_filtro_reglas() -> list[str]:
    """Devuelve opciones para filtrar la base de reglas por identificador."""
    return ["Todas"] + [regla.identificador for regla in rules.obtener_reglas_difusas()]


def filtrar_tabla_reglas(filtro_regla: str, texto_busqueda: str) -> pd.DataFrame:
    """Filtra la tabla de reglas por ID y texto libre."""
    tabla = tabla_reglas()
    if filtro_regla and filtro_regla != "Todas":
        tabla = tabla[tabla["id"] == filtro_regla]

    busqueda = (texto_busqueda or "").strip().lower()
    if busqueda:
        mascara = tabla.apply(
            lambda fila: fila.astype(str).str.lower().str.contains(busqueda, regex=False).any(),
            axis=1,
        )
        tabla = tabla[mascara]
    return tabla


def mostrar_seccion_mas(opcion: str) -> tuple[gr.update, gr.update, gr.update]:
    """Muestra solo la seccion seleccionada dentro del menu Mas."""
    return (
        gr.update(visible=opcion == "Surface Viewer"),
        gr.update(visible=opcion == "Historial"),
        gr.update(visible=opcion == "Acerca del proyecto"),
    )


def opciones_reglas() -> list[str]:
    """Construye opciones legibles para el visor de reglas."""
    return [f"{regla.identificador} - {regla.texto[:90]}" for regla in rules.obtener_reglas_difusas()]


def ver_regla(opcion: str) -> str:
    """Muestra el detalle de una regla seleccionada."""
    if not opcion:
        return "Seleccione una regla para ver su detalle."
    identificador = opcion.split(" - ", 1)[0]
    for regla in rules.obtener_reglas_difusas():
        if regla.identificador == identificador:
            antecedentes = "\n".join(
                f"- {antecedente.variable}: `{antecedente.conjunto}`"
                for antecedente in regla.antecedentes
            )
            return f"""
## {regla.identificador}

**Operador:** `{regla.operador_logico}`

**Antecedentes**
{antecedentes}

**Consecuentes**
- tiempo_riego: `{regla.consecuentes.tiempo_riego}`
- frecuencia_riego: `{regla.consecuentes.frecuencia_riego}`
- caudal_agua: `{regla.consecuentes.caudal_agua}`

**Regla legible**
{rules.convertir_regla_a_texto(regla)}

**Explicacion**
{regla.explicacion}
"""
    return "No se encontro la regla seleccionada."


def obtener_resultado_rule_viewer(
    resultado: dict[str, Any] | None,
    humedad_suelo: float,
    temperatura: float,
    humedad_ambiental: float,
    velocidad_viento: float,
    tipo_cultivo: str,
) -> dict[str, Any]:
    """Obtiene el ultimo resultado o calcula uno nuevo con las entradas actuales."""
    if resultado:
        return resultado

    _, _, _, _, _, nuevo_resultado = ejecutar_calculo(
        humedad_suelo,
        temperatura,
        humedad_ambiental,
        velocidad_viento,
        tipo_cultivo,
    )
    if not nuevo_resultado:
        raise RuntimeError("No hay datos reales disponibles para construir el Rule Viewer.")
    return nuevo_resultado


def construir_tabla_rule_viewer(resultado: dict[str, Any]) -> pd.DataFrame:
    """Construye la tabla educativa de reglas activadas."""
    filas = []
    for regla in resultado["reglas_activadas"]:
        consecuentes = regla["consecuentes"]
        filas.append(
            {
                "ID de regla": regla["id"],
                "Regla linguistica": regla["texto"],
                "Grado de activacion": round(float(regla["grado_activacion"]), 4),
                "Tiempo de riego": consecuentes["tiempo_riego"],
                "Frecuencia": consecuentes["frecuencia_riego"],
                "Caudal": consecuentes["caudal_agua"],
            }
        )
    return pd.DataFrame(filas)


def construir_tabla_rule_viewer_html(resultado: dict[str, Any]) -> str:
    """Construye una tabla HTML con resaltado de reglas de mayor activacion."""
    tabla = construir_tabla_rule_viewer(resultado)
    if tabla.empty:
        return "<p>No hay reglas activadas.</p>"

    maximo = float(tabla["Grado de activacion"].max())
    encabezados = "".join(f"<th>{columna}</th>" for columna in tabla.columns)
    filas_html = []
    for _, fila in tabla.iterrows():
        clase = " class='rule-max'" if float(fila["Grado de activacion"]) == maximo else ""
        celdas = "".join(f"<td>{fila[columna]}</td>" for columna in tabla.columns)
        filas_html.append(f"<tr{clase}>{celdas}</tr>")

    return (
        "<div class='texto-suave'>Las filas azules corresponden a la mayor activacion.</div>"
        "<table class='rule-table'>"
        f"<thead><tr>{encabezados}</tr></thead>"
        f"<tbody>{''.join(filas_html)}</tbody>"
        "</table>"
    )


def construir_entradas_rule_viewer(
    humedad_suelo: float,
    temperatura: float,
    humedad_ambiental: float,
    velocidad_viento: float,
    tipo_cultivo: str,
) -> str:
    """Resume las entradas seleccionadas por el usuario."""
    codigo_cultivo = fuzzy_engine.resolver_tipo_cultivo(tipo_cultivo)
    return f"""
### Entradas seleccionadas
- Humedad del suelo: `{humedad_suelo:.2f} %`
- Temperatura ambiental: `{temperatura:.2f} C`
- Humedad ambiental: `{humedad_ambiental:.2f} %`
- Velocidad del viento: `{velocidad_viento:.2f} km/h`
- Tipo de cultivo: `{tipo_cultivo}` codigo `{codigo_cultivo:g}`
"""


def construir_resumen_rule_viewer(resultado: dict[str, Any]) -> str:
    """Resume activacion, agregacion y centroides finales."""
    reglas = resultado["reglas_activadas"]
    regla_maxima = max(reglas, key=lambda regla: regla["grado_activacion"])
    return f"""
### Lectura educativa del Rule Viewer
- Reglas activadas: `{len(reglas)}`
- Mayor intensidad: `{regla_maxima["id"]}` con alpha `{regla_maxima["grado_activacion"]:.4f}`
- Consecuentes recortados: cada salida linguistica se recorta con `min(alpha, μ_B(z))`.
- Salida agregada: las funciones recortadas se combinan con `MAX`.
- Centroide final tiempo: `{resultado["tiempo_riego"]:.4f} min`
- Centroide final frecuencia: `{resultado["frecuencia_riego"]:.4f} dias`
- Centroide final caudal: `{resultado["caudal_agua"]:.4f} L/min`
"""


def construir_interpretacion_final_rule_viewer(resultado: dict[str, Any]) -> str:
    """Construye una interpretacion final breve para el Rule Viewer."""
    reglas = resultado["reglas_activadas"]
    regla_maxima = max(reglas, key=lambda regla: regla["grado_activacion"])
    return f"""
### Interpretacion final
El motor Mamdani activo `{len(reglas)}` reglas para este escenario. La regla dominante fue
`{regla_maxima["id"]}` con un grado de activacion de `{regla_maxima["grado_activacion"]:.4f}`.

Tras recortar los consecuentes, agregarlos mediante MAX y aplicar el centroide, el sistema obtiene:

- Tiempo de riego: `{resultado["tiempo_riego"]:.2f} min`
- Frecuencia de riego: `{resultado["frecuencia_riego"]:.2f} dias`
- Caudal de agua: `{resultado["caudal_agua"]:.2f} L/min`
"""


def graficar_rule_viewer(resultado: dict[str, Any]):
    """Crea una figura educativa tipo Rule Viewer con datos reales del motor."""
    reglas = resultado["reglas_activadas"]
    grados = resultado["grados_pertenencia"]
    agregados = resultado["conjuntos_agregados"]

    fig, axes = plt.subplots(2, 2, figsize=(12, 8.4))
    ax_grados, ax_reglas, ax_salidas, ax_recortes = axes.flatten()

    etiquetas_grados = []
    valores_grados = []
    for variable, conjuntos in grados.items():
        for conjunto, grado in conjuntos.items():
            if grado > 0:
                etiquetas_grados.append(f"{variable}\n{conjunto}")
                valores_grados.append(grado)
    ax_grados.barh(etiquetas_grados, valores_grados, color="#2f9e44")
    ax_grados.set_title("Grados de pertenencia activos")
    ax_grados.set_xlabel("μ(x)")
    ax_grados.set_xlim(0, 1)
    ax_grados.grid(axis="x", alpha=0.25)

    reglas_top = sorted(reglas, key=lambda regla: regla["grado_activacion"], reverse=True)[:12]
    ids = [regla["id"] for regla in reglas_top]
    intensidades = [float(regla["grado_activacion"]) for regla in reglas_top]
    colores = ["#1d4ed8" if valor == max(intensidades) else "#38bdf8" for valor in intensidades]
    ax_reglas.bar(ids, intensidades, color=colores)
    ax_reglas.set_title("Intensidad de reglas activadas")
    ax_reglas.set_ylabel("α")
    ax_reglas.set_ylim(0, 1)
    ax_reglas.tick_params(axis="x", rotation=45)
    ax_reglas.grid(axis="y", alpha=0.25)

    nombres_salidas = ["tiempo_riego", "frecuencia_riego", "caudal_agua"]
    colores_salidas = ["#2f9e44", "#1f6f9f", "#7c3aed"]
    for nombre_salida, color in zip(nombres_salidas, colores_salidas):
        universo = np.asarray(agregados[nombre_salida]["universo"], dtype=float)
        membresia = np.asarray(agregados[nombre_salida]["membresia"], dtype=float)
        universo_normalizado = (universo - universo.min()) / (universo.max() - universo.min())
        ax_salidas.plot(universo_normalizado, membresia, color=color, linewidth=2, label=nombre_salida)
        ax_salidas.fill_between(universo_normalizado, membresia, color=color, alpha=0.16)
        centroide = float(resultado[nombre_salida])
        centroide_normalizado = (centroide - universo.min()) / (universo.max() - universo.min())
        ax_salidas.axvline(centroide_normalizado, color=color, linestyle="--", linewidth=1.6)
    ax_salidas.set_title("Salidas agregadas y centroides normalizados")
    ax_salidas.set_xlabel("Universo normalizado")
    ax_salidas.set_ylabel("μ agregada")
    ax_salidas.set_ylim(0, 1)
    ax_salidas.grid(alpha=0.25)
    ax_salidas.legend(fontsize=8)

    funciones = membership.crear_funciones_membresia(membership.crear_universos())
    regla_principal = reglas_top[0]
    alpha = float(regla_principal["grado_activacion"])
    for nombre_salida, color in zip(nombres_salidas, colores_salidas):
        consecuente = regla_principal["consecuentes"][nombre_salida]
        universo = membership.crear_universos()[nombre_salida]
        recorte = np.minimum(alpha, funciones[nombre_salida][consecuente])
        universo_normalizado = (universo - universo.min()) / (universo.max() - universo.min())
        ax_recortes.plot(
            universo_normalizado,
            recorte,
            color=color,
            linewidth=2,
            label=f"{nombre_salida}: {consecuente}",
        )
        ax_recortes.fill_between(universo_normalizado, recorte, color=color, alpha=0.12)
    ax_recortes.set_title(f"Consecuentes recortados de la regla principal {regla_principal['id']}")
    ax_recortes.set_xlabel("Universo normalizado")
    ax_recortes.set_ylabel("min(α, μB)")
    ax_recortes.set_ylim(0, 1)
    ax_recortes.grid(alpha=0.25)
    ax_recortes.legend(fontsize=8)

    fig.tight_layout()
    return fig


def actualizar_rule_viewer(
    resultado: dict[str, Any] | None,
    humedad_suelo: float,
    temperatura: float,
    humedad_ambiental: float,
    velocidad_viento: float,
    tipo_cultivo: str,
):
    """Actualiza todos los componentes del Rule Viewer con datos del motor."""
    resultado_real = obtener_resultado_rule_viewer(
        resultado,
        humedad_suelo,
        temperatura,
        humedad_ambiental,
        velocidad_viento,
        tipo_cultivo,
    )
    return (
        construir_entradas_rule_viewer(
            humedad_suelo,
            temperatura,
            humedad_ambiental,
            velocidad_viento,
            tipo_cultivo,
        ),
        formatear_diccionario_grados(resultado_real["grados_pertenencia"]),
        construir_tabla_rule_viewer(resultado_real),
        construir_tabla_rule_viewer_html(resultado_real),
        graficar_rule_viewer(resultado_real),
        construir_resumen_rule_viewer(resultado_real),
        construir_interpretacion_final_rule_viewer(resultado_real),
    )


def obtener_valor_variable_desde_entradas(
    nombre_variable: str,
    humedad_suelo: float,
    temperatura: float,
    humedad_ambiental: float,
    velocidad_viento: float,
    tipo_cultivo: str,
) -> float:
    """Obtiene el valor actual de una variable desde los controles de la app."""
    valores = {
        "humedad_suelo": humedad_suelo,
        "temperatura_ambiental": temperatura,
        "humedad_ambiental": humedad_ambiental,
        "velocidad_viento": velocidad_viento,
        "tipo_cultivo": fuzzy_engine.resolver_tipo_cultivo(tipo_cultivo),
    }
    return float(valores[nombre_variable])


def graficar_membresia(
    nombre_variable: str,
    humedad_suelo: float,
    temperatura: float,
    humedad_ambiental: float,
    velocidad_viento: float,
    tipo_cultivo: str,
):
    """Grafica funciones de pertenencia marcando el valor ingresado."""
    valor = obtener_valor_variable_desde_entradas(
        nombre_variable,
        humedad_suelo,
        temperatura,
        humedad_ambiental,
        velocidad_viento,
        tipo_cultivo,
    )
    return charts.graficar_variable(nombre_variable, valor)


def graficar_salida_agregada_interfaz(
    resultado: dict[str, Any] | None,
    salida_visible: str,
    humedad_suelo: float,
    temperatura: float,
    humedad_ambiental: float,
    velocidad_viento: float,
    tipo_cultivo: str,
):
    """Grafica la funcion agregada de una salida usando el ultimo calculo."""
    if not resultado:
        _, _, _, _, _, resultado = ejecutar_calculo(
            humedad_suelo,
            temperatura,
            humedad_ambiental,
            velocidad_viento,
            tipo_cultivo,
        )

    nombre_salida = SALIDAS[salida_visible]
    datos_agregados = resultado["conjuntos_agregados"][nombre_salida]
    return charts.graficar_salida_agregada(
        nombre_salida=nombre_salida,
        universo=datos_agregados["universo"],
        funcion_agregada=datos_agregados["membresia"],
        centroide=float(resultado[nombre_salida]),
    )


def construir_entradas_superficie(
    variable_x: str,
    valor_x: float,
    variable_y: str,
    valor_y: float,
    humedad_suelo_fija: float,
    temperatura_fija: float,
    humedad_ambiental_fija: float,
    velocidad_viento_fija: float,
    tipo_cultivo: str,
) -> dict[str, float | str]:
    """Construye las entradas del motor para un punto de la malla 3D."""
    entradas: dict[str, float | str] = {
        "humedad_suelo": float(humedad_suelo_fija),
        "temperatura": float(temperatura_fija),
        "humedad_ambiental": float(humedad_ambiental_fija),
        "velocidad_viento": float(velocidad_viento_fija),
        "tipo_cultivo": tipo_cultivo,
    }
    entradas[variable_x] = float(valor_x)
    entradas[variable_y] = float(valor_y)
    return entradas


def graficar_superficie(
    superficie: str,
    tipo_cultivo: str,
    humedad_suelo_fija: float,
    temperatura_fija: float,
    humedad_ambiental_fija: float,
    velocidad_viento_fija: float,
    resolucion: int,
):
    """Genera una superficie 3D calculada con el motor Mamdani real."""
    configuracion = SUPERFICIES_3D[superficie]
    resolucion = int(resolucion)
    valores_x = np.linspace(*configuracion["x_rango"], resolucion)
    valores_y = np.linspace(*configuracion["y_rango"], resolucion)
    malla_x, malla_y = np.meshgrid(valores_x, valores_y)
    malla_z = np.zeros_like(malla_x, dtype=float)

    for fila in range(malla_x.shape[0]):
        for columna in range(malla_x.shape[1]):
            entradas = construir_entradas_superficie(
                variable_x=str(configuracion["x"]),
                valor_x=float(malla_x[fila, columna]),
                variable_y=str(configuracion["y"]),
                valor_y=float(malla_y[fila, columna]),
                humedad_suelo_fija=humedad_suelo_fija,
                temperatura_fija=temperatura_fija,
                humedad_ambiental_fija=humedad_ambiental_fija,
                velocidad_viento_fija=velocidad_viento_fija,
                tipo_cultivo=tipo_cultivo,
            )
            resultado = fuzzy_engine.calcular_riego_mamdani(**entradas)
            malla_z[fila, columna] = float(resultado[str(configuracion["z"])])

    fig = plt.figure(figsize=(9, 6.2))
    ax = fig.add_subplot(111, projection="3d")
    superficie_plot = ax.plot_surface(
        malla_x,
        malla_y,
        malla_z,
        cmap="YlGnBu",
        linewidth=0,
        antialiased=True,
        alpha=0.94,
    )
    ax.contour(
        malla_x,
        malla_y,
        malla_z,
        zdir="z",
        offset=float(np.nanmin(malla_z)),
        cmap="YlGnBu",
        alpha=0.45,
    )
    ax.set_title(f"Surface Viewer 3D\n{superficie}", pad=18)
    ax.set_xlabel(str(configuracion["x_label"]), labelpad=10)
    ax.set_ylabel(str(configuracion["y_label"]), labelpad=10)
    ax.set_zlabel(str(configuracion["z_label"]), labelpad=10)
    ax.view_init(elev=28, azim=-135)
    fig.colorbar(superficie_plot, ax=ax, shrink=0.65, pad=0.12, label=str(configuracion["z_label"]))
    fig.tight_layout()

    carpeta_salida = Path("assets") / "generated"
    carpeta_salida.mkdir(parents=True, exist_ok=True)
    ruta_png = carpeta_salida / f"surface_viewer_{uuid4().hex}.png"
    fig.savefig(ruta_png, dpi=170, bbox_inches="tight")

    resumen = (
        f"Superficie calculada con {resolucion} x {resolucion} = {resolucion * resolucion} "
        f"evaluaciones reales del motor Mamdani. Cultivo: {tipo_cultivo}. "
        f"Valores fijos usados cuando no son eje: humedad suelo {humedad_suelo_fija:g} %, "
        f"temperatura {temperatura_fija:g} C, humedad ambiental {humedad_ambiental_fija:g} %, "
        f"viento {velocidad_viento_fija:g} km/h."
    )
    return fig, str(ruta_png), resumen


def superficie_pendiente():
    """Muestra un grafico liviano hasta que el usuario genere la superficie 3D."""
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.text(
        0.5,
        0.5,
        "Seleccione una superficie y presione\nActualizar superficie",
        ha="center",
        va="center",
        fontsize=13,
        color="#14532d",
    )
    ax.set_axis_off()
    fig.tight_layout()
    return fig, None, "La superficie 3D se calculara cuando presione Actualizar superficie."


def cargar_tabla_historial() -> pd.DataFrame:
    """Carga el historial disponible desde CSV."""
    try:
        return history.leer_historial(RUTA_HISTORIAL)
    except Exception as error:
        return pd.DataFrame({"error": [str(error)]})


def guardar_evaluacion_historial(
    resultado: dict[str, Any] | None,
    humedad_suelo: float,
    temperatura: float,
    humedad_ambiental: float,
    velocidad_viento: float,
    tipo_cultivo: str,
) -> tuple[pd.DataFrame, str]:
    """Guarda la ultima evaluacion calculada en el historial CSV."""
    if not resultado:
        _, _, _, _, _, resultado = ejecutar_calculo(
            humedad_suelo,
            temperatura,
            humedad_ambiental,
            velocidad_viento,
            tipo_cultivo,
        )
    try:
        tabla = history.guardar_evaluacion(
            humedad_suelo=humedad_suelo,
            temperatura_ambiental=temperatura,
            humedad_ambiental=humedad_ambiental,
            velocidad_viento=velocidad_viento,
            tipo_cultivo=tipo_cultivo,
            resultado=resultado,
            ruta_csv=RUTA_HISTORIAL,
        )
        return tabla, "Evaluacion guardada correctamente en data/historial.csv."
    except Exception as error:
        return cargar_tabla_historial(), f"No se pudo guardar la evaluacion: {error}"


def descargar_historial_csv() -> str:
    """Devuelve el archivo CSV del historial para descarga."""
    return history.descargar_historial(RUTA_HISTORIAL)


def limpiar_historial_interfaz() -> tuple[pd.DataFrame, str]:
    """Limpia el historial desde la interfaz."""
    try:
        tabla = history.limpiar_historial(RUTA_HISTORIAL)
        return tabla, "Historial limpiado correctamente."
    except Exception as error:
        return cargar_tabla_historial(), f"No se pudo limpiar el historial: {error}"


def generar_reporte_interfaz(
    resultado: dict[str, Any] | None,
    humedad_suelo: float,
    temperatura: float,
    humedad_ambiental: float,
    velocidad_viento: float,
    tipo_cultivo: str,
) -> tuple[str | None, str]:
    """Genera el PDF solo si existe una evaluacion valida previa."""
    if not resultado:
        return None, "Primero realice una evaluacion valida antes de generar el reporte PDF."

    entradas_reporte = {
        "humedad_suelo": humedad_suelo,
        "temperatura": temperatura,
        "humedad_ambiental": humedad_ambiental,
        "velocidad_viento": velocidad_viento,
        "tipo_cultivo": tipo_cultivo,
    }
    try:
        ruta_pdf = report.generar_reporte_pdf(
            resultado=resultado,
            ruta_salida=Path("assets") / "reports",
            entradas=entradas_reporte,
        )
        return str(ruta_pdf), f"Reporte PDF generado: {ruta_pdf.name}"
    except Exception as error:
        return None, f"No se pudo generar el reporte PDF: {error}"


def crear_interfaz() -> gr.Blocks:
    """Construye la interfaz web completa en Gradio."""
    with gr.Blocks(title="Riego Difuso Mamdani") as demo:
        resultado_estado = gr.State({})
        gr.HTML(
            """
            <div class="site-brandbar">
                <div class="brand-lockup">
                    <div class="brand-mark">RI</div>
                    <div>
                        <div class="brand-name">Sistema Inteligente de Riego</div>
                        <div class="brand-subtitle">Universidad Cesar Vallejo - Ingenieria de Sistemas</div>
                    </div>
                </div>
            </div>
            """
        )

        with gr.Tab("Inicio"):
            gr.HTML(
                f"""
                <div class="hero">
                    <h1>{TITULO}</h1>
                    <p>
                        Plataforma academica para evaluar recomendaciones de riego usando
                        un Sistema de Inferencia Difusa Mamdani con cinco entradas,
                        tres salidas y una base de reglas explicable.
                    </p>
                </div>
                """
            )
            gr.HTML(
                """
                <div class="academic-grid">
                    <div class="academic-card">
                        <h3>Objetivo academico</h3>
                        <p>Diseñar un sistema inteligente que apoye la toma de decisiones de riego mediante logica difusa Mamdani.</p>
                    </div>
                    <div class="academic-card">
                        <h3>Variables evaluadas</h3>
                        <p>Humedad del suelo, temperatura ambiental, humedad ambiental, velocidad del viento y tipo de cultivo.</p>
                    </div>
                    <div class="academic-card">
                        <h3>Salidas del sistema</h3>
                        <p>Tiempo de riego, frecuencia de riego y caudal de agua calculados con inferencia difusa.</p>
                    </div>
                </div>
                <div class="section-heading">Modulos del proyecto</div>
                <div class="module-grid">
                    <div class="module-card">
                        <h3>Motor difuso</h3>
                        <p>Inferencia Mamdani completa con fuzzificacion, reglas, agregacion y centroide.</p>
                    </div>
                    <div class="module-card">
                        <h3>Funciones de pertenencia</h3>
                        <p>Funciones triangulares y trapezoidales para entradas y salidas del sistema.</p>
                    </div>
                    <div class="module-card">
                        <h3>Rule Viewer</h3>
                        <p>Vista educativa de reglas activadas, intensidad y consecuentes recortados.</p>
                    </div>
                    <div class="module-card">
                        <h3>Reportes</h3>
                        <p>Historial CSV y reporte PDF para documentar escenarios evaluados.</p>
                    </div>
                </div>
"""
            )

        with gr.Tab("Evaluar riego"):
            gr.Markdown("### Ingrese las condiciones actuales del cultivo")
            humedad_suelo, humedad_suelo_numero = crear_control_numerico(
                "Humedad del suelo (%)", 0, 100, 35, 1, 0
            )
            temperatura, temperatura_numero = crear_control_numerico(
                "Temperatura ambiental (C)", 0, 45, 28, 0.5, 1
            )
            humedad_ambiental, humedad_ambiental_numero = crear_control_numerico(
                "Humedad ambiental (%)", 0, 100, 55, 1, 0
            )
            velocidad_viento, velocidad_viento_numero = crear_control_numerico(
                "Velocidad del viento (km/h)", 0, 40, 12, 0.5, 1
            )
            with gr.Column(elem_classes=["input-card"]):
                gr.HTML("<div class='field-title'>Tipo de cultivo</div>")
                tipo_cultivo = gr.Dropdown(
                    CULTIVOS,
                    value="Tomate",
                    show_label=False,
                    filterable=False,
                    allow_custom_value=False,
                    buttons=[],
                    elem_id="tipo-cultivo-select",
                    elem_classes=["clean-dropdown"],
                )
            estado = gr.HTML(estado_proceso("Analizando condiciones"))
            salida_tiempo = gr.HTML(formatear_tarjeta("Tiempo de riego", "-", "minutos"))
            salida_frecuencia = gr.HTML(formatear_tarjeta("Frecuencia de riego", "-", "dias"))
            salida_caudal = gr.HTML(formatear_tarjeta("Caudal", "-", "L/min"))
            salida_interpretacion = gr.Textbox(
                label="Interpretacion del sistema",
                lines=5,
                interactive=False,
            )
            archivo_reporte_pdf = gr.File(label="Reporte PDF")
            mensaje_reporte_pdf = gr.Textbox(label="Estado del reporte", interactive=False)
            boton_calcular = gr.Button("Calcular riego inteligente", variant="primary")
            boton_procedimiento = gr.Button("Ver procedimiento Mamdani paso a paso")
            boton_reporte_pdf = gr.Button("Descargar reporte PDF")
            with gr.Column(
                elem_id="procedimiento-evaluacion-section",
                elem_classes=["procedure-section"],
                visible=False,
            ) as procedimiento_evaluacion_contenedor:
                procedimiento_desde_evaluacion = gr.Markdown(
                    sanitize_html=False,
                    latex_delimiters=[
                        {"left": "$$", "right": "$$", "display": True},
                        {"left": "\\[", "right": "\\]", "display": True},
                        {"left": "\\(", "right": "\\)", "display": False},
                    ],
                )

        with gr.Tab("Procedimiento Mamdani"):
            gr.Markdown("### Trazabilidad matematica del ultimo calculo")
            procedimiento_general = gr.Markdown(
                "Ejecute primero una evaluacion de riego.",
                sanitize_html=False,
                latex_delimiters=[
                    {"left": "$$", "right": "$$", "display": True},
                    {"left": "\\[", "right": "\\]", "display": True},
                    {"left": "\\(", "right": "\\)", "display": False},
                ],
            )

        with gr.Tab("Funciones de pertenencia"):
            with gr.Column(elem_classes=["section-card", "membership-panel"]):
                gr.Markdown("### Parametros y visualizacion de funciones de pertenencia")
                with gr.Row(elem_classes=["controls-grid"]):
                    selector_variable = gr.Dropdown(
                        choices=VARIABLES_MEMBRESIA,
                        value="humedad_suelo",
                        label="Variable difusa",
                        filterable=False,
                        allow_custom_value=False,
                        buttons=[],
                        elem_classes=["membership-combobox"],
                    )
                    selector_salida_agregada = gr.Dropdown(
                        choices=list(SALIDAS.keys()),
                        value="Tiempo de riego",
                        label="Salida agregada",
                        filterable=False,
                        allow_custom_value=False,
                        buttons=[],
                        elem_classes=["membership-combobox"],
                    )
                boton_actualizar_graficas = gr.Button("Actualizar graficas con valores ingresados", variant="primary")
            with gr.Column(elem_classes=["section-card", "plot-section"]):
                grafico_membresia = gr.Plot(label="Funciones de pertenencia")
            with gr.Column(elem_classes=["section-card", "plot-section"]):
                grafico_salida_agregada = gr.Plot(label="Salida agregada")
            with gr.Column(elem_classes=["section-card", "membership-table-card"]):
                gr.Markdown("### Tabla de parametros")
                tabla_parametros_membresia = gr.HTML(
                    value=tabla_parametros_variable_html("humedad_suelo"),
                    elem_classes=["membership-params-table"],
                )
            with gr.Column(elem_classes=["section-card", "math-note"]):
                gr.Markdown(
                    """
### Explicacion matematica
Las funciones trapezoidales se usan en los extremos para cubrir los limites del universo sin huecos.
Las funciones triangulares se usan en conjuntos intermedios para representar transiciones graduales.

Para una funcion triangular se evalua la subida hasta el punto central y luego la bajada hacia el limite superior.
Para una funcion trapezoidal se agrega una zona de pertenencia maxima donde el grado es 1.
"""
                )

        with gr.Tab("Base de reglas"):
            with gr.Column(elem_classes=["section-card", "rules-panel"]):
                gr.Markdown("### Base de reglas Mamdani")
                with gr.Row(elem_classes=["controls-grid"]):
                    filtro_regla = gr.Dropdown(
                        choices=opciones_filtro_reglas(),
                        value="Todas",
                        label="Filtrar por regla",
                        filterable=False,
                        allow_custom_value=False,
                        buttons=[],
                    )
                    busqueda_reglas = gr.Textbox(
                        label="Buscar",
                        placeholder="Buscar por antecedente, consecuente o explicacion",
                    )
                tabla_base_reglas = gr.Dataframe(
                    value=tabla_reglas,
                    interactive=False,
                    wrap=True,
                    max_height=650,
                    show_row_numbers=False,
                    elem_classes=["light-dataframe", "wide-dataframe", "rules-dataframe"],
                )

        with gr.Tab("Rule Viewer"):
            with gr.Column(elem_classes=["section-card", "rule-viewer-panel"]):
                gr.Markdown("### Rule Viewer educativo tipo Mamdani")
                gr.Markdown(
                    "El visor usa el ultimo resultado real calculado por `fuzzy_engine.py`: "
                    "fuzzificacion, reglas activadas, recortes Mamdani, agregacion y centroide."
                )
                boton_actualizar_rule_viewer = gr.Button("Actualizar Rule Viewer", variant="primary")
            with gr.Column(elem_classes=["section-card"]):
                rule_viewer_entradas = gr.Markdown("Ejecute una evaluacion para ver las entradas.")
            with gr.Column(elem_classes=["section-card"]):
                gr.Markdown("### Grados de pertenencia")
                rule_viewer_grados = gr.Markdown("Ejecute una evaluacion para ver los grados de pertenencia.")
            with gr.Column(elem_classes=["section-card"]):
                rule_viewer_resumen = gr.Markdown("Ejecute una evaluacion para ver la lectura educativa.")
            with gr.Column(elem_classes=["section-card"]):
                gr.Markdown("### Tabla de reglas activadas")
                rule_viewer_tabla = gr.Dataframe(
                    headers=[
                        "ID de regla",
                        "Regla linguistica",
                        "Grado de activacion",
                        "Tiempo de riego",
                        "Frecuencia",
                        "Caudal",
                    ],
                    interactive=False,
                    wrap=True,
                    max_height=560,
                    show_row_numbers=False,
                    elem_classes=["light-dataframe", "wide-dataframe", "rule-viewer-dataframe"],
                )
                rule_viewer_tabla_html = gr.HTML(visible=False)
            with gr.Column(elem_classes=["section-card"]):
                gr.Markdown("### Visor individual de reglas")
                selector_regla = gr.Dropdown(
                    choices=opciones_reglas(),
                    label="Regla",
                    filterable=False,
                    allow_custom_value=False,
                    buttons=[],
                )
                detalle_regla = gr.Markdown("Seleccione una regla para ver sus antecedentes y consecuentes.")
            with gr.Column(elem_classes=["section-card", "plot-section"]):
                gr.Markdown("### Graficos")
                rule_viewer_grafico = gr.Plot(label="Rule Viewer Mamdani")
            with gr.Column(elem_classes=["section-card", "final-reading"]):
                rule_viewer_interpretacion = gr.Markdown("Ejecute una evaluacion para ver la interpretacion final.")

        with gr.Tab("▼ Más"):
            with gr.Column(elem_classes=["section-card", "more-menu-card"]):
                selector_mas = gr.Dropdown(
                    choices=["Surface Viewer", "Historial", "Acerca del proyecto"],
                    value="Surface Viewer",
                    label="Seleccionar seccion",
                    filterable=False,
                    allow_custom_value=False,
                    buttons=[],
                )

            with gr.Column(elem_classes=["more-section"], visible=True) as seccion_surface:
                with gr.Column(elem_classes=["section-card", "surface-panel"]):
                    gr.Markdown("### Surface Viewer 3D")
                    gr.Markdown(
                        "Cada punto de la malla se calcula con `fuzzy_engine.py`; no se usan "
                        "formulas simplificadas ni valores inventados."
                    )
                    with gr.Row(elem_classes=["controls-grid"]):
                        superficie_surface = gr.Dropdown(
                            list(SUPERFICIES_3D.keys()),
                            value="Humedad del suelo vs temperatura ambiental -> tiempo de riego",
                            label="Superficie",
                            filterable=False,
                            allow_custom_value=False,
                            buttons=[],
                        )
                        cultivo_surface = gr.Dropdown(
                            CULTIVOS,
                            value="Tomate",
                            label="Cultivo",
                            filterable=False,
                            allow_custom_value=False,
                            buttons=[],
                        )
                    with gr.Row(elem_classes=["surface-fixed-grid"]):
                        with gr.Column():
                            humedad_suelo_surface = gr.Slider(0, 100, value=35, step=1, label="Humedad del suelo fija (%)")
                            temperatura_surface = gr.Slider(0, 45, value=28, step=0.5, label="Temperatura fija (C)")
                        with gr.Column():
                            humedad_surface = gr.Slider(0, 100, value=55, step=1, label="Humedad ambiental fija (%)")
                            viento_surface = gr.Slider(0, 40, value=12, step=0.5, label="Viento fijo (km/h)")
                    resolucion_surface = gr.Slider(
                        10,
                        25,
                        value=15,
                        step=1,
                        label="Resolucion de malla por eje",
                    )
                    boton_surface = gr.Button("Actualizar superficie", variant="primary")
                with gr.Column(elem_classes=["section-card", "plot-section", "surface-plot-card"]):
                    grafico_surface = gr.Plot()
                    archivo_surface = gr.File(label="Descargar imagen PNG")
                with gr.Column(elem_classes=["section-card"]):
                    resumen_surface = gr.Textbox(label="Resumen del calculo", interactive=False, lines=3)

            with gr.Column(elem_classes=["more-section"], visible=False) as seccion_historial:
                with gr.Column(elem_classes=["section-card", "history-panel"]):
                    gr.Markdown("### Historial de evaluaciones")
                    with gr.Row(elem_classes=["controls-grid"]):
                        boton_guardar_historial = gr.Button("Guardar evaluacion", variant="primary")
                        boton_descargar_historial = gr.Button("Descargar historial CSV")
                        boton_limpiar_historial = gr.Button("Limpiar historial")
                    mensaje_historial = gr.Textbox(label="Estado del historial", interactive=False)
                    tabla_historial = gr.Dataframe(
                        value=cargar_tabla_historial,
                        interactive=False,
                        wrap=True,
                        max_height=560,
                        show_row_numbers=False,
                        elem_classes=["light-dataframe", "wide-dataframe", "history-dataframe"],
                    )
                    archivo_historial = gr.File(label="Archivo CSV")
                    gr.Markdown(
                        "En servicios web como Render el almacenamiento puede reiniciarse segun el plan. "
                        "Descargue el historial CSV si desea conservarlo."
                    )

            with gr.Column(elem_classes=["more-section"], visible=False) as seccion_acerca:
                with gr.Column(elem_classes=["section-card", "about-panel"]):
                    gr.Markdown(
                        """
## Dise?o de un Sistema Inteligente para el Riego Autom?tico mediante L?gica Difusa Mamdani

### Datos acad?micos
**Universidad:** Universidad C?sar Vallejo
**Escuela:** Ingenier?a de Sistemas
**Curso:** Sistemas Inteligentes
**Unidad:** Unidad 3
**Asesor:** Tito Chura, Virgilio Fredy

### Autores
- Barrientos Romero, Samira Pamela
- Espinoza Huerta, Brennys Stefano
- Ramirez Bardales, Rober Kener
- Warthon Arratea, Sharonn Nicolle

### Enfoque ODS
**ODS 6:** Agua limpia y saneamiento
**Meta 6.4:** uso eficiente de los recursos h?dricos

### L?neas acad?micas
**L?nea de investigaci?n:** Sistemas de Informaci?n y Comunicaci?n
**L?nea de responsabilidad social universitaria:** Desarrollo sostenible y adaptaci?n al cambio clim?tico

### Explicaci?n breve del sistema
El sistema eval?a condiciones agr?colas como humedad del suelo, temperatura ambiental, humedad ambiental, velocidad del viento y tipo de cultivo. Con estas entradas calcula recomendaciones de tiempo de riego, frecuencia de riego y caudal de agua, buscando apoyar un uso m?s eficiente del recurso h?drico.

### M?todo Mamdani
El m?todo Mamdani transforma valores num?ricos en grados de pertenencia difusos, eval?a reglas ling??sticas del tipo SI...ENTONCES, recorta los consecuentes seg?n el grado de activaci?n, agrega las salidas con el operador m?ximo y obtiene valores finales mediante desfuzzificaci?n por centroide.

### Tecnolog?as utilizadas
Python, Gradio, NumPy, Pandas, Matplotlib, ReportLab y l?gica difusa implementada en CPU.
"""
                    )
        entradas = [humedad_suelo, temperatura, humedad_ambiental, velocidad_viento, tipo_cultivo]
        salidas_calculo = [
            salida_tiempo,
            salida_frecuencia,
            salida_caudal,
            salida_interpretacion,
            estado,
            resultado_estado,
        ]
        salidas_rule_viewer = [
            rule_viewer_entradas,
            rule_viewer_grados,
            rule_viewer_tabla,
            rule_viewer_tabla_html,
            rule_viewer_grafico,
            rule_viewer_resumen,
            rule_viewer_interpretacion,
        ]
        humedad_suelo.release(
            fn=lambda valor: limitar_valor_control(valor, 0, 100, 0),
            inputs=humedad_suelo,
            outputs=humedad_suelo_numero,
        )
        humedad_suelo_numero.change(
            fn=lambda valor: limitar_valor_control(valor, 0, 100, 0),
            inputs=humedad_suelo_numero,
            outputs=humedad_suelo,
        )
        temperatura.release(
            fn=lambda valor: limitar_valor_control(valor, 0, 45, 1),
            inputs=temperatura,
            outputs=temperatura_numero,
        )
        temperatura_numero.change(
            fn=lambda valor: limitar_valor_control(valor, 0, 45, 1),
            inputs=temperatura_numero,
            outputs=temperatura,
        )
        humedad_ambiental.release(
            fn=lambda valor: limitar_valor_control(valor, 0, 100, 0),
            inputs=humedad_ambiental,
            outputs=humedad_ambiental_numero,
        )
        humedad_ambiental_numero.change(
            fn=lambda valor: limitar_valor_control(valor, 0, 100, 0),
            inputs=humedad_ambiental_numero,
            outputs=humedad_ambiental,
        )
        velocidad_viento.release(
            fn=lambda valor: limitar_valor_control(valor, 0, 40, 1),
            inputs=velocidad_viento,
            outputs=velocidad_viento_numero,
        )
        velocidad_viento_numero.change(
            fn=lambda valor: limitar_valor_control(valor, 0, 40, 1),
            inputs=velocidad_viento_numero,
            outputs=velocidad_viento,
        )
        evento_calculo = boton_calcular.click(fn=ejecutar_calculo, inputs=entradas, outputs=salidas_calculo)
        evento_calculo.then(
            fn=actualizar_rule_viewer,
            inputs=[resultado_estado, *entradas],
            outputs=salidas_rule_viewer,
        )
        boton_actualizar_rule_viewer.click(
            fn=actualizar_rule_viewer,
            inputs=[resultado_estado, *entradas],
            outputs=salidas_rule_viewer,
        )
        selector_mas.change(
            fn=mostrar_seccion_mas,
            inputs=selector_mas,
            outputs=[seccion_surface, seccion_historial, seccion_acerca],
        )
        filtro_regla.change(
            fn=filtrar_tabla_reglas,
            inputs=[filtro_regla, busqueda_reglas],
            outputs=tabla_base_reglas,
        )
        busqueda_reglas.change(
            fn=filtrar_tabla_reglas,
            inputs=[filtro_regla, busqueda_reglas],
            outputs=tabla_base_reglas,
        )
        boton_guardar_historial.click(
            fn=guardar_evaluacion_historial,
            inputs=[resultado_estado, *entradas],
            outputs=[tabla_historial, mensaje_historial],
        )
        boton_reporte_pdf.click(
            fn=generar_reporte_interfaz,
            inputs=[resultado_estado, *entradas],
            outputs=[archivo_reporte_pdf, mensaje_reporte_pdf],
        )
        boton_descargar_historial.click(
            fn=descargar_historial_csv,
            outputs=archivo_historial,
        )
        boton_limpiar_historial.click(
            fn=limpiar_historial_interfaz,
            outputs=[tabla_historial, mensaje_historial],
        )
        boton_procedimiento.click(
            fn=mostrar_procedimiento_evaluacion,
            inputs=[resultado_estado, *entradas],
            outputs=[procedimiento_desde_evaluacion, procedimiento_evaluacion_contenedor],
        ).then(
            fn=generar_procedimiento,
            inputs=[resultado_estado, *entradas],
            outputs=procedimiento_general,
        )
        entradas_grafico_membresia = [
            selector_variable,
            humedad_suelo,
            temperatura,
            humedad_ambiental,
            velocidad_viento,
            tipo_cultivo,
        ]
        entradas_grafico_agregado = [
            resultado_estado,
            selector_salida_agregada,
            humedad_suelo,
            temperatura,
            humedad_ambiental,
            velocidad_viento,
            tipo_cultivo,
        ]
        selector_variable.change(
            fn=graficar_membresia,
            inputs=entradas_grafico_membresia,
            outputs=grafico_membresia,
        )
        selector_variable.change(
            fn=tabla_parametros_variable_html,
            inputs=selector_variable,
            outputs=tabla_parametros_membresia,
        )
        selector_salida_agregada.change(
            fn=graficar_salida_agregada_interfaz,
            inputs=entradas_grafico_agregado,
            outputs=grafico_salida_agregada,
        )
        boton_actualizar_graficas.click(
            fn=graficar_membresia,
            inputs=entradas_grafico_membresia,
            outputs=grafico_membresia,
        ).then(
            fn=graficar_salida_agregada_interfaz,
            inputs=entradas_grafico_agregado,
            outputs=grafico_salida_agregada,
        ).then(
            fn=tabla_parametros_variable_html,
            inputs=selector_variable,
            outputs=tabla_parametros_membresia,
        )
        demo.load(fn=graficar_membresia, inputs=entradas_grafico_membresia, outputs=grafico_membresia)
        demo.load(
            fn=graficar_salida_agregada_interfaz,
            inputs=entradas_grafico_agregado,
            outputs=grafico_salida_agregada,
        )
        selector_regla.change(fn=ver_regla, inputs=selector_regla, outputs=detalle_regla)
        boton_surface.click(
            fn=graficar_superficie,
            inputs=[
                superficie_surface,
                cultivo_surface,
                humedad_suelo_surface,
                temperatura_surface,
                humedad_surface,
                viento_surface,
                resolucion_surface,
            ],
            outputs=[grafico_surface, archivo_surface, resumen_surface],
        )
        demo.load(fn=superficie_pendiente, outputs=[grafico_surface, archivo_surface, resumen_surface])
        demo.load(
            fn=actualizar_rule_viewer,
            inputs=[resultado_estado, *entradas],
            outputs=salidas_rule_viewer,
        )

        _ = (charts, report)

    return demo


if __name__ == "__main__":
    demo = crear_interfaz()
    port = int(os.environ.get("PORT", 7860))
    demo.launch(server_name="0.0.0.0", server_port=port, css=cargar_css(), theme=crear_tema_claro())
