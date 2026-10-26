# Buscador Semántico con PostgreSQL + pgvector

Buscador semántico interactivo desarrollado en Python que permite almacenar documentos en una base de datos PostgreSQL y recuperar los textos más relevantes mediante similitud vectorial.

El proyecto utiliza **Neon** como servicio de PostgreSQL en la nube, **pgvector** para almacenar y comparar vectores y **Sentence Transformers** para generar embeddings de texto.

## Objetivo

Implementar un sistema básico de recuperación semántica que permita:

- Conectarse a una base de datos PostgreSQL alojada en Neon.
- Activar la extensión pgvector y crear una tabla de documentos.
- Convertir textos en embeddings de 384 dimensiones.
- Almacenar documentos y sus vectores de forma persistente.
- Recuperar los dos documentos más similares a una consulta.
- Realizar múltiples búsquedas desde una terminal interactiva.

## Tecnologías utilizadas

| Tecnología | Función |
|---|---|
| Python | Lenguaje principal |
| PostgreSQL | Almacenamiento de documentos |
| Neon | Alojamiento de PostgreSQL en la nube |
| pgvector | Almacenamiento y búsqueda vectorial |
| Sentence Transformers | Generación de embeddings |
| psycopg | Conexión entre Python y PostgreSQL |
| python-dotenv | Gestión de variables de entorno |

**Modelo de embeddings:** `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`

Este modelo multilingüe transforma los textos en vectores de 384 dimensiones, permitiendo comparar su similitud semántica.

## Arquitectura del sistema

El proyecto se divide en dos procesos principales:

**1. Almacenamiento de documentos**

```text
Documentos de ejemplo
        |
        v
Sentence Transformers
        |
        v
Embeddings (384 dimensiones)
        |
        v
PostgreSQL + pgvector
        |
        v
Base de datos Neon
```

Los documentos se insertan inicialmente cuando la tabla está vacía. En ejecuciones posteriores se reutilizan los datos almacenados.

**2. Búsqueda semántica**

```text
Pregunta del usuario
        |
        v
Sentence Transformers
        |
        v
Embedding de la pregunta
        |
        v
Consulta SQL con pgvector
        |
        v
Comparación por distancia coseno
        |
        v
2 documentos más similares
```

## Estructura del proyecto

```text
P9-PostgreSQL-pgvector/
|
|-- main.py
|-- requirements.txt
|-- .env
|-- .gitignore
|-- README.md
```

El archivo `.env` contiene las credenciales de conexión y no debe subirse al repositorio.

## Instalación

### 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd P9-PostgreSQL-pgvector
```

Sustituye `<URL_DEL_REPOSITORIO>` por la URL real del proyecto.

### 2. Crear un entorno virtual

```bash
python -m venv .venv
```

Activarlo en Windows (PowerShell):

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar Neon

1. Crear un proyecto PostgreSQL en [Neon](https://neon.com).
2. Obtener la cadena de conexión desde el panel del proyecto.
3. Crear un archivo `.env` en la raíz del repositorio.
4. Añadir la siguiente variable:

```env
DATABASE_URL=postgresql://USUARIO:CONTRASENA@HOST/BASE_DE_DATOS?sslmode=require
```

Los valores deben sustituirse por las credenciales reales proporcionadas por Neon.

### 5. Ejecutar el proyecto

```bash
python main.py
```

En la primera ejecución, el programa prepara la extensión pgvector, crea la tabla y almacena los cinco documentos de ejemplo.

En las siguientes ejecuciones, los documentos existentes se conservan y no se vuelven a insertar.

## Funcionamiento

Una vez iniciado, el programa muestra un buscador interactivo que permite escribir preguntas libremente.

Ejemplo de consulta:

```text
===== BUSCADOR SEMÁNTICO =====
Escribe una pregunta para buscar documentos.
Escribe 'salir' para finalizar.

Tu pregunta: ¿Qué jugador consiguió marcar varios goles?

RESULTADOS DE LA BÚSQUEDA SEMÁNTICA:
1. El delantero marcó tres goles durante el partido.
   Similitud: 63.99%

2. El Real Madrid consiguió una victoria en el último minuto.
   Similitud: 31.75%
```

Los resultados corresponden a una ejecución de prueba y pueden variar si se modifica el modelo o el contenido almacenado.

Para finalizar el programa, escribir `salir`.

## Búsqueda vectorial

La recuperación de documentos se realiza mediante una consulta SQL que utiliza el operador `<=>` de pgvector para calcular la distancia coseno.

```sql
SELECT texto, 1 - (embedding <=> %s) AS similitud
FROM documentos
ORDER BY embedding <=> %s
LIMIT %s;
```

La consulta ordena los documentos por cercanía vectorial y devuelve los dos primeros por defecto.

La similitud coseno se obtiene restando la distancia coseno a 1. Esta puntuación mide la cercanía entre representaciones vectoriales, pero no debe interpretarse como una probabilidad de que la respuesta sea correcta.

## Resultados y conclusiones

Las pruebas realizadas muestran que el sistema puede identificar documentos relacionados con la temática de las preguntas, incluso cuando estas no coinciden literalmente con el texto almacenado.

También se observaron limitaciones en el orden de relevancia de algunas consultas, lo que demuestra que la calidad de la búsqueda depende del modelo de embeddings utilizado.

El proyecto permite comprender los fundamentos del almacenamiento vectorial y de la recuperación semántica, dos componentes habituales en arquitecturas RAG (*Retrieval-Augmented Generation*).

## Posibles mejoras

- Permitir añadir nuevos documentos sin depender de que la tabla esté vacía.
- Incorporar un umbral mínimo de similitud.
- Evaluar otros modelos de embeddings.
- Crear índices vectoriales para colecciones de mayor tamaño.
- Integrar la búsqueda en una API o en un asistente basado en RAG.

---

Proyecto desarrollado como práctica de formación en AI Engineering.