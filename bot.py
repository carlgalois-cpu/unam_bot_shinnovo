import os
import json
import random
import logging
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import database as db

# Cargar token desde .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Configurar logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Cargar preguntas desde archivos JSON
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
                preguntas_por_materia[materia] = json.load(f)
        except FileNotFoundError:
            logger.warning(f"Archivo {materia}.json no encontrado. Se creará vacío.")
            preguntas_por_materia[materia] = []
    return preguntas_por_materia

preguntas = cargar_preguntas()

# Diccionario temporal para almacenar la pregunta actual de cada usuario
user_current_question = {}

# Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.get_user(user.id, user.username)
    await update.message.reply_text(
        f"¡Hola {user.first_name}! Soy tu bot de estudio para la UNAM.\n"
        "Usa /menu para ver las materias disponibles.\n"
        "Usa /nivel para ver tu progreso."
    )

# Comando /menu
async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Español", callback_data="materia_espanol")],
        [InlineKeyboardButton("Matemáticas", callback_data="materia_matematicas")],
        [InlineKeyboardButton("Física", callback_data="materia_fisica")],
        [InlineKeyboardButton("Química", callback_data="materia_quimica")],
        [InlineKeyboardButton("Literatura", callback_data="materia_literatura")],
        [InlineKeyboardButton("Geografía", callback_data="materia_geografia")],
        [InlineKeyboardButton("Historia de México", callback_data="materia_historia_mexico")],
        [InlineKeyboardButton("Historia Universal", callback_data="materia_historia_universal")],
        [InlineKeyboardButton("Química Orgánica", callback_data="materia_quimica_organica")],
        [InlineKeyboardButton("Cálculo", callback_data="materia_calculo")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Elige una materia:", reply_markup=reply_markup)

# Manejar selección de materia
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    user_id = update.effective_user.id

    if data.startswith("materia_"):
        materia = data.replace("materia_", "")
        # Obtener preguntas de esa materia
        preguntas_materia = preguntas.get(materia, [])
        if not preguntas_materia:
            await query.edit_message_text("No hay preguntas disponibles para esta materia aún.")
            return
        # Elegir una pregunta aleatoria (nivel 1 por ahora)
        preguntas_nivel = [p for p in preguntas_materia if p.get("nivel", 1) == 1]
        if not preguntas_nivel:
            preguntas_nivel = preguntas_materia
        pregunta = random.choice(preguntas_nivel)
        # Guardar la pregunta actual para este usuario
        user_current_question[user_id] = (materia, pregunta)
        # Crear botones para las opciones
        opciones = pregunta["opciones"]
        keyboard = []
        for i, opcion in enumerate(opciones):
            keyboard.append([InlineKeyboardButton(opcion, callback_data=f"resp_{i}")])
        # Añadir botón de mnemotecnia
        keyboard.append([InlineKeyboardButton("🔍 Ver mnemotecnia", callback_data="mnemotecnia")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"*{pregunta['pregunta']}*",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    elif data.startswith("resp_"):
        # El usuario respondió una opción
        indice_respuesta = int(data.split("_")[1])
        materia, pregunta = user_current_question.get(user_id, (None, None))
        if not pregunta:
            await query.edit_message_text("Ya no hay pregunta activa. Usa /menu para empezar.")
            return
        correcta = pregunta["respuesta"]
        es_correcta = (indice_respuesta == correcta)
        # Actualizar estadísticas en BD
        db.update_user_stats(user_id, es_correcta, 1)
        # Responder
        if es_correcta:
            mensaje = "✅ ¡Correcto!"
        else:
            opcion_correcta = pregunta["opciones"][correcta]
            mensaje = f"❌ Incorrecto. La respuesta correcta es: {opcion_correcta}"
        # Ofrecer siguiente pregunta
        keyboard = [[InlineKeyboardButton("Siguiente pregunta", callback_data=f"materia_{materia}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            mensaje + "\n\n¿Quieres otra pregunta?",
            reply_markup=reply_markup
        )
        # Limpiar pregunta actual
        del user_current_question[user_id]
    elif data == "mnemotecnia":
        # Mostrar la mnemotecnia de la pregunta actual
        materia, pregunta = user_current_question.get(user_id, (None, None))
        if not pregunta:
            await query.edit_message_text("No hay pregunta activa.")
            return
        mne = pregunta.get("mnemotecnia", "No hay mnemotecnia disponible.")
        # Crear botón para volver a la pregunta
        keyboard = [[InlineKeyboardButton("Volver a la pregunta", callback_data=f"materia_{materia}")]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(
            f"🧠 *Mnemotecnia:* {mne}",
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

# Comando /nivel para ver progreso
async def nivel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    datos = db.get_user(user.id)
    if datos:
        _, username, nivel, puntos, correctas, totales = datos
        porcentaje = (correctas / totales * 100) if totales > 0 else 0
        await update.message.reply_text(
            f"📊 *Tu progreso:*\n"
            f"Nivel actual: {nivel}\n"
            f"Puntos: {puntos}\n"
            f"Respuestas correctas: {correctas}/{totales} ({porcentaje:.1f}%)",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text("Aún no tienes estadísticas. ¡Empieza a estudiar con /menu!")

# Comando /help
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Comandos disponibles:\n"
        "/start - Iniciar\n"
        "/menu - Elegir materia\n"
        "/nivel - Ver tu progreso\n"
        "/help - Esta ayuda"
    )

def main():
    # Crear la aplicación
    application = Application.builder().token(BOT_TOKEN).build()

    # Añadir manejadores
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("menu", menu))
    application.add_handler(CommandHandler("nivel", nivel))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Iniciar el bot
    logger.info("Bot iniciado...")
    application.run_polling()

if __name__ == "__main__":
    main()
