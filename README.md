# Sistema Inteligente para el Riego Automatico mediante Logica Difusa Mamdani

## Descripcion

Aplicacion web academica desarrollada en Python y Gradio para evaluar recomendaciones de riego automatico mediante un Sistema de Inferencia Difusa Mamdani. El sistema recibe condiciones del cultivo y del ambiente, calcula tiempo de riego, frecuencia y caudal, y muestra trazabilidad mediante funciones de pertenencia, Rule Viewer, Surface Viewer 3D, historial CSV y reportes PDF.

## Objetivo

Disenar un sistema inteligente que apoye el uso eficiente del agua en riego agricola, aplicando logica difusa Mamdani para transformar variables ambientales y agronomicas en recomendaciones interpretables.

## Tecnologias

- Python 3.11
- Gradio
- NumPy
- Pandas
- Matplotlib
- ReportLab
- Render

## Arquitectura

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
├── Procfile
├── runtime.txt
├── README.md
├── assets/
│   └── logo.png
└── data/
    └── historial.csv
```

## Capturas

> Espacio reservado para capturas de pantalla.

- Inicio: `docs/captura_inicio.png`
- Evaluacion de riego: `docs/captura_evaluacion.png`
- Rule Viewer: `docs/captura_rule_viewer.png`
- Surface Viewer: `docs/captura_surface_viewer.png`
- Reporte PDF: `docs/captura_reporte.png`

## Instalacion local

```bash
git clone <URL_DEL_REPOSITORIO>
cd riego-difuso-mamdani
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

En Linux/macOS:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecucion

```bash
python app.py
```

Abrir:

```text
http://127.0.0.1:7860
```

## Despliegue en Render

### 1. Subir el proyecto a GitHub

```bash
git init
git add .
git commit -m "Preparar sistema de riego difuso para Render"
git branch -M main
git remote add origin <URL_DEL_REPOSITORIO>
git push -u origin main
```

### 2. Conectar GitHub con Render

1. Ingresar a https://render.com.
2. Crear o iniciar sesion en una cuenta.
3. Ir a **Dashboard**.
4. Seleccionar **New +**.
5. Elegir **Web Service**.
6. Conectar la cuenta de GitHub si Render lo solicita.
7. Seleccionar el repositorio del proyecto.

### 3. Crear el Web Service

Configuracion recomendada:

- **Environment:** Python
- **Branch:** main
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:** `python app.py`
- **Instance Type:** Free o Starter, segun disponibilidad

El archivo `Procfile` tambien define:

```text
web: python app.py
```

La aplicacion detecta automaticamente el puerto asignado por Render mediante la variable de entorno `PORT`.

### 4. Actualizaciones automaticas

Render puede desplegar automaticamente cada vez que se haga push a la rama configurada:

```bash
git add .
git commit -m "Actualizar sistema"
git push
```

Si **Auto-Deploy** esta activado, Render reconstruira y publicara la nueva version.

## Historial

El historial se guarda en `data/historial.csv`. En servicios web como Render, el sistema de archivos puede ser efimero segun el plan y la configuracion. Para conservar los datos, descargar el CSV desde la pestana **Historial**.

## Reportes PDF

La aplicacion genera reportes PDF solo despues de realizar una evaluacion valida. Los archivos temporales se crean en `assets/reports/` y no deben versionarse en Git.

## ODS

- ODS 6: Agua limpia y saneamiento
- Meta 6.4: uso eficiente de los recursos hidricos

## Curso

Sistemas Inteligentes - Unidad 3

## Universidad

Universidad Cesar Vallejo  
Escuela de Ingenieria de Sistemas

## Profesor

Tito Chura, Virgilio Fredy

## Autores

- Barrientos Romero, Samira Pamela
- Espinoza Huerta, Brennys Stefano
- Ramirez Bardales, Rober Kener
- Warthon Arratea, Sharonn Nicolle

## Licencia

Proyecto academico con fines educativos. Se permite su uso, adaptacion y presentacion citando a los autores.
