# Generación de Estímulos Dinámicos de Dolor mediante IA Generativa

Este repositorio contiene el código y la documentación para el proyecto de generación de estímulos de video para estudios de emociones (específicamente dolor vs. control). El objetivo es crear un set de videos estandarizados siguiendo lineamientos científicos (basados en *Behnke et al., 2025*), utilizando IA Generativa.

## Descripción del Proyecto

El proyecto busca superar las limitaciones de los sets de estímulos tradicionales mediante la generación sintética de videos que permitan un control preciso sobre las variables experimentales. Se generan pares de videos (Dolor vs. Control) donde la única variación es la interacción dolorosa, manteniendo idénticos el fondo, la iluminación, la identidad del sujeto y otros factores contextuales.

## Metodología

El proceso de generación se divide en tres fases principales:

### Fase 1: Extracción de "Ground Truth" (Source Analysis)
Para asegurar la validez ecológica y evitar problemas de derechos de autor, no se parte de prompts libres sino de descripciones semánticas extraídas de bases de datos de imágenes validadas.

*   **Entrada:** Pares de imágenes originales (Pain / No-Pain).
*   **Herramienta:** VLM (Visual Language Model) - **Gemini 3**.
*   **Proceso:** Se procesan las imágenes con un System Prompt diseñado para visión por computadora, obteniendo descripciones densas que aíslan la acción física, anatomía y objetos, eliminando la identidad del sujeto original.
*   **Lógica:** La descripción de la condición de Dolor (`t_end_P`) actúa como "Maestra". Las descripciones de Control (`t_end_C`) e Inicio (`t_start`) se derivan como variaciones sustractivas.

### Fase 2: Síntesis de Activos Visuales (Asset Batch Generation)
Generación de los fotogramas clave (*keyframes*) asegurando consistencia *pixel-perfect* en las áreas no manipuladas (fondo, ropa).

*   **Herramientas:** **FLUX.1 [dev]** + **Inpainting API** (vía Fal.ai).
*   **Protocolo de Generación Inversa:**
    1.  **Master Anchor (`t_end_P`)**: Se genera primero la imagen de dolor. Esta fija el fondo y la identidad.
    2.  **Segmentación (ROI)**: Se crea una máscara sobre el objeto causante y la zona anatómica afectada (vía SAM o manual).
    3.  **Variantes (`t_start` y `t_end_C`)**: Se usa inpainting sobre el *Master Anchor* para generar el estado inicial (objeto preparado) y la condición de control (objeto en reposo sin causar dolor), manteniendo el resto de la imagen intacta.

### Fase 3: Interpolación Dinámica (Video Synthesis)
Conversión de los keyframes estáticos en videos fluidos de corta duración (aprox. 5 segundos).

*   **Herramienta:** **Kling v1.6 Pro**.
*   **Técnica:** Image-to-Video con interpolación de keyframes.
*   **Salida:**
    *   **Video Dolor:** Transición de `t_start` &rarr; `t_end_P` ("Sudden, visceral impact").
    *   **Video Control:** Transición de `t_start` &rarr; `t_end_C` ("Slow, controlled movement").

## Estructura del Repositorio

*   `scripts/`: Scripts de Python para la ejecución de las distintas etapas del pipeline.
    *   `generate_ref_img.py`: Generación de imágenes de referencia (Master Anchors).
    *   `generate_pov_img.py`: Generación de variantes en primera persona (Point of View).
    *   `generate_poc.py`: Pruebas de concepto (Proof of Concept).
*   `src/`: Código fuente del paquete `pain_stimuli`.
*   `img/`: Directorio de almacenamiento para las imágenes generadas.
*   `ai_prompts.xlsx`: Archivo de control conteniendo los prompts estructurados para cada fase.

## Instalación

El proyecto utiliza un entorno de Python gestionado. Se recomienda utilizar Conda/Mamba.

1.  **Clonar el repositorio:**
    ```bash
    git clone <URL_DEL_REPO>
    cd affective_ai_videos
    ```

2.  **Crear el entorno:**
    ```bash
    conda env create -f environment.yml
    conda activate gen-ai
    ```

3.  **Instalar en modo editable:**
    ```bash
    pip install -e .
    ```

Requisitos principales:
*   Python 3.11
*   `fal-client` (para la API de Fal.ai)
*   `numpy`, `pandas`, `openpyxl`

## Estado del Proyecto

*   [x] Definición de estándares (adaptación de *Behnke et al., 2025* para video).
*   [x] **Fase 1** completada para un subset inicial de estímulos de dolor.
*   [ ] Completar Fase 2 y 3 para todo el set (~96 videos).
*   [ ] Validación experimental de los estímulos generados.

## Notas Técnicas

*   Se ha optimizado la duración de los videos a **5-10 segundos** para viabilidad técnica y experimental.
*   El enfoque de "Anchored Inpainting" es crítico para asegurar que los controles sean verdaderos controles experimentales, variando solo el estímulo afectivo.

---
*Este proyecto es parte de una investigación en curso sobre procesamiento afectivo y dolor.*
