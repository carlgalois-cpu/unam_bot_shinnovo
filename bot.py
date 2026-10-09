def cargar_preguntas():
    preguntas_por_materia = {}
    materias = [
        "espanol", "matematicas", "fisica", "quimica", "literatura",
        "geografia", "historia_mexico", "historia_universal",
        "quimica_organica", "calculo"
    ]
    for materia in materias:
        try:
            with open(f"data/{materia}.json", "r", encoding="utf-8") as f:
                contenido = f.read().strip()
                if not contenido:
                    preguntas_por_materia[materia] = []
                else:
                    preguntas_por_materia[materia] = json.loads(contenido)
        except FileNotFoundError:
            logger.warning(f"Archivo {materia}.json no encontrado. Se usará lista vacía.")
            preguntas_por_materia[materia] = []
        except json.JSONDecodeError:
            logger.warning(f"Archivo {materia}.json tiene formato inválido. Se usará lista vacía.")
            preguntas_por_materia[materia] = []
    return preguntas_por_materia
