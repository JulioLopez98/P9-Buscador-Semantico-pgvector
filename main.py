
# ============================================================
# PROYECTO 9 - BUSCADOR SEMÁNTICO CON POSTGRESQL + PGVECTOR
# ============================================================
# Objetivo:
# Almacenar documentos como embeddings en Neon (PostgreSQL)
# y recuperar los más similares a una pregunta del usuario.
# ============================================================

# ============================================================
# 1. IMPORTACIONES Y CONFIGURACIÓN
# ============================================================

import os  # Acceso a las variables de entorno
import psycopg  # Conexión con PostgreSQL

from dotenv import load_dotenv  # Lectura del archivo .env
from sentence_transformers import SentenceTransformer  # Embeddings
from pgvector.psycopg import register_vector  # Soporte pgvector


# Cargamos las variables de entorno
load_dotenv()

# Recuperamos la URL de conexión a Neon
DATABASE_URL = os.getenv("DATABASE_URL")

# Verificamos que exista antes de continuar
if not DATABASE_URL:
    raise ValueError("No se encontró DATABASE_URL en el archivo .env")


# ============================================================
# 2. PREPARACIÓN DE POSTGRESQL Y PGVECTOR
# ============================================================

print("\n===== CONFIGURACIÓN DE LA BASE DE DATOS =====")

# Abrimos una conexión con PostgreSQL
with psycopg.connect(DATABASE_URL) as conexion:

    # Creamos un cursor para ejecutar consultas SQL
    with conexion.cursor() as cursor:

        # Consultamos la versión de PostgreSQL
        cursor.execute("SELECT version();")
        resultado = cursor.fetchone()

        if resultado is not None:
            print("Conexión a Neon establecida correctamente")
            print(f"PostgreSQL: {resultado[0]}")
        else:
            raise RuntimeError("No se pudo obtener la versión de PostgreSQL")

        # Activamos la extensión pgvector si no existe
        cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")

        # Consultamos la versión instalada de pgvector
        cursor.execute("""
            SELECT extversion
            FROM pg_extension
            WHERE extname = 'vector';
        """)

        resultado_vector = cursor.fetchone()

        if resultado_vector is not None:
            print(f"pgvector: versión {resultado_vector[0]}")
        else:
            raise RuntimeError("No se encontró la extensión pgvector")

        # Creamos la tabla que almacenará textos y vectores
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS documentos (
                id SERIAL PRIMARY KEY,
                texto TEXT NOT NULL,
                embedding VECTOR(384)
            );
        """)

        print("Tabla 'documentos' preparada correctamente")


# ============================================================
# 3. MODELO DE EMBEDDINGS Y DOCUMENTOS
# ============================================================

print("\n===== MODELO DE EMBEDDINGS =====")

# Cargamos un modelo multilingüe de 384 dimensiones
modelo = SentenceTransformer(
    "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

print("Modelo de embeddings cargado correctamente")


# Documentos de ejemplo para nuestra base de datos
frases = [
    "Mañana se esperan lluvias intensas en Valencia.",
    "Las temperaturas bajarán durante el fin de semana.",
    "El cielo estará despejado y hará mucho calor.",
    "El Real Madrid consiguió una victoria en el último minuto.",
    "El delantero marcó tres goles durante el partido."
]


# ============================================================
# 4. ALMACENAMIENTO Y RECUPERACIÓN DE DOCUMENTOS
# ============================================================

print("\n===== DOCUMENTOS EN NEON =====")

# Abrimos una conexión para consultar e insertar documentos
with psycopg.connect(DATABASE_URL) as conexion:

    # Registramos el tipo vector en esta conexión
    register_vector(conexion)

    with conexion.cursor() as cursor:

        # Contamos los documentos almacenados
        cursor.execute("SELECT COUNT(*) FROM documentos;")
        resultado = cursor.fetchone()

        # Comprobamos que la consulta haya funcionado
        if resultado is None:
            raise RuntimeError("No se pudo contar los documentos")

        total_documentos = resultado[0]

        # Solo insertamos documentos si la tabla está vacía
        if total_documentos == 0:

            print("Tabla vacía. Generando embeddings...")

            # Convertimos las frases en vectores de 384 dimensiones
            embeddings = modelo.encode(frases)

            print(f"Embeddings generados: {len(embeddings)}")
            print(f"Dimensiones por vector: {len(embeddings[0])}")

            # Asociamos cada frase con su embedding
            for frase, vector in zip(frases, embeddings):

                # Guardamos el texto y su vector en PostgreSQL
                cursor.execute("""
                    INSERT INTO documentos (texto, embedding)
                    VALUES (%s, %s);
                """, (frase, vector))

            print(f"{len(frases)} documentos insertados correctamente")

        else:
            # Evitamos generar e insertar documentos repetidos
            print(f"Documentos existentes: {total_documentos}")

        # Recuperamos los documentos para comprobar su contenido
        cursor.execute("""
            SELECT id, texto
            FROM documentos
            ORDER BY id;
        """)

        documentos = cursor.fetchall()

        # Mostramos los documentos almacenados
        print("\nDOCUMENTOS ALMACENADOS:")

        for id_documento, texto in documentos:
            print(f"{id_documento}. {texto}")


# ============================================================
# 5. FUNCIÓN DE BÚSQUEDA SEMÁNTICA
# ============================================================

def buscar_documentos(pregunta, limite=2):
    """
    Busca los documentos más similares a una pregunta.

    Parámetros:
        pregunta: texto introducido por el usuario.
        limite: número máximo de resultados (por defecto, 2).

    Devuelve:
        Lista de documentos y sus puntuaciones de similitud.
    """

    # Transformamos la pregunta en un embedding
    vector_pregunta = modelo.encode(pregunta)

    # Verificamos la URL para el análisis de tipos
    assert DATABASE_URL is not None

    # Abrimos una conexión para realizar la búsqueda
    with psycopg.connect(DATABASE_URL) as conexion:

        register_vector(conexion)

        with conexion.cursor() as cursor:

            # <=> calcula la distancia coseno entre dos vectores
            # 1 - distancia convierte el resultado en similitud
            # ORDER BY recupera los vectores más cercanos
            cursor.execute("""
                SELECT texto, 1 - (embedding <=> %s) AS similitud
                FROM documentos
                ORDER BY embedding <=> %s
                LIMIT %s;
            """, (vector_pregunta, vector_pregunta, limite))

            # Recuperamos los resultados de PostgreSQL
            resultados = cursor.fetchall()

    return resultados


# ============================================================
# 6. BUSCADOR SEMÁNTICO INTERACTIVO
# ============================================================

print("\n===== BUSCADOR SEMÁNTICO =====")
print("Escribe una pregunta para buscar documentos.")
print("Escribe 'salir' para finalizar.")


# Mantenemos el programa activo para múltiples consultas
while True:

    # Solicitamos una pregunta y eliminamos espacios sobrantes
    pregunta = input("\nTu pregunta: ").strip()

    # Permitimos finalizar el programa
    if pregunta.lower() == "salir":
        print("\n¡Hasta pronto!")
        break

    # Evitamos procesar preguntas vacías
    if not pregunta:
        print("Introduce una pregunta válida.")
        continue

    # Recuperamos los dos documentos más similares
    resultados = buscar_documentos(pregunta)

    print("\nRESULTADOS DE LA BÚSQUEDA SEMÁNTICA:")

    # Mostramos cada documento y su similitud coseno
    for posicion, (texto, similitud) in enumerate(resultados, start=1):
        print(f"{posicion}. {texto}")
        print(f"   Similitud: {similitud:.2%}")
