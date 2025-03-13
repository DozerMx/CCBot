import os
import sqlite3
import asyncio
from PIL import Image
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaDocument
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
import threading

TOKEN = "7865047964:AAEA-vBOOkMbH04NykR63e597whAxF512MQ"
IMAGE_FOLDER = "Cedulas"
MAX_FILE_SIZE = 1 * 1024 * 1024
LARGE_IMAGES = [3, 4]

def init_db():
    conn = sqlite3.connect("authorized_users.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

def is_user_authorized(user_id: int) -> bool:
    conn = sqlite3.connect("authorized_users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users WHERE user_id = ?", (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result is not None

def compress_image(image_path: str, output_path: str, image_number: int) -> None:
    with Image.open(image_path) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        if image_number in LARGE_IMAGES:
            width, height = img.size
            new_width = int(width * 0.6)
            new_height = int(height * 0.6)
            img = img.resize((new_width, new_height), Image.LANCZOS)
            img.save(output_path, 'JPEG', quality=30, optimize=True)
        else:
            img.save(output_path, 'JPEG', quality=85, optimize=True)

def compress_image_thread(image_path, output_path, image_number):
    compress_image(image_path, output_path, image_number)

async def send_image(update: Update, context: ContextTypes.DEFAULT_TYPE, image_number: int) -> None:
    image_path = os.path.join(IMAGE_FOLDER, f"{image_number}.png")
    if os.path.exists(image_path):
        compressed_path = os.path.join(IMAGE_FOLDER, f"compressed_{image_number}.jpg")
        
        threading.Thread(target=compress_image_thread, args=(image_path, compressed_path, image_number)).start()
        
        while not os.path.exists(compressed_path) or os.path.getsize(compressed_path) == 0:
            await asyncio.sleep(0.1)
        
        file_size = os.path.getsize(compressed_path)
        if file_size > MAX_FILE_SIZE:
            if image_number in LARGE_IMAGES:
                with Image.open(image_path) as img:
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    width, height = img.size
                    new_width = int(width * 0.4)
                    new_height = int(height * 0.4)
                    img = img.resize((new_width, new_height), Image.LANCZOS)
                    img.save(compressed_path, 'JPEG', quality=15, optimize=True)
                    
                    file_size = os.path.getsize(compressed_path)
                    if file_size > MAX_FILE_SIZE:
                        await update.callback_query.answer("La imagen sigue siendo demasiado grande") if hasattr(update, 'callback_query') else await update.message.reply_text("La imagen sigue siendo demasiado grande incluso con compresión extrema.")
                        os.remove(compressed_path)
                        return
            else:
                await update.callback_query.answer("La imagen es demasiado grande") if hasattr(update, 'callback_query') else await update.message.reply_text("La imagen es demasiado grande incluso después de la compresión.")
                os.remove(compressed_path)
                return

        keyboard = [
            [InlineKeyboardButton("⬅️ Anterior", callback_data=f'nav_prev_{image_number}'),
             InlineKeyboardButton("Siguiente ➡️", callback_data=f'nav_next_{image_number}')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        with open(compressed_path, 'rb') as file:
            if hasattr(update, 'message') and update.message:
                await update.message.reply_document(document=file, reply_markup=reply_markup, filename=f"Cedula_{image_number}.jpg")
            elif hasattr(update, 'callback_query'):
                await update.callback_query.message.reply_document(document=file, reply_markup=reply_markup, filename=f"Cedula_{image_number}.jpg")
        
        os.remove(compressed_path)
    else:
        if hasattr(update, 'message') and update.message:
            await update.message.reply_text(f"No se encontró la imagen {image_number}.")
        elif hasattr(update, 'callback_query'):
            await update.callback_query.answer(f"No se encontró la imagen {image_number}.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    if is_user_authorized(user_id):
        await send_image(update, context, 1)
    else:
        keyboard = [
            [InlineKeyboardButton("Aceptar", callback_data='accept')],
            [InlineKeyboardButton("Rechazar", callback_data='reject')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            "Bienvenido al bot privado desarrollado por NSN Null Signal Network y Bdc.\n\n"
            "Este es un bot totalmente privado. Sin acceso autorizado por uno de los administradores oficiales, no podrás acceder a él.\n\n"
            "Política de privacidad: Este bot es confidencial. Acepta para continuar.",
            reply_markup=reply_markup
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    if query.data == 'accept':
        if is_user_authorized(user_id):
            await send_image(update, context, 1)
        else:
            await query.edit_message_text("No estás autorizado. Contacta a un administrador.")
    elif query.data == 'reject':
        await query.edit_message_text("Has rechazado los términos. No puedes usar este bot.")
    elif query.data.startswith('nav_'):
        _, action, current = query.data.split('_')
        current = int(current)
        if action == 'next':
            current += 1
        elif action == 'prev':
            current -= 1
        if current < 1:
            current = 1
        await send_image(update, context, current)

def main() -> None:
    init_db()
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))
    application.run_polling()

if __name__ == '__main__':
    main()
