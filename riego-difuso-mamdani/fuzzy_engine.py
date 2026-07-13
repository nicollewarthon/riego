"""Motor principal de inferencia difusa Mamdani.

Flujo implementado:

1. Validacion de entradas.
2. Fuzzificacion.
3. Evaluacion de reglas.
4. Activacion de antecedentes.
5. Implicacion Mamdani por recorte.
6. Agregacion por maximo.
7. Desfuzzificacion por centroide.
8. Interpretacion textual.

Formulas documentadas:

Funcion triangular:
    mu(x;a,b,c) = max(min((x-a)/(b-a), (c-x)/(c-b)), 0)

Funcion trapezoidal:
    mu(x;a,b,c,d) = max(min((x-a)/(b-a), 1, (d-x)/(d-c)), 0)

Activacion de regla:
    alpha = min(mu1, mu2, ..., mun)

Implicacion Mamdani:
    mu'_B(z) = min(alpha, mu_B(z))

Agregacion:
    mu_agregada(z) = max(mu'_B1(z), mu'_B2(z), ...)

Centroide:
    z* = Sum[z_i * mu(z_i)] / Sum[mu(z_i)]
"""

from __future__ import annotations

import unicodedata
from typing import Any

import numpy as np
from numpy.typing import NDArray

from membership import (
    CULTIVOS_CODIFICADOS,
    calcular_grados_entrada,
    codificar_cultivo,
    crear_funciones_membresia,
    crear_universos,
    validar_rango_variable,
)
from rules import (
    ReglaDifusa,
    calcular_grado_activacion,
    convertir_regla_a_texto,
    filtrar_reglas_activadas,
    obtener_reglas_difusas,
)


SALIDAS_DIFUSAS = ("tiempo_riego", "frecuencia_riego", "caudal_agua")


def normalizar_texto(texto: str) -> str:
    """Normaliza texto de entrada para aceptar tildes y mayusculas."""
    texto_ascii = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return texto_ascii.strip().lower()


def resolver_tipo_cultivo(tipo_cultivo: str | int | float) -> float:
    """Convierte el cultivo a codigo numerico o valida un codigo recibido."""
    if isinstance(tipo_cultivo, str):
        cultivo_normalizado = normalizar_texto(tipo_cultivo)
        try:
            return float(codificar_cultivo(cultivo_normalizado))
        except ValueError as error:
            disponibles = ", ".join(CULTIVOS_CODIFICADOS)
            raise ValueError(f"Tipo de cultivo invalido. Use: {disponibles}.") from error

    try:
        codigo = float(tipo_cultivo)
    except (TypeError, ValueError) as error:
        raise ValueError("Tipo de cultivo invalido. Debe ser nombre o codigo numerico.") from error

    validar_rango_variable("tipo_cultivo", codigo)
    return codigo


def validar_entradas(
    humedad_suelo: float,
    temperatura: float,
    humedad_ambiental: float,
    velocidad_viento: float,
    tipo_cultivo: str | int | float,
) -> dict[str, float]:
    """Valida entradas numericas y devuelve valores listos para fuzzificar."""
    valores = {
        "humedad_suelo": float(humedad_suelo),
        "temperatura_ambiental": float(temperatura),
        "humedad_ambiental": float(humedad_ambiental),
        "velocidad_viento": float(velocidad_viento),
        "tipo_cultivo": resolver_tipo_cultivo(tipo_cultivo),
    }

    for nombre_variable, valor in valores.items():
        validar_rango_variable(nombre_variable, valor)

    return valores


def fuzzificar_entradas(valores: dict[str, float]) -> dict[str, dict[str, float]]:
    """Calcula grados de pertenencia para las cinco entradas del sistema."""
    return calcular_grados_entrada(
        humedad_suelo=valores["humedad_suelo"],
        temperatura_ambiental=valores["temperatura_ambiental"],
        humedad_ambiental=valores["humedad_ambiental"],
        velocidad_viento=valores["velocidad_viento"],
        tipo_cultivo=valores["tipo_cultivo"],
    )


def obtener_consecuente(regla: ReglaDifusa, salida: str) -> str:
    """Obtiene el conjunto consecuente de una salida para una regla."""
    if salida == "tiempo_riego":
        return regla.consecuentes.tiempo_riego
    if salida == "frecuencia_riego":
        return regla.consecuentes.frecuencia_riego
    if salida == "caudal_agua":
        return regla.consecuentes.caudal_agua
    raise KeyError(f"Salida difusa no soportada: {salida}")


