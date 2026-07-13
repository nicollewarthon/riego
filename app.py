"""Interfaz web profesional para el sistema de riego difuso Mamdani.

Aplicacion preparada para CPU basica y despliegue como servicio web en Render.
"""

from __future__ import annotations

import os
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


CSS = """
:root {
    --verde: #1f7a4d;
    --verde-claro: #e8f5ed;
    --azul: #1f6f9f;
    --azul-claro: #eaf5fb;
    --gris: #000000;
    --gris-suave: #000000;
}
.gradio-container {
    max-width: 1180px !important;
    margin: 0 auto !important;
    background: linear-gradient(180deg, #f7fbf8 0%, #ffffff 45%) !important;
    color: var(--gris) !important;
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
    color: var(--gris) !important;
}
.gradio-container h1,
.gradio-container h2,
.gradio-container h3,
.gradio-container h4 {
    color: #000000 !important;
}
.gradio-container *,
.gradio-container *::before,
.gradio-container *::after {
    color: #000000 !important;
}
.gradio-container .block,
.gradio-container .form,
.gradio-container .panel,
.gradio-container textarea,
.gradio-container input,
.gradio-container select {
    background: #ffffff !important;
}
.gradio-container textarea,
.gradio-container input,
.gradio-container select {
    border-color: #94a3b8 !important;
}
.hero {
    padding: 28px;
    border-radius: 8px;
    background: linear-gradient(135deg, #e8f5ed 0%, #eaf5fb 100%);
    border: 1px solid #cfe8d8;
}
.hero h1 {
    color: #000000 !important;
    margin-bottom: 8px;
}
.hero p, .texto-suave {
    color: var(--gris-suave) !important;
}
.metric-card {
    padding: 18px;
    border-radius: 8px;
    background: #ffffff;
    border: 1px solid #dbeafe;
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
}
.metric-label {
    color: #000000 !important;
    font-size: 0.9rem;
    font-weight: 700;
}
.metric-value {
    color: #000000 !important;
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
    color: #000000 !important;
    font-weight: 700;
}
.pending {
    color: #475569 !important;
}
.rule-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.92rem;
}
.rule-table th {
    background: #e8f5ed;
    color: #000000 !important;
    text-align: left;
    padding: 8px;
    border: 1px solid #cbd5e1;
}
.rule-table td {
    padding: 8px;
    border: 1px solid #e2e8f0;
    vertical-align: top;
}
.rule-table tr.rule-max {
    background: #dbeafe;
    font-weight: 700;
}
button.primary {
    background: #1f7a4d !important;
    color: #000000 !important;
    border-color: #166534 !important;
}
button.primary span,
.gradio-container button.primary span {
    color: #000000 !important;
}
.gradio-container button:not(.primary) {
    color: #000000 !important;
}
@media (max-width: 760px) {
    .hero {
        padding: 18px;
    }
    .metric-value {
        font-size: 1.35rem;
    }
}
"""


def formatear_tarjeta(etiqueta: str, valor: str, unidad: str) -> str:
    """Crea una tarjeta HTML compacta para resultados."""
    return (
        "<div class='metric-card'>"
        f"<div class='metric-label'>{etiqueta}</div>"
        f"<div class='metric-value'>{valor}</div>"
        f"<div class='texto-suave'>{unidad}</div>"
        "</div>"
    )


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


def generar_procedimiento(
    resultado: dict[str, Any] | None,
    humedad_suelo: float,
    temperatura: float,
    humedad_ambiental: float,
    velocidad_viento: float,
    tipo_cultivo: str,
) -> str:
    """Genera el procedimiento Mamdani paso a paso."""
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

    reglas_activadas = resultado["reglas_activadas"]
    reglas_md = "\n".join(
        f"- `{regla['id']}` alpha=`{regla['grado_activacion']:.4f}`: {regla['texto']}"
        for regla in reglas_activadas[:12]
    )
    if len(reglas_activadas) > 12:
        reglas_md += f"\n- ... {len(reglas_activadas) - 12} reglas activadas adicionales."

    pasos = resultado["pasos_matematicos"]
    return f"""
## Procedimiento Mamdani paso a paso

### 1. Valores ingresados
- Humedad del suelo: `{humedad_suelo:.2f} %`
- Temperatura ambiental: `{temperatura:.2f} C`
- Humedad ambiental: `{humedad_ambiental:.2f} %`
- Velocidad del viento: `{velocidad_viento:.2f} km/h`
- Tipo de cultivo: `{tipo_cultivo}`

### 2. Grados de pertenencia
{formatear_diccionario_grados(resultado["grados_pertenencia"])}

### 3. Reglas activadas y calculo de MIN
{pasos["activacion"]}

{reglas_md}

### 4. Agregacion por MAX
{pasos["implicacion"]}

{pasos["agregacion"]}

### 5. Formula del centroide
{pasos["desfuzzificacion"]}

### 6. Calculo final de salidas
- Tiempo de riego: `{resultado["tiempo_riego"]:.4f} minutos`
- Frecuencia de riego: `{resultado["frecuencia_riego"]:.4f} dias`
- Caudal de agua: `{resultado["caudal_agua"]:.4f} L/min`

### 7. Explicacion entendible
{resultado["interpretacion"]}
"""


