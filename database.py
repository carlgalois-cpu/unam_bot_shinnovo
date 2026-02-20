import sqlite3
import os

DB_PATH = os.path.join('data', 'bot_database.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Tabla de usuarios
    c.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            nivel_actual INTEGER DEFAULT 1,
            puntos INTEGER DEFAULT 0,
            respuestas_correctas INTEGER DEFAULT 0,
            respuestas_totales INTEGER DEFAULT 0
        )
    ''')
    # Tabla de progreso por materia (opcional)
    c.execute('''
        CREATE TABLE IF NOT EXISTS progreso_materia (
            user_id INTEGER,
            materia TEXT,
            nivel INTEGER DEFAULT 1,
            PRIMARY KEY (user_id, materia)
        )
    ''')
    conn.commit()
    conn.close()

def get_user(user_id, username=None):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("SELECT * FROM usuarios WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    if not user and username:
        # Crear usuario nuevo
        c.execute("INSERT INTO usuarios (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
        c.execute("SELECT * FROM usuarios WHERE user_id = ?", (user_id,))
        user = c.fetchone()
    conn.close()
    return user

def update_user_stats(user_id, correct, total):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        UPDATE usuarios 
        SET respuestas_correctas = respuestas_correctas + ?,
            respuestas_totales = respuestas_totales + ?,
            puntos = puntos + ?
        WHERE user_id = ?
    ''', (1 if correct else 0, 1, 10 if correct else 0, user_id))
    conn.commit()
    conn.close()

# Inicializar la base de datos al importar
if not os.path.exists(DB_PATH):
    init_db()
