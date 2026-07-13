"""Funciones de membresia para el sistema de riego difuso Mamdani.

El modulo define universos, conjuntos difusos y utilidades reutilizables
para calcular grados de pertenencia.

Formulas usadas:

Funcion triangular, con parametros ``a <= b <= c``:

    mu(x) = 0                         si x <= a o x >= c
    mu(x) = (x - a) / (b - a)         si a < x < b
    mu(x) = 1                         si x = b
    mu(x) = (c - x) / (c - b)         si b < x < c

Funcion trapezoidal, con parametros ``a <= b <= c <= d``:

    mu(x) = 0                         si x < a o x > d
    mu(x) = (x - a) / (b - a)         si a < x < b
    mu(x) = 1                         si b <= x <= c
    mu(x) = (d - x) / (d - c)         si c < x < d

En los extremos se usan trapecios de hombro para representar saturacion
inferior o superior. Los conjuntos intermedios son triangulares.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
from numpy.typing import NDArray


TipoFuncion = Literal["triangular", "trapezoidal"]


@dataclass(frozen=True)
class DefinicionMembresia:
    """Representa una funcion de pertenencia difusa."""

    nombre: str
    tipo: TipoFuncion
    parametros: tuple[float, ...]


@dataclass(frozen=True)
class VariableDifusa:
    """Representa una variable linguistica y sus conjuntos difusos."""

    nombre: str
    minimo: float
    maximo: float
    paso: float
    unidad: str
    conjuntos: tuple[DefinicionMembresia, ...]


CULTIVOS_CODIFICADOS: dict[str, int] = {
    "lechuga": 0,
    "tomate": 1,
    "maiz": 2,
    "papa": 3,
    "fresa": 4,
}


VARIABLES_DIFUSAS: dict[str, VariableDifusa] = {
    "humedad_suelo": VariableDifusa(
        nombre="Humedad del suelo",
        minimo=0,
        maximo=100,
        paso=1,
        unidad="%",
        conjuntos=(
            DefinicionMembresia("muy_seca", "trapezoidal", (0, 0, 15, 30)),
            DefinicionMembresia("seca", "triangular", (20, 40, 60)),
            DefinicionMembresia("humeda", "triangular", (50, 65, 80)),
            DefinicionMembresia("muy_humeda", "trapezoidal", (70, 85, 100, 100)),
        ),
    ),
    "temperatura_ambiental": VariableDifusa(
        nombre="Temperatura ambiental",
        minimo=0,
        maximo=45,
        paso=0.5,
        unidad="C",
        conjuntos=(
            DefinicionMembresia("baja", "trapezoidal", (0, 0, 10, 18)),
            DefinicionMembresia("media", "triangular", (15, 24, 33)),
            DefinicionMembresia("alta", "trapezoidal", (30, 36, 45, 45)),
        ),
    ),
    "humedad_ambiental": VariableDifusa(
        nombre="Humedad ambiental",
        minimo=0,
        maximo=100,
        paso=1,
        unidad="%",
        conjuntos=(
            DefinicionMembresia("baja", "trapezoidal", (0, 0, 30, 45)),
            DefinicionMembresia("media", "triangular", (35, 55, 75)),
            DefinicionMembresia("alta", "trapezoidal", (65, 80, 100, 100)),
        ),
    ),
    "velocidad_viento": VariableDifusa(
        nombre="Velocidad del viento",
        minimo=0,
        maximo=40,
        paso=0.5,
        unidad="km/h",
        conjuntos=(
            DefinicionMembresia("baja", "trapezoidal", (0, 0, 8, 15)),
            DefinicionMembresia("media", "triangular", (10, 20, 30)),
            DefinicionMembresia("alta", "trapezoidal", (25, 32, 40, 40)),
        ),
    ),
    "tipo_cultivo": VariableDifusa(
        nombre="Tipo de cultivo",
        minimo=0,
        maximo=4,
        paso=0.01,
        unidad="codigo",
        conjuntos=(
            DefinicionMembresia("lechuga", "trapezoidal", (0, 0, 0.25, 0.75)),
            DefinicionMembresia("tomate", "triangular", (0.25, 1, 1.75)),
            DefinicionMembresia("maiz", "triangular", (1.25, 2, 2.75)),
            DefinicionMembresia("papa", "triangular", (2.25, 3, 3.75)),
            DefinicionMembresia("fresa", "trapezoidal", (3.25, 3.75, 4, 4)),
        ),
    ),
    "tiempo_riego": VariableDifusa(
        nombre="Tiempo de riego",
        minimo=0,
        maximo=60,
        paso=1,
        unidad="min",
        conjuntos=(
            DefinicionMembresia("muy_corto", "trapezoidal", (0, 0, 5, 12)),
            DefinicionMembresia("corto", "triangular", (8, 17, 26)),
            DefinicionMembresia("medio", "triangular", (22, 30, 38)),
            DefinicionMembresia("largo", "triangular", (34, 43, 52)),
            DefinicionMembresia("muy_largo", "trapezoidal", (48, 55, 60, 60)),
        ),
    ),
    "frecuencia_riego": VariableDifusa(
        nombre="Frecuencia de riego",
        minimo=1,
        maximo=7,
        paso=0.1,
        unidad="dias",
        conjuntos=(
            DefinicionMembresia("muy_frecuente", "trapezoidal", (1, 1, 1.5, 2.5)),
            DefinicionMembresia("frecuente", "triangular", (2, 3, 4)),
            DefinicionMembresia("normal", "triangular", (3.5, 4.75, 6)),
            DefinicionMembresia("esporadica", "trapezoidal", (5.5, 6.25, 7, 7)),
        ),
    ),
    "caudal_agua": VariableDifusa(
        nombre="Caudal de agua",
        minimo=0,
        maximo=20,
        paso=0.5,
        unidad="L/min",
        conjuntos=(
            DefinicionMembresia("bajo", "trapezoidal", (0, 0, 4, 8)),
            DefinicionMembresia("medio", "triangular", (6, 10, 14)),
            DefinicionMembresia("alto", "trapezoidal", (12, 16, 20, 20)),
        ),
    ),
}


def funcion_triangular(valor: float, a: float, b: float, c: float) -> float:
    """Calcula ``mu(x)`` para una funcion triangular."""
    if not a <= b <= c:
        raise ValueError("Los parametros triangulares deben cumplir a <= b <= c.")

    x = float(valor)
    if x <= a or x >= c:
        return 0.0
    if x == b:
        return 1.0
    if a < x < b:
        return (x - a) / (b - a)
    return (c - x) / (c - b)


def funcion_trapezoidal(valor: float, a: float, b: float, c: float, d: float) -> float:
    """Calcula ``mu(x)`` para una funcion trapezoidal."""
    if not a <= b <= c <= d:
        raise ValueError("Los parametros trapezoidales deben cumplir a <= b <= c <= d.")

    x = float(valor)
    if x < a or x > d:
        return 0.0
    if b <= x <= c:
        return 1.0
    if a < x < b:
        return 1.0 if a == b else (x - a) / (b - a)
    if c < x < d:
        return 1.0 if c == d else (d - x) / (d - c)
    return 0.0


def obtener_variable(nombre_variable: str) -> VariableDifusa:
    """Obtiene la definicion de una variable difusa por nombre tecnico."""
    try:
        return VARIABLES_DIFUSAS[nombre_variable]
    except KeyError as error:
        disponibles = ", ".join(VARIABLES_DIFUSAS)
        raise KeyError(f"Variable no definida: {nombre_variable}. Disponibles: {disponibles}") from error


def validar_rango_variable(nombre_variable: str, valor: float) -> None:
    """Valida que un valor pertenezca al universo definido para la variable."""
    variable = obtener_variable(nombre_variable)

    if not variable.minimo <= float(valor) <= variable.maximo:
        raise ValueError(
            f"{variable.nombre} debe estar entre {variable.minimo:g} y "
            f"{variable.maximo:g} {variable.unidad}."
        )


def calcular_grado_pertenencia(definicion: DefinicionMembresia, valor: float) -> float:
    """Calcula el grado de pertenencia de un valor en un conjunto difuso."""
    if definicion.tipo == "triangular":
        grado = funcion_triangular(valor, *definicion.parametros)
    elif definicion.tipo == "trapezoidal":
        grado = funcion_trapezoidal(valor, *definicion.parametros)
    else:
        raise ValueError(f"Tipo de funcion no soportado: {definicion.tipo}")

    return max(0.0, min(1.0, grado))


def calcular_grados_variable(nombre_variable: str, valor: float) -> dict[str, float]:
    """Devuelve todos los grados de pertenencia para una variable concreta."""
    validar_rango_variable(nombre_variable, valor)
    variable = obtener_variable(nombre_variable)

    return {
        conjunto.nombre: calcular_grado_pertenencia(conjunto, valor)
        for conjunto in variable.conjuntos
    }


def calcular_grados_entrada(
    humedad_suelo: float,
    temperatura_ambiental: float,
    humedad_ambiental: float,
    velocidad_viento: float,
    tipo_cultivo: float,
) -> dict[str, dict[str, float]]:
    """Calcula todos los grados de pertenencia de una entrada completa."""
    valores = {
        "humedad_suelo": humedad_suelo,
        "temperatura_ambiental": temperatura_ambiental,
        "humedad_ambiental": humedad_ambiental,
        "velocidad_viento": velocidad_viento,
        "tipo_cultivo": tipo_cultivo,
    }
    return {
        nombre: calcular_grados_variable(nombre, valor)
        for nombre, valor in valores.items()
    }


def codificar_cultivo(nombre_cultivo: str) -> int:
    """Convierte el nombre de un cultivo en su codigo numerico documentado."""
    clave = nombre_cultivo.strip().lower()
    try:
        return CULTIVOS_CODIFICADOS[clave]
    except KeyError as error:
        disponibles = ", ".join(CULTIVOS_CODIFICADOS)
        raise ValueError(f"Cultivo no soportado: {nombre_cultivo}. Disponibles: {disponibles}") from error


def crear_universos() -> dict[str, NDArray[np.float64]]:
    """Crea los universos numericos de todas las variables del sistema."""
    return {
        nombre: np.arange(variable.minimo, variable.maximo + variable.paso, variable.paso)
        for nombre, variable in VARIABLES_DIFUSAS.items()
    }


def crear_funciones_membresia(
    universos: dict[str, NDArray[np.float64]] | None = None,
) -> dict[str, dict[str, NDArray[np.float64]]]:
    """Crea arreglos de membresia para cada conjunto difuso de cada universo."""
    universos = crear_universos() if universos is None else universos
    funciones: dict[str, dict[str, NDArray[np.float64]]] = {}

    for nombre_variable, universo in universos.items():
        variable = obtener_variable(nombre_variable)
        funciones[nombre_variable] = {}
        for conjunto in variable.conjuntos:
            funciones[nombre_variable][conjunto.nombre] = np.array(
                [calcular_grado_pertenencia(conjunto, valor) for valor in universo],
                dtype=float,
            )

    return funciones


def obtener_tabla_parametros() -> list[dict[str, str]]:
    """Devuelve una tabla serializable con los parametros de cada funcion."""
    tabla = []
    for nombre_variable, variable in VARIABLES_DIFUSAS.items():
        for conjunto in variable.conjuntos:
            tabla.append(
                {
                    "variable": nombre_variable,
                    "conjunto": conjunto.nombre,
                    "tipo": conjunto.tipo,
                    "parametros": ", ".join(f"{valor:g}" for valor in conjunto.parametros),
                    "universo": f"{variable.minimo:g} a {variable.maximo:g} {variable.unidad}",
                }
            )
    return tabla


def ejecutar_pruebas_simples() -> None:
    """Verifica que los grados calculados esten siempre entre 0 y 1."""
    universos = crear_universos()
    funciones = crear_funciones_membresia(universos)

    for nombre_variable, conjuntos in funciones.items():
        for nombre_conjunto, grados in conjuntos.items():
            if np.any(grados < 0) or np.any(grados > 1):
                raise AssertionError(
                    f"Grados fuera de rango en {nombre_variable}.{nombre_conjunto}"
                )

    ejemplo = calcular_grados_entrada(
        humedad_suelo=35,
        temperatura_ambiental=28,
        humedad_ambiental=60,
        velocidad_viento=18,
        tipo_cultivo=codificar_cultivo("tomate"),
    )
    for nombre_variable, grados in ejemplo.items():
        for nombre_conjunto, grado in grados.items():
            if not 0 <= grado <= 1:
                raise AssertionError(
                    f"Grado fuera de rango en {nombre_variable}.{nombre_conjunto}: {grado}"
                )


if __name__ == "__main__":
    ejecutar_pruebas_simples()
    print("Pruebas simples de membresia completadas correctamente.")