def tabla_funciones_pertenencia() -> pd.DataFrame:
    """Devuelve tabla de parametros de membresia."""
    return pd.DataFrame(membership.obtener_tabla_parametros())


def tabla_reglas() -> pd.DataFrame:
    """Devuelve tabla de reglas difusas."""
    return pd.DataFrame(rules.obtener_tabla_reglas())


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
            gr.Markdown(
                """
### Modulos del sistema
- Motor difuso Mamdani implementado en CPU.
- Funciones de pertenencia triangulares y trapezoidales.
- Base de reglas representativa y explicable.
- Visualizacion de reglas, superficies y procedimiento matematico.
"""
            )

        with gr.Tab("Evaluar riego"):
            gr.Markdown("### Ingrese las condiciones actuales del cultivo")
            with gr.Row():
                with gr.Column(scale=1):
                    humedad_suelo = gr.Slider(0, 100, value=35, step=1, label="Humedad del suelo (%)")
                    temperatura = gr.Slider(0, 45, value=28, step=0.5, label="Temperatura ambiental (C)")
                    humedad_ambiental = gr.Slider(0, 100, value=55, step=1, label="Humedad ambiental (%)")
                    velocidad_viento = gr.Slider(0, 40, value=12, step=0.5, label="Velocidad del viento (km/h)")
                    tipo_cultivo = gr.Dropdown(CULTIVOS, value="Tomate", label="Tipo de cultivo")
                    boton_calcular = gr.Button("Calcular riego inteligente", variant="primary")
                    boton_procedimiento = gr.Button("Ver procedimiento Mamdani paso a paso")
                    boton_reporte_pdf = gr.Button("Descargar reporte PDF")
                with gr.Column(scale=1):
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
            procedimiento_desde_evaluacion = gr.Markdown()

        with gr.Tab("Procedimiento Mamdani"):
            gr.Markdown("### Trazabilidad matematica del ultimo calculo")
            procedimiento_general = gr.Markdown("Ejecute primero una evaluacion de riego.")

        with gr.Tab("Funciones de pertenencia"):
            gr.Markdown("### Parametros y visualizacion de funciones de pertenencia")
            with gr.Row():
                selector_variable = gr.Dropdown(
                    choices=list(membership.VARIABLES_DIFUSAS.keys()),
                    value="humedad_suelo",
                    label="Variable difusa",
                )
                selector_salida_agregada = gr.Dropdown(
                    choices=list(SALIDAS.keys()),
                    value="Tiempo de riego",
                    label="Salida agregada",
                )
            boton_actualizar_graficas = gr.Button("Actualizar graficas con valores ingresados", variant="primary")
            with gr.Row():
                grafico_membresia = gr.Plot(label="Funciones de pertenencia")
                grafico_salida_agregada = gr.Plot(label="Salida agregada")
            gr.Dataframe(value=tabla_funciones_pertenencia, interactive=False, wrap=True)

        with gr.Tab("Base de reglas"):
            gr.Markdown("### Base de reglas Mamdani")
            gr.Dataframe(value=tabla_reglas, interactive=False, wrap=True)

        with gr.Tab("Rule Viewer"):
            gr.Markdown("### Rule Viewer educativo tipo Mamdani")
            gr.Markdown(
                "El visor usa el ultimo resultado real calculado por `fuzzy_engine.py`: "
                "fuzzificacion, reglas activadas, recortes Mamdani, agregacion y centroide."
            )
            boton_actualizar_rule_viewer = gr.Button("Actualizar Rule Viewer", variant="primary")
            with gr.Row():
                rule_viewer_entradas = gr.Markdown("Ejecute una evaluacion para ver las entradas.")
                rule_viewer_resumen = gr.Markdown("Ejecute una evaluacion para ver el resumen.")
            with gr.Row():
                rule_viewer_grados = gr.Markdown("Ejecute una evaluacion para ver los grados de pertenencia.")
                rule_viewer_grafico = gr.Plot(label="Rule Viewer Mamdani")
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
            )
            rule_viewer_tabla_html = gr.HTML()
            gr.Markdown("### Visor individual de reglas")
            selector_regla = gr.Dropdown(choices=opciones_reglas(), label="Regla")
            detalle_regla = gr.Markdown("Seleccione una regla para ver sus antecedentes y consecuentes.")

        with gr.Tab("Surface Viewer"):
            gr.Markdown("### Surface Viewer 3D")
            gr.Markdown(
                "Cada punto de la malla se calcula con `fuzzy_engine.py`; no se usan "
                "formulas simplificadas ni valores inventados."
            )
            with gr.Row():
                superficie_surface = gr.Dropdown(
                    list(SUPERFICIES_3D.keys()),
                    value="Humedad del suelo vs temperatura ambiental -> tiempo de riego",
                    label="Superficie",
                )
                cultivo_surface = gr.Dropdown(CULTIVOS, value="Tomate", label="Cultivo")
            with gr.Row():
                humedad_suelo_surface = gr.Slider(0, 100, value=35, step=1, label="Humedad del suelo fija (%)")
                temperatura_surface = gr.Slider(0, 45, value=28, step=0.5, label="Temperatura fija (C)")
            with gr.Row():
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
            grafico_surface = gr.Plot()
            archivo_surface = gr.File(label="Descargar imagen PNG")
            resumen_surface = gr.Textbox(label="Resumen del calculo", interactive=False, lines=3)

        with gr.Tab("Historial"):
            gr.Markdown("### Historial de evaluaciones")
            with gr.Row():
                boton_guardar_historial = gr.Button("Guardar evaluacion", variant="primary")
                boton_descargar_historial = gr.Button("Descargar historial CSV")
                boton_limpiar_historial = gr.Button("Limpiar historial")
            mensaje_historial = gr.Textbox(label="Estado del historial", interactive=False)
            tabla_historial = gr.Dataframe(value=cargar_tabla_historial, interactive=False, wrap=True)
            archivo_historial = gr.File(label="Archivo CSV")
            gr.Markdown(
                "En servicios web como Render el almacenamiento puede reiniciarse segun el plan. "
                "Descargue el historial CSV si desea conservarlo."
            )

        with gr.Tab("Acerca del proyecto"):
            gr.Markdown(
                """
## Diseño de un Sistema Inteligente para el Riego Automático mediante Lógica Difusa Mamdani

### Datos académicos
**Universidad:** Universidad César Vallejo  
**Escuela:** Ingeniería de Sistemas  
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
**Meta 6.4:** uso eficiente de los recursos hídricos

### Líneas académicas
**Línea de investigación:** Sistemas de Información y Comunicación  
**Línea de responsabilidad social universitaria:** Desarrollo sostenible y adaptación al cambio climático

### Explicación breve del sistema
El sistema evalúa condiciones agrícolas como humedad del suelo, temperatura ambiental, humedad ambiental, velocidad del viento y tipo de cultivo. Con estas entradas calcula recomendaciones de tiempo de riego, frecuencia de riego y caudal de agua, buscando apoyar un uso más eficiente del recurso hídrico.

### Método Mamdani
El método Mamdani transforma valores numéricos en grados de pertenencia difusos, evalúa reglas lingüísticas del tipo SI...ENTONCES, recorta los consecuentes según el grado de activación, agrega las salidas con el operador máximo y obtiene valores finales mediante desfuzzificación por centroide.

### Tecnologías utilizadas
Python, Gradio, NumPy, Pandas, Matplotlib, ReportLab y lógica difusa implementada en CPU.
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
        ]
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
            fn=generar_procedimiento,
            inputs=[resultado_estado, *entradas],
            outputs=procedimiento_desde_evaluacion,
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
    demo.launch(server_name="0.0.0.0", server_port=port, css=CSS, theme=gr.themes.Soft())
