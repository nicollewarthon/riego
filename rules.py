"""Base de reglas difusas Mamdani para el sistema de riego automatico.

Las reglas fueron disenadas de forma representativa, no como una
expansion automatica de todas las combinaciones posibles. Cada regla
incluye antecedentes, operador logico, consecuentes, texto legible y una
explicacion breve para trazabilidad academica.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal


OperadorLogico = Literal["AND", "OR"]


@dataclass(frozen=True)
class Antecedente:
    """Condicion difusa de entrada usada en una regla."""

    variable: str
    conjunto: str


@dataclass(frozen=True)
class Consecuentes:
    """Salidas linguisticas recomendadas por una regla."""

    tiempo_riego: str
    frecuencia_riego: str
    caudal_agua: str


@dataclass(frozen=True)
class ReglaDifusa:
    """Regla Mamdani declarativa y facil de recorrer."""

    identificador: str
    antecedentes: tuple[Antecedente, ...]
    operador_logico: OperadorLogico
    consecuentes: Consecuentes
    texto: str
    explicacion: str


REGLAS_DIFUSAS: tuple[ReglaDifusa, ...] = (
    ReglaDifusa(
        "R01",
        (Antecedente("humedad_suelo", "muy_seca"),),
        "AND",
        Consecuentes("muy_largo", "muy_frecuente", "alto"),
        "SI humedad del suelo es muy seca ENTONCES tiempo muy largo, frecuencia muy frecuente y caudal alto.",
        "La falta extrema de agua en el suelo exige una respuesta de riego maxima.",
    ),
    ReglaDifusa(
        "R02",
        (Antecedente("humedad_suelo", "seca"),),
        "AND",
        Consecuentes("largo", "frecuente", "medio"),
        "SI humedad del suelo es seca ENTONCES tiempo largo, frecuencia frecuente y caudal medio.",
        "Un suelo seco requiere aumentar el riego, pero sin llegar al maximo absoluto.",
    ),
    ReglaDifusa(
        "R03",
        (Antecedente("humedad_suelo", "humeda"),),
        "AND",
        Consecuentes("corto", "normal", "bajo"),
        "SI humedad del suelo es humeda ENTONCES tiempo corto, frecuencia normal y caudal bajo.",
        "La humedad disponible permite mantener el riego en un nivel conservador.",
    ),
    ReglaDifusa(
        "R04",
        (Antecedente("humedad_suelo", "muy_humeda"),),
        "AND",
        Consecuentes("muy_corto", "esporadica", "bajo"),
        "SI humedad del suelo es muy humeda ENTONCES tiempo muy corto, frecuencia esporadica y caudal bajo.",
        "El exceso de humedad reduce el riego al minimo para evitar saturacion.",
    ),
    ReglaDifusa(
        "R05",
        (
            Antecedente("humedad_suelo", "muy_seca"),
            Antecedente("temperatura_ambiental", "alta"),
        ),
        "AND",
        Consecuentes("muy_largo", "muy_frecuente", "alto"),
        "SI humedad del suelo es muy seca Y temperatura ambiental es alta ENTONCES riego maximo.",
        "El calor acelera la evaporacion y agrava la sequedad del suelo.",
    ),
    ReglaDifusa(
        "R06",
        (
            Antecedente("humedad_suelo", "seca"),
            Antecedente("temperatura_ambiental", "alta"),
        ),
        "AND",
        Consecuentes("muy_largo", "frecuente", "alto"),
        "SI humedad del suelo es seca Y temperatura ambiental es alta ENTONCES tiempo muy largo, frecuencia frecuente y caudal alto.",
        "El calor aumenta la demanda hidrica aun cuando la sequedad no sea extrema.",
    ),
    ReglaDifusa(
        "R07",
        (
            Antecedente("temperatura_ambiental", "alta"),
            Antecedente("velocidad_viento", "alta"),
        ),
        "AND",
        Consecuentes("largo", "frecuente", "alto"),
        "SI temperatura ambiental es alta Y velocidad del viento es alta ENTONCES tiempo largo, frecuencia frecuente y caudal alto.",
        "La combinacion de calor y viento eleva la evapotranspiracion.",
    ),
    ReglaDifusa(
        "R08",
        (
            Antecedente("temperatura_ambiental", "alta"),
            Antecedente("humedad_ambiental", "baja"),
        ),
        "AND",
        Consecuentes("largo", "frecuente", "alto"),
        "SI temperatura ambiental es alta Y humedad ambiental es baja ENTONCES tiempo largo, frecuencia frecuente y caudal alto.",
        "El ambiente seco favorece perdida de agua por evaporacion.",
    ),
    ReglaDifusa(
        "R09",
        (
            Antecedente("humedad_suelo", "seca"),
            Antecedente("velocidad_viento", "alta"),
        ),
        "AND",
        Consecuentes("muy_largo", "frecuente", "alto"),
        "SI humedad del suelo es seca Y velocidad del viento es alta ENTONCES tiempo muy largo, frecuencia frecuente y caudal alto.",
        "El viento incrementa la perdida superficial de humedad.",
    ),
    ReglaDifusa(
        "R10",
        (
            Antecedente("humedad_suelo", "humeda"),
            Antecedente("temperatura_ambiental", "alta"),
            Antecedente("velocidad_viento", "alta"),
        ),
        "AND",
        Consecuentes("medio", "normal", "medio"),
        "SI suelo humedo Y temperatura alta Y viento alto ENTONCES tiempo medio, frecuencia normal y caudal medio.",
        "Aunque el suelo conserva humedad, las condiciones climaticas justifican compensacion moderada.",
    ),
    ReglaDifusa(
        "R11",
        (
            Antecedente("humedad_suelo", "muy_humeda"),
            Antecedente("temperatura_ambiental", "alta"),
        ),
        "AND",
        Consecuentes("corto", "normal", "bajo"),
        "SI suelo muy humedo Y temperatura alta ENTONCES tiempo corto, frecuencia normal y caudal bajo.",
        "El calor no debe causar riego excesivo cuando el suelo ya esta saturado.",
    ),
    ReglaDifusa(
        "R12",
        (
            Antecedente("humedad_ambiental", "alta"),
            Antecedente("humedad_suelo", "seca"),
        ),
        "AND",
        Consecuentes("medio", "normal", "medio"),
        "SI humedad ambiental alta Y suelo seco ENTONCES tiempo medio, frecuencia normal y caudal medio.",
        "La humedad ambiental alta reduce moderadamente la necesidad de riego.",
    ),
    ReglaDifusa(
        "R13",
        (
            Antecedente("humedad_ambiental", "alta"),
            Antecedente("humedad_suelo", "humeda"),
        ),
        "AND",
        Consecuentes("muy_corto", "esporadica", "bajo"),
        "SI humedad ambiental alta Y suelo humedo ENTONCES tiempo muy corto, frecuencia esporadica y caudal bajo.",
        "Ambas condiciones indican baja perdida de agua.",
    ),
    ReglaDifusa(
        "R14",
        (
            Antecedente("humedad_ambiental", "baja"),
            Antecedente("humedad_suelo", "seca"),
        ),
        "AND",
        Consecuentes("muy_largo", "frecuente", "alto"),
        "SI humedad ambiental baja Y suelo seco ENTONCES tiempo muy largo, frecuencia frecuente y caudal alto.",
        "Un ambiente seco intensifica el deficit hidrico del cultivo.",
    ),
    ReglaDifusa(
        "R15",
        (
            Antecedente("temperatura_ambiental", "baja"),
            Antecedente("humedad_suelo", "humeda"),
        ),
        "AND",
        Consecuentes("muy_corto", "normal", "bajo"),
        "SI temperatura baja Y suelo humedo ENTONCES tiempo muy corto, frecuencia normal y caudal bajo.",
        "Con baja evaporacion, el sistema puede reducir el aporte de agua.",
    ),
    ReglaDifusa(
        "R16",
        (
            Antecedente("temperatura_ambiental", "baja"),
            Antecedente("humedad_ambiental", "alta"),
        ),
        "AND",
        Consecuentes("muy_corto", "esporadica", "bajo"),
        "SI temperatura baja Y humedad ambiental alta ENTONCES riego minimo.",
        "El riesgo de evaporacion es bajo y se evita sobrehumedecer el suelo.",
    ),
    ReglaDifusa(
        "R17",
        (
            Antecedente("velocidad_viento", "baja"),
            Antecedente("humedad_suelo", "humeda"),
        ),
        "AND",
        Consecuentes("corto", "normal", "bajo"),
        "SI viento bajo Y suelo humedo ENTONCES tiempo corto, frecuencia normal y caudal bajo.",
        "El viento bajo conserva humedad y no exige aumentar el caudal.",
    ),
    ReglaDifusa(
        "R18",
        (
            Antecedente("velocidad_viento", "media"),
            Antecedente("humedad_suelo", "seca"),
        ),
        "AND",
        Consecuentes("largo", "frecuente", "medio"),
        "SI viento medio Y suelo seco ENTONCES tiempo largo, frecuencia frecuente y caudal medio.",
        "El viento medio aumenta la demanda, pero no tanto como viento alto.",
    ),
    ReglaDifusa(
        "R19",
        (
            Antecedente("humedad_suelo", "muy_seca"),
            Antecedente("tipo_cultivo", "lechuga"),
        ),
        "AND",
        Consecuentes("muy_largo", "muy_frecuente", "alto"),
        "SI suelo muy seco Y cultivo lechuga ENTONCES riego maximo.",
        "La lechuga es sensible a la falta de humedad.",
    ),
    ReglaDifusa(
        "R20",
        (
            Antecedente("humedad_suelo", "seca"),
            Antecedente("tipo_cultivo", "lechuga"),
        ),
        "AND",
        Consecuentes("muy_largo", "muy_frecuente", "medio"),
        "SI suelo seco Y cultivo lechuga ENTONCES tiempo muy largo, frecuencia muy frecuente y caudal medio.",
        "La lechuga demanda humedad constante aun con sequedad moderada.",
    ),
    ReglaDifusa(
        "R21",
        (
            Antecedente("humedad_suelo", "muy_seca"),
            Antecedente("tipo_cultivo", "fresa"),
        ),
        "AND",
        Consecuentes("muy_largo", "muy_frecuente", "alto"),
        "SI suelo muy seco Y cultivo fresa ENTONCES riego maximo.",
        "La fresa requiere protegerse de deficit hidrico pronunciado.",
    ),
    ReglaDifusa(
        "R22",
        (
            Antecedente("humedad_suelo", "seca"),
            Antecedente("tipo_cultivo", "fresa"),
        ),
        "AND",
        Consecuentes("largo", "muy_frecuente", "medio"),
        "SI suelo seco Y cultivo fresa ENTONCES tiempo largo, frecuencia muy frecuente y caudal medio.",
        "La fresa se beneficia de riegos frecuentes sin caudal excesivo.",
    ),
    ReglaDifusa(
        "R23",
        (
            Antecedente("humedad_suelo", "seca"),
            Antecedente("tipo_cultivo", "tomate"),
        ),
        "AND",
        Consecuentes("largo", "frecuente", "alto"),
        "SI suelo seco Y cultivo tomate ENTONCES tiempo largo, frecuencia frecuente y caudal alto.",
        "El tomate se considera de demanda media-alta.",
    ),
    ReglaDifusa(
        "R24",
        (
            Antecedente("temperatura_ambiental", "alta"),
            Antecedente("tipo_cultivo", "tomate"),
        ),
        "AND",
        Consecuentes("largo", "frecuente", "medio"),
        "SI temperatura alta Y cultivo tomate ENTONCES tiempo largo, frecuencia frecuente y caudal medio.",
        "El tomate incrementa su demanda bajo calor.",
    ),
    ReglaDifusa(
        "R25",
        (
            Antecedente("humedad_suelo", "seca"),
            Antecedente("tipo_cultivo", "maiz"),
        ),
        "AND",
        Consecuentes("largo", "frecuente", "medio"),
        "SI suelo seco Y cultivo maiz ENTONCES tiempo largo, frecuencia frecuente y caudal medio.",
        "El maiz se modela con demanda hidrica media.",
    ),
    ReglaDifusa(
        "R26",
        (
            Antecedente("humedad_suelo", "muy_seca"),
            Antecedente("tipo_cultivo", "maiz"),
        ),
        "AND",
        Consecuentes("muy_largo", "frecuente", "alto"),
        "SI suelo muy seco Y cultivo maiz ENTONCES tiempo muy largo, frecuencia frecuente y caudal alto.",
        "La sequedad extrema requiere subir el aporte incluso en cultivos de demanda media.",
    ),
    ReglaDifusa(
        "R27",
        (
            Antecedente("humedad_suelo", "seca"),
            Antecedente("tipo_cultivo", "papa"),
        ),
        "AND",
        Consecuentes("medio", "frecuente", "medio"),
        "SI suelo seco Y cultivo papa ENTONCES tiempo medio, frecuencia frecuente y caudal medio.",
        "La papa se considera de demanda media y se evita saturacion.",
    ),
    ReglaDifusa(
        "R28",
        (
            Antecedente("humedad_suelo", "muy_seca"),
            Antecedente("tipo_cultivo", "papa"),
        ),
        "AND",
        Consecuentes("largo", "frecuente", "medio"),
        "SI suelo muy seco Y cultivo papa ENTONCES tiempo largo, frecuencia frecuente y caudal medio.",
        "Se compensa el deficit sin aplicar caudal maximo por sensibilidad a exceso de agua.",
    ),
    ReglaDifusa(
        "R29",
        (
            Antecedente("humedad_suelo", "humeda"),
            Antecedente("tipo_cultivo", "lechuga"),
        ),
        "AND",
        Consecuentes("medio", "frecuente", "bajo"),
        "SI suelo humedo Y cultivo lechuga ENTONCES tiempo medio, frecuencia frecuente y caudal bajo.",
        "La lechuga mantiene necesidad frecuente aunque el suelo no este seco.",
    ),
    ReglaDifusa(
        "R30",
        (
            Antecedente("humedad_suelo", "humeda"),
            Antecedente("tipo_cultivo", "fresa"),
        ),
        "AND",
        Consecuentes("corto", "frecuente", "bajo"),
        "SI suelo humedo Y cultivo fresa ENTONCES tiempo corto, frecuencia frecuente y caudal bajo.",
        "La fresa requiere continuidad de humedad con bajo volumen.",
    ),
    ReglaDifusa(
        "R31",
        (
            Antecedente("humedad_suelo", "muy_humeda"),
            Antecedente("tipo_cultivo", "lechuga"),
        ),
        "AND",
        Consecuentes("muy_corto", "normal", "bajo"),
        "SI suelo muy humedo Y cultivo lechuga ENTONCES tiempo muy corto, frecuencia normal y caudal bajo.",
        "Aunque sea sensible, no conviene regar en exceso con suelo muy humedo.",
    ),
    ReglaDifusa(
        "R32",
        (
            Antecedente("humedad_suelo", "muy_humeda"),
            Antecedente("tipo_cultivo", "fresa"),
        ),
        "AND",
        Consecuentes("muy_corto", "normal", "bajo"),
        "SI suelo muy humedo Y cultivo fresa ENTONCES tiempo muy corto, frecuencia normal y caudal bajo.",
        "Se protege el cultivo evitando saturacion.",
    ),
    ReglaDifusa(
        "R33",
        (
            Antecedente("humedad_suelo", "muy_humeda"),
            Antecedente("humedad_ambiental", "alta"),
        ),
        "AND",
        Consecuentes("muy_corto", "esporadica", "bajo"),
        "SI suelo muy humedo Y humedad ambiental alta ENTONCES riego minimo.",
        "La combinacion indica baja necesidad de reposicion de agua.",
    ),
    ReglaDifusa(
        "R34",
        (
            Antecedente("temperatura_ambiental", "media"),
            Antecedente("humedad_suelo", "seca"),
        ),
        "AND",
        Consecuentes("largo", "frecuente", "medio"),
        "SI temperatura media Y suelo seco ENTONCES tiempo largo, frecuencia frecuente y caudal medio.",
        "Condicion comun donde el deficit del suelo domina la decision.",
    ),
    ReglaDifusa(
        "R35",
        (
            Antecedente("temperatura_ambiental", "media"),
            Antecedente("humedad_suelo", "humeda"),
        ),
        "AND",
        Consecuentes("corto", "normal", "bajo"),
        "SI temperatura media Y suelo humedo ENTONCES tiempo corto, frecuencia normal y caudal bajo.",
        "Condicion estable que requiere mantenimiento limitado.",
    ),
    ReglaDifusa(
        "R36",
        (
            Antecedente("velocidad_viento", "alta"),
            Antecedente("humedad_ambiental", "baja"),
        ),
        "AND",
        Consecuentes("largo", "frecuente", "alto"),
        "SI viento alto Y humedad ambiental baja ENTONCES tiempo largo, frecuencia frecuente y caudal alto.",
        "El viento seco produce perdida rapida de humedad.",
    ),
    ReglaDifusa(
        "R37",
        (
            Antecedente("temperatura_ambiental", "alta"),
            Antecedente("velocidad_viento", "alta"),
            Antecedente("humedad_ambiental", "baja"),
        ),
        "AND",
        Consecuentes("muy_largo", "muy_frecuente", "alto"),
        "SI temperatura alta Y viento alto Y humedad ambiental baja ENTONCES riego maximo.",
        "Es el escenario climatico de mayor demanda hidrica.",
    ),
    ReglaDifusa(
        "R38",
        (
            Antecedente("humedad_suelo", "muy_seca"),
            Antecedente("temperatura_ambiental", "alta"),
            Antecedente("velocidad_viento", "alta"),
        ),
        "AND",
        Consecuentes("muy_largo", "muy_frecuente", "alto"),
        "SI suelo muy seco Y temperatura alta Y viento alto ENTONCES riego maximo.",
        "Combina deficit del suelo con condiciones climaticas criticas.",
    ),
    ReglaDifusa(
        "R39",
        (
            Antecedente("humedad_suelo", "muy_humeda"),
            Antecedente("temperatura_ambiental", "baja"),
        ),
        "OR",
        Consecuentes("muy_corto", "esporadica", "bajo"),
        "SI suelo muy humedo O temperatura baja ENTONCES tiempo muy corto, frecuencia esporadica y caudal bajo.",
        "Cualquiera de estas condiciones reduce la necesidad inmediata de riego.",
    ),
    ReglaDifusa(
        "R40",
        (
            Antecedente("humedad_suelo", "muy_seca"),
            Antecedente("humedad_ambiental", "baja"),
            Antecedente("velocidad_viento", "alta"),
        ),
        "OR",
        Consecuentes("largo", "frecuente", "alto"),
        "SI suelo muy seco O humedad ambiental baja O viento alto ENTONCES tiempo largo, frecuencia frecuente y caudal alto.",
        "Cualquiera de estas senales puede justificar aumento preventivo del riego.",
    ),
)


def obtener_reglas_difusas() -> list[ReglaDifusa]:
    """Devuelve todas las reglas difusas Mamdani definidas."""
    return list(REGLAS_DIFUSAS)


def convertir_regla_a_texto(regla: ReglaDifusa) -> str:
    """Convierte una regla en una descripcion legible tipo SI...ENTONCES."""
    antecedentes = f" {regla.operador_logico} ".join(
        f"{antecedente.variable} es {antecedente.conjunto}"
        for antecedente in regla.antecedentes
    )
    return (
        f"{regla.identificador}: SI {antecedentes} ENTONCES "
        f"tiempo_riego es {regla.consecuentes.tiempo_riego}, "
        f"frecuencia_riego es {regla.consecuentes.frecuencia_riego}, "
        f"caudal_agua es {regla.consecuentes.caudal_agua}."
    )


def calcular_grado_activacion(
    regla: ReglaDifusa,
    grados_entrada: dict[str, dict[str, float]],
) -> float:
    """Calcula el grado de activacion de una regla usando MIN para AND y MAX para OR."""
    grados_antecedentes = []

    for antecedente in regla.antecedentes:
        try:
            grado = grados_entrada[antecedente.variable][antecedente.conjunto]
        except KeyError as error:
            raise KeyError(
                f"Falta el grado de pertenencia para "
                f"{antecedente.variable}.{antecedente.conjunto}"
            ) from error
        grados_antecedentes.append(float(grado))

    if not grados_antecedentes:
        return 0.0

    if regla.operador_logico == "AND":
        return min(grados_antecedentes)
    if regla.operador_logico == "OR":
        return max(grados_antecedentes)

    raise ValueError(f"Operador logico no soportado: {regla.operador_logico}")


def filtrar_reglas_activadas(
    grados_entrada: dict[str, dict[str, float]],
    umbral: float = 0.0,
) -> list[tuple[ReglaDifusa, float]]:
    """Devuelve reglas con grado de activacion mayor que el umbral indicado."""
    activadas = []
    for regla in REGLAS_DIFUSAS:
        grado = calcular_grado_activacion(regla, grados_entrada)
        if grado > umbral:
            activadas.append((regla, grado))

    return sorted(activadas, key=lambda item: item[1], reverse=True)


def mostrar_grado_activacion(
    regla: ReglaDifusa,
    grados_entrada: dict[str, dict[str, float]],
) -> str:
    """Devuelve el texto de una regla junto con su grado de activacion."""
    grado = calcular_grado_activacion(regla, grados_entrada)
    return f"{regla.identificador} | grado={grado:.3f} | {convertir_regla_a_texto(regla)}"


def obtener_tabla_reglas() -> list[dict[str, str]]:
    """Devuelve la base de reglas como tabla serializable."""
    tabla = []
    for regla in REGLAS_DIFUSAS:
        tabla.append(
            {
                "id": regla.identificador,
                "antecedentes": f" {regla.operador_logico} ".join(
                    f"{antecedente.variable}:{antecedente.conjunto}"
                    for antecedente in regla.antecedentes
                ),
                "operador": regla.operador_logico,
                "tiempo_riego": regla.consecuentes.tiempo_riego,
                "frecuencia_riego": regla.consecuentes.frecuencia_riego,
                "caudal_agua": regla.consecuentes.caudal_agua,
                "explicacion": regla.explicacion,
            }
        )
    return tabla


def verificar_cobertura_reglas() -> dict[str, bool]:
    """Verifica cobertura basica de escenarios relevantes del sistema."""
    texto_reglas = " ".join(
        f"{regla.texto} {regla.explicacion}".lower()
        for regla in REGLAS_DIFUSAS
    )
    cultivos = ["lechuga", "tomate", "maiz", "papa", "fresa"]

    return {
        "escenarios_secos": "muy seca" in texto_reglas or "suelo seco" in texto_reglas,
        "escenarios_humedos": "muy humed" in texto_reglas or "suelo humedo" in texto_reglas,
        "escenarios_calurosos": "temperatura alta" in texto_reglas,
        "escenarios_ventosos": "viento alto" in texto_reglas,
        "distintos_cultivos": all(cultivo in texto_reglas for cultivo in cultivos),
        "cantidad_valida": 35 <= len(REGLAS_DIFUSAS) <= 50,
    }


def ejecutar_pruebas_simples() -> None:
    """Ejecuta verificaciones estructurales de la base de reglas."""
    cobertura = verificar_cobertura_reglas()
    faltantes = [nombre for nombre, existe in cobertura.items() if not existe]
    if faltantes:
        raise AssertionError(f"Cobertura insuficiente en reglas: {', '.join(faltantes)}")

    for regla in REGLAS_DIFUSAS:
        if not regla.identificador or not regla.antecedentes:
            raise AssertionError(f"Regla incompleta: {regla}")
        if regla.operador_logico not in {"AND", "OR"}:
            raise AssertionError(f"Operador invalido en {regla.identificador}")


if __name__ == "__main__":
    ejecutar_pruebas_simples()
    print(f"Base de reglas verificada correctamente: {len(REGLAS_DIFUSAS)} reglas.")
