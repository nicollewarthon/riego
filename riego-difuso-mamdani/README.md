# Sistema Inteligente para el Riego Automatico mediante Logica Difusa Mamdani

Proyecto academico en Python preparado para construir un sistema de riego automatico basado en logica difusa Mamdani.

## Estado actual

El proyecto incluye motor difuso Mamdani, funciones de pertenencia, base de reglas, interfaz Gradio, Rule Viewer, Surface Viewer 3D e historial CSV de evaluaciones.

## Tecnologias

- Python 3.11 o superior
- Gradio
- NumPy
- Pandas
- Matplotlib
- scikit-fuzzy
- ReportLab
- Hugging Face Spaces

## Ejecucion local

```bash
pip install -r requirements.txt
python app.py
```

## Preparacion para Hugging Face Spaces

Hugging Face Spaces detecta `app.py` como punto de entrada para aplicaciones Gradio. El proyecto no requiere GPU y esta orientado a ejecucion en CPU basica.

## Historial de evaluaciones

Cada evaluacion puede guardarse en `data/historial.csv` desde la pestaña Historial. El archivo registra fecha y hora, entradas, salidas calculadas y reglas principales activadas.

En Hugging Face Spaces el almacenamiento local puede reiniciarse o perderse cuando el Space se reconstruye o reinicia. Para conservar los datos, descargue el historial con el boton **Descargar historial CSV**.

## Estructura

```text
riego-difuso-mamdani/
├── app.py
├── fuzzy_engine.py
├── membership.py
├── rules.py
├── charts.py
├── report.py
├── history.py
├── requirements.txt
├── README.md
├── assets/
│   └── logo.png
└── data/
    └── historial.csv
```