def evaluar_reglas(
    grados_pertenencia: dict[str, dict[str, float]],
) -> list[dict[str, Any]]:
    """Evalua reglas y devuelve solo las reglas activadas."""
    reglas_activadas = filtrar_reglas_activadas(grados_pertenencia, umbral=0.0)
    if not reglas_activadas:
        raise RuntimeError("Ninguna regla fue activada con las entradas proporcionadas.")

    return [
        {
            "id": regla.identificador,
            "grado_activacion": grado,
            "operador": regla.operador_logico,
            "antecedentes": [
                {"variable": antecedente.variable, "conjunto": antecedente.conjunto}
                for antecedente in regla.antecedentes
            ],
            "consecuentes": {
                "tiempo_riego": regla.consecuentes.tiempo_riego,
                "frecuencia_riego": regla.consecuentes.frecuencia_riego,
                "caudal_agua": regla.consecuentes.caudal_agua,
            },
            "texto": convertir_regla_a_texto(regla),
            "explicacion": regla.explicacion,
            "_regla": regla,
        }
        for regla, grado in reglas_activadas
    ]


def aplicar_implicacion_y_agregacion(
    reglas_activadas: list[dict[str, Any]],
    universos: dict[str, NDArray[np.float64]],
    funciones_membresia: dict[str, dict[str, NDArray[np.float64]]],
) -> dict[str, NDArray[np.float64]]:
    """Aplica recorte Mamdani y agrega las salidas con operador MAX."""
    agregados = {
        salida: np.zeros_like(universos[salida], dtype=float)
        for salida in SALIDAS_DIFUSAS
    }

    for registro in reglas_activadas:
        regla = registro["_regla"]
        alpha = float(registro["grado_activacion"])
        for salida in SALIDAS_DIFUSAS:
            nombre_conjunto = obtener_consecuente(regla, salida)
            funcion_salida = funciones_membresia[salida][nombre_conjunto]
            funcion_recortada = np.minimum(alpha, funcion_salida)
            agregados[salida] = np.maximum(agregados[salida], funcion_recortada)

    return agregados


def desfuzzificar_centroide(
    universo: NDArray[np.float64],
    membresia_agregada: NDArray[np.float64],
    nombre_salida: str,
) -> float:
    """Calcula el valor crisp usando el metodo del centroide."""
    denominador = float(np.sum(membresia_agregada))
    if denominador == 0:
        raise ZeroDivisionError(
            f"No se puede desfuzzificar {nombre_salida}: denominador cero en el centroide."
        )

    numerador = float(np.sum(universo * membresia_agregada))
    return numerador / denominador


def interpretar_resultado(
    tiempo_riego: float,
    frecuencia_riego: float,
    caudal_agua: float,
    reglas_activadas: list[dict[str, Any]],
) -> str:
    """Genera una interpretacion textual a partir de los resultados calculados."""
    regla_principal = max(reglas_activadas, key=lambda regla: regla["grado_activacion"])
    return (
        f"El motor Mamdani recomienda regar durante {tiempo_riego:.2f} minutos, "
        f"cada {frecuencia_riego:.2f} dias, con un caudal aproximado de "
        f"{caudal_agua:.2f} L/min. La regla con mayor activacion fue "
        f"{regla_principal['id']} con grado {regla_principal['grado_activacion']:.3f}: "
        f"{regla_principal['explicacion']}"
    )


def construir_pasos_matematicos(reglas_activadas: list[dict[str, Any]]) -> dict[str, str]:
    """Resume las formulas usadas durante la inferencia."""
    cantidad_reglas = len(reglas_activadas)
    return {
        "fuzzificacion": (
            "Se calculan grados con funciones triangulares y trapezoidales: "
            "mu_triangular(x;a,b,c)=max(min((x-a)/(b-a),(c-x)/(c-b)),0) y "
            "mu_trapezoidal(x;a,b,c,d)=max(min((x-a)/(b-a),1,(d-x)/(d-c)),0)."
        ),
        "activacion": (
            "Para cada regla AND se usa alpha=min(mu1,mu2,...,mun); "
            "para reglas OR se usa max(mu1,mu2,...,mun)."
        ),
        "implicacion": "Cada consecuente se recorta con mu'_B(z)=min(alpha,mu_B(z)).",
        "agregacion": (
            f"Se agregaron {cantidad_reglas} reglas activadas mediante "
            "mu_agregada(z)=max(mu'_B1(z),mu'_B2(z),...)."
        ),
        "desfuzzificacion": "Se aplica centroide: z*=Sum[z_i*mu(z_i)]/Sum[mu(z_i)].",
    }


