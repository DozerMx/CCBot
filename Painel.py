import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

ADMIN_BOT_TOKEN = "8145135614:AAETwvnnBkfU8Xe0MICN8GxNvlQH60DZZxc"

def init_db():
    conn = sqlite3.connect("authorized_users.db")
    cursor = conn.cursor()
    cursor.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY)")
    conn.commit()
    conn.close()

async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        user_id = int(context.args[0])
        conn = sqlite3.connect("authorized_users.db")
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"✅ Usuario {user_id} autorizado.")
    else:
        await update.message.reply_text("⚠️ Uso: /add <user_id>")

async def del_user(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if context.args:
        user_id = int(context.args[0])
        conn = sqlite3.connect("authorized_users.db")
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
        conn.commit()
        conn.close()
        await update.message.reply_text(f"❌ Usuario {user_id} eliminado.")
    else:
        await update.message.reply_text("⚠️ Uso: /del <user_id>")

async def list_users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    conn = sqlite3.connect("authorized_users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = cursor.fetchall()
    conn.close()
    if users:
        users_list = "\n".join(str(user[0]) for user in users)
        await update.message.reply_text(f"👥 Usuarios autorizados:\n{users_list}")
    else:
        await update.message.reply_text("⚠️ No hay usuarios autorizados.")

def main() -> None:
    init_db()
    application = Application.builder().token(ADMIN_BOT_TOKEN).build()
    application.add_handler(CommandHandler("add", add_user))
    application.add_handler(CommandHandler("del", del_user))
    application.add_handler(CommandHandler("list", list_users))
    application.run_polling()

if __name__ == '__main__':
    main()