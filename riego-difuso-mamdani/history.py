"""Manejo del historial de evaluaciones del sistema de riego.

El historial se guarda en ``data/historial.csv``. En Hugging Face Spaces
este archivo puede perderse si el entorno se reinicia, por lo que la
interfaz permite descargar el CSV.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd


RUTA_HISTORIAL_PREDETERMINADA = Path("data") / "historial.csv"

COLUMNAS_HISTORIAL = [
    "fecha_hora",
    "humedad_suelo",
    "temperatura_ambiental",
    "humedad_ambiental",
    "velocidad_viento",
    "tipo_cultivo",
    "tiempo_riego",
    "frecuencia",
    "caudal",
    "reglas_principales_activadas",
]


def asegurar_archivo_historial(ruta_csv: Path = RUTA_HISTORIAL_PREDETERMINADA) -> None:
    """Crea el archivo de historial con cabeceras si no existe."""
    ruta_csv.parent.mkdir(parents=True, exist_ok=True)
    if not ruta_csv.exists():
        pd.DataFrame(columns=COLUMNAS_HISTORIAL).to_csv(ruta_csv, index=False)


def leer_historial(ruta_csv: Path = RUTA_HISTORIAL_PREDETERMINADA) -> pd.DataFrame:
    """Lee el historial CSV y garantiza las columnas esperadas."""
    asegurar_archivo_historial(ruta_csv)
    try:
        datos = pd.read_csv(ruta_csv)
    except (OSError, pd.errors.ParserError) as error:
        raise RuntimeError(f"No se pudo leer el historial: {error}") from error

    for columna in COLUMNAS_HISTORIAL:
        if columna not in datos.columns:
            datos[columna] = pd.NA
    return datos[COLUMNAS_HISTORIAL]


def _resumir_reglas_principales(resultado: dict[str, Any], limite: int = 5) -> str:
    """Resume las reglas con mayor activacion en una cadena compacta."""
    reglas = resultado.get("reglas_activadas", [])
    reglas_ordenadas = sorted(
        reglas,
        key=lambda regla: float(regla.get("grado_activacion", 0)),
        reverse=True,
    )
    resumen = [
        f"{regla['id']}({float(regla['grado_activacion']):.3f})"
        for regla in reglas_ordenadas[:limite]
    ]
    return "; ".join(resumen)


def guardar_evaluacion(
    humedad_suelo: float,
    temperatura_ambiental: float,
    humedad_ambiental: float,
    velocidad_viento: float,
    tipo_cultivo: str,
    resultado: dict[str, Any],
    ruta_csv: Path = RUTA_HISTORIAL_PREDETERMINADA,
) -> pd.DataFrame:
    """Guarda una evaluacion completa y devuelve el historial actualizado."""
    if not resultado:
        raise ValueError("No hay resultado calculado para guardar.")

    registro = {
        "fecha_hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "humedad_suelo": float(humedad_suelo),
        "temperatura_ambiental": float(temperatura_ambiental),
        "humedad_ambiental": float(humedad_ambiental),
        "velocidad_viento": float(velocidad_viento),
        "tipo_cultivo": str(tipo_cultivo),
        "tiempo_riego": float(resultado["tiempo_riego"]),
        "frecuencia": float(resultado["frecuencia_riego"]),
        "caudal": float(resultado["caudal_agua"]),
        "reglas_principales_activadas": _resumir_reglas_principales(resultado),
    }

    historial = leer_historial(ruta_csv)
    nuevo_registro = pd.DataFrame([registro], columns=COLUMNAS_HISTORIAL)
    if historial.empty:
        historial = nuevo_registro
    else:
        historial = pd.concat([historial, nuevo_registro], ignore_index=True)

    try:
        historial.to_csv(ruta_csv, index=False)
    except OSError as error:
        raise RuntimeError(f"No se pudo guardar la evaluacion: {error}") from error

    return historial


def descargar_historial(ruta_csv: Path = RUTA_HISTORIAL_PREDETERMINADA) -> str:
    """Devuelve la ruta del CSV para descargarlo desde Gradio."""
    asegurar_archivo_historial(ruta_csv)
    return str(ruta_csv)


def limpiar_historial(ruta_csv: Path = RUTA_HISTORIAL_PREDETERMINADA) -> pd.DataFrame:
    """Limpia el historial y conserva solo las cabeceras."""
    ruta_csv.parent.mkdir(parents=True, exist_ok=True)
    historial_vacio = pd.DataFrame(columns=COLUMNAS_HISTORIAL)
    try:
        historial_vacio.to_csv(ruta_csv, index=False)
    except OSError as error:
        raise RuntimeError(f"No se pudo limpiar el historial: {error}") from error
    return historial_vacio


def cargar_historial(ruta_csv: Path) -> pd.DataFrame:
    """Alias de compatibilidad para llamadas anteriores."""
    return leer_historial(ruta_csv)


def guardar_registro(ruta_csv: Path, registro: dict[str, Any]) -> None:
    """Guarda un registro ya construido en el historial CSV."""
    historial = leer_historial(ruta_csv)
    registro_normalizado = {columna: registro.get(columna, pd.NA) for columna in COLUMNAS_HISTORIAL}
    nuevo_registro = pd.DataFrame([registro_normalizado], columns=COLUMNAS_HISTORIAL)
    if historial.empty:
        historial = nuevo_registro
    else:
        historial = pd.concat([historial, nuevo_registro], ignore_index=True)
    historial.to_csv(ruta_csv, index=False)