def serializar_agregados(
    universos: dict[str, NDArray[np.float64]],
    agregados: dict[str, NDArray[np.float64]],
) -> dict[str, dict[str, list[float]]]:
    """Convierte universos y membresias agregadas a listas simples."""
    return {
        salida: {
            "universo": universos[salida].round(4).tolist(),
            "membresia": agregados[salida].round(6).tolist(),
        }
        for salida in SALIDAS_DIFUSAS
    }


def calcular_riego_mamdani(
    humedad_suelo: float,
    temperatura: float,
    humedad_ambiental: float,
    velocidad_viento: float,
    tipo_cultivo: str | int | float,
) -> dict[str, Any]:
    """Ejecuta el sistema completo de inferencia difusa Mamdani."""
    valores = validar_entradas(
        humedad_suelo=humedad_suelo,
        temperatura=temperatura,
        humedad_ambiental=humedad_ambiental,
        velocidad_viento=velocidad_viento,
        tipo_cultivo=tipo_cultivo,
    )
    grados_pertenencia = fuzzificar_entradas(valores)
    reglas_activadas = evaluar_reglas(grados_pertenencia)
    universos = crear_universos()
    funciones_membresia = crear_funciones_membresia(universos)
    agregados = aplicar_implicacion_y_agregacion(reglas_activadas, universos, funciones_membresia)

    tiempo_riego = desfuzzificar_centroide(
        universos["tiempo_riego"], agregados["tiempo_riego"], "tiempo_riego"
    )
    frecuencia_riego = desfuzzificar_centroide(
        universos["frecuencia_riego"], agregados["frecuencia_riego"], "frecuencia_riego"
    )
    caudal_agua = desfuzzificar_centroide(
        universos["caudal_agua"], agregados["caudal_agua"], "caudal_agua"
    )

    reglas_salida = [
        {clave: valor for clave, valor in regla.items() if clave != "_regla"}
        for regla in reglas_activadas
    ]
    grados_activacion = {
        regla["id"]: float(regla["grado_activacion"])
        for regla in reglas_salida
    }

    return {
        "tiempo_riego": round(tiempo_riego, 4),
        "frecuencia_riego": round(frecuencia_riego, 4),
        "caudal_agua": round(caudal_agua, 4),
        "grados_pertenencia": grados_pertenencia,
        "reglas_activadas": reglas_salida,
        "grados_activacion": grados_activacion,
        "conjuntos_agregados": serializar_agregados(universos, agregados),
        "pasos_matematicos": construir_pasos_matematicos(reglas_activadas),
        "interpretacion": interpretar_resultado(
            tiempo_riego=tiempo_riego,
            frecuencia_riego=frecuencia_riego,
            caudal_agua=caudal_agua,
            reglas_activadas=reglas_activadas,
        ),
    }


def ejecutar_pruebas_simples() -> None:
    """Ejecuta pruebas con cinco escenarios representativos."""
    escenarios = [
        {
            "nombre": "Suelo muy seco y temperatura alta",
            "entradas": (10, 38, 35, 12, "lechuga"),
        },
        {
            "nombre": "Suelo humedo",
            "entradas": (65, 24, 55, 8, "maiz"),
        },
        {
            "nombre": "Viento fuerte",
            "entradas": (45, 29, 35, 36, "tomate"),
        },
        {
            "nombre": "Humedad ambiental alta",
            "entradas": (50, 22, 90, 10, "papa"),
        },
        {
            "nombre": "Cultivo distinto sensible",
            "entradas": (42, 27, 50, 18, "fresa"),
        },
    ]

    for escenario in escenarios:
        resultado = calcular_riego_mamdani(*escenario["entradas"])
        for salida in SALIDAS_DIFUSAS:
            if resultado[salida] <= 0:
                raise AssertionError(f"Resultado invalido en {escenario['nombre']}: {salida}")
        if not resultado["reglas_activadas"]:
            raise AssertionError(f"Sin reglas activadas en {escenario['nombre']}")
        print(
            f"{escenario['nombre']}: "
            f"tiempo={resultado['tiempo_riego']:.2f}, "
            f"frecuencia={resultado['frecuencia_riego']:.2f}, "
            f"caudal={resultado['caudal_agua']:.2f}, "
            f"reglas={len(resultado['reglas_activadas'])}"
        )

    reglas_definidas = obtener_reglas_difusas()
    if not reglas_definidas:
        raise AssertionError("No existen reglas difusas definidas.")


if __name__ == "__main__":
    ejecutar_pruebas_simples()
