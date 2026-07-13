"""Utilidades para generar graficas del sistema difuso.

Las graficas usan Matplotlib y no requieren GPU. Se apoyan en las
definiciones de ``membership.py`` para mantener una sola fuente de verdad
de universos, conjuntos y funciones de pertenencia.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.figure import Figure
from numpy.typing import NDArray

import membership


COLOR_LINEA_VALOR = "#dc2626"
COLOR_CENTROIDE = "#1d4ed8"
COLOR_AREA = "#2f9e44"


def _obtener_unidad(nombre_variable: str) -> str:
    """Devuelve la unidad documentada para una variable difusa."""
    variable = membership.obtener_variable(nombre_variable)
    return variable.unidad


def _formatear_grados(nombre_variable: str, valor: float) -> str:
    """Convierte los grados de pertenencia de un valor en texto de leyenda."""
    grados = membership.calcular_grados_variable(nombre_variable, valor)
    return "\n".join(f"{nombre}: {grado:.3f}" for nombre, grado in grados.items())


def graficar_variable(nombre_variable: str, valor: float | None = None) -> Figure:
    """Grafica todas las funciones de pertenencia de una variable.

    Args:
        nombre_variable: Nombre tecnico de la variable definida en ``membership.py``.
        valor: Valor opcional ingresado por el usuario. Si se proporciona, se marca
            con una linea vertical y se muestran sus grados de pertenencia.

    Returns:
        Figura Matplotlib lista para mostrarse en Gradio.
    """
    variable = membership.obtener_variable(nombre_variable)
    universos = membership.crear_universos()
    funciones = membership.crear_funciones_membresia(universos)
    universo = universos[nombre_variable]

    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    for conjunto, grados in funciones[nombre_variable].items():
        ax.plot(universo, grados, linewidth=2.2, label=conjunto.replace("_", " "))

    if valor is not None:
        membership.validar_rango_variable(nombre_variable, valor)
        ax.axvline(
            valor,
            color=COLOR_LINEA_VALOR,
            linestyle="--",
            linewidth=2,
            label=f"valor ingresado = {valor:g} {variable.unidad}",
        )
        texto_grados = _formatear_grados(nombre_variable, valor)
        ax.text(
            0.985,
            0.04,
            texto_grados,
            transform=ax.transAxes,
            ha="right",
            va="bottom",
            fontsize=8.5,
            bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#cbd5e1"},
        )

    ax.set_title(f"Funciones de pertenencia - {variable.nombre}")
    ax.set_xlabel(f"{variable.nombre} ({_obtener_unidad(nombre_variable)})")
    ax.set_ylabel("Grado de pertenencia μ(x)")
    ax.set_ylim(-0.05, 1.05)
    ax.set_xlim(float(np.min(universo)), float(np.max(universo)))
    ax.grid(True, alpha=0.28)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=3, frameon=False)
    fig.tight_layout()
    return fig


def graficar_salida_agregada(
    nombre_salida: str,
    universo: list[float] | NDArray[np.float64],
    funcion_agregada: list[float] | NDArray[np.float64],
    centroide: float,
) -> Figure:
    """Grafica una salida agregada y su valor crisp final.

    La funcion sombreada representa ``mu_agregada(z)`` y la linea vertical
    marca el centroide calculado por el motor Mamdani.
    """
    variable = membership.obtener_variable(nombre_salida)
    universo_np = np.asarray(universo, dtype=float)
    agregada_np = np.asarray(funcion_agregada, dtype=float)

    if universo_np.shape != agregada_np.shape:
        raise ValueError("El universo y la funcion agregada deben tener la misma longitud.")
    membership.validar_rango_variable(nombre_salida, centroide)

    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    ax.plot(universo_np, agregada_np, color=COLOR_AREA, linewidth=2.2, label="μ agregada")
    ax.fill_between(universo_np, agregada_np, color=COLOR_AREA, alpha=0.28)
    ax.axvline(
        centroide,
        color=COLOR_CENTROIDE,
        linestyle="--",
        linewidth=2.2,
        label=f"centroide = {centroide:.3f} {variable.unidad}",
    )
    ax.scatter([centroide], [0], color=COLOR_CENTROIDE, s=42, zorder=5)

    ax.set_title(f"Salida agregada - {variable.nombre}")
    ax.set_xlabel(f"{variable.nombre} ({variable.unidad})")
    ax.set_ylabel("Grado de pertenencia μ(z)")
    ax.set_ylim(-0.05, 1.05)
    ax.set_xlim(float(np.min(universo_np)), float(np.max(universo_np)))
    ax.grid(True, alpha=0.28)
    ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.16), ncol=2, frameon=False)
    ax.text(
        0.985,
        0.92,
        f"Valor crisp final\n{centroide:.3f} {variable.unidad}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=9,
        bbox={"boxstyle": "round,pad=0.35", "facecolor": "white", "edgecolor": "#cbd5e1"},
    )
    fig.tight_layout()
    return fig


def graficar_funciones_membresia(datos_membresia: dict[str, Any], ruta_salida: Path) -> Path:
    """Genera una grafica de membresia y la guarda en disco.

    Se conserva esta funcion por compatibilidad con llamadas previas.
    ``datos_membresia`` debe incluir ``nombre_variable`` y opcionalmente ``valor``.
    """
    nombre_variable = str(datos_membresia["nombre_variable"])
    valor = datos_membresia.get("valor")
    fig = graficar_variable(nombre_variable, valor)
    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta_salida, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return ruta_salida


def graficar_historial(ruta_historial: Path, ruta_salida: Path) -> Path:
    """Genera una grafica simple del historial de mediciones y recomendaciones."""
    if not ruta_historial.exists():
        raise FileNotFoundError(f"No existe el historial: {ruta_historial}")

    datos = pd.read_csv(ruta_historial)
    if datos.empty:
        raise ValueError("El historial esta vacio; no hay datos para graficar.")

    fig, ax = plt.subplots(figsize=(8.6, 4.8))
    columnas_numericas = [
        columna for columna in datos.columns if pd.api.types.is_numeric_dtype(datos[columna])
    ]
    if not columnas_numericas:
        raise ValueError("El historial no contiene columnas numericas para graficar.")

    for columna in columnas_numericas:
        ax.plot(datos.index, datos[columna], marker="o", linewidth=1.8, label=columna)

    ax.set_title("Historial de mediciones y recomendaciones")
    ax.set_xlabel("Registro")
    ax.set_ylabel("Valor")
    ax.grid(True, alpha=0.28)
    ax.legend()
    fig.tight_layout()

    ruta_salida.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(ruta_salida, dpi=160, bbox_inches="tight")
    plt.close(fig)
    return ruta_salida
