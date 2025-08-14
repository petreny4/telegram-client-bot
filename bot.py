import re
import sqlite3
import logging
import os
from telegram import Update
from telegram.ext import Updater, MessageHandler, Filters, CallbackContext

# Логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

# Файл базы данных
DB_FILE = "clients.db"

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS clients (
            username TEXT PRIMARY KEY
        )
    """)
    conn.commit()
    conn.close()

# Проверка клиента в базе
def is_client_in_db(username: str) -> bool:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM clients WHERE username = ?", (username,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists

# Добавление новых клиентов
def add_clients_to_db(usernames: list):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    for username in usernames:
        try:
            cursor.execute("INSERT INTO clients (username) VALUES (?)", (username,))
        except sqlite3.IntegrityError:
            pass
    conn.commit()
    conn.close()

# Извлечение никнеймов
def extract_usernames(text: str) -> list:
    return re.findall(r'@(\w+)', text)

# Обработка сообщений
def process_message(update: Update, context: CallbackContext):
    text = update.message.text
    raw_usernames = extract_usernames(text)
    if not raw_usernames:
        update.message.reply_text("❌ Не найдено ни одного юзернейма в формате @username")
        return

    duplicates = []
    unique_new = []
    seen_in_message = set()

    for username in raw_usernames:
        username_lower = username.lower()
        if username_lower in seen_in_message:
            if username_lower not in (d.lower() for d in duplicates):
                duplicates.append(f"@{username}")
            continue
        seen_in_message.add(username_lower)

        if is_client_in_db(username_lower):
            if username_lower not in (d.lower() for d in duplicates):
                duplicates.append(f"@{username}")
        else:
            unique_new.append(f"@{username}")

    if not duplicates:
        response = "✅ Всё чисто, можно писать!"
        add_clients_to_db([u[1:].lower() for u in unique_new])
    else:
        add_clients_to_db([u[1:].lower() for u in unique_new])
        response = "⚠️ Есть повторения:\n" + "\n".join(duplicates)
        if unique_new:
            response += "\n\n✅ Клиенты, которым можно писать:\n" + "\n".join(unique_new)
        else:
            response += "\n\n❌ Новых клиентов для добавления нет"

    update.message.reply_text(response)

def main():
    init_db()
    TOKEN = os.environ.get("BOT_TOKEN", "8068204248:AAE1_5BbBZtlrFVVTiyyM6aqlDqHzPedVAk")

    updater = Updater(TOKEN)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, process_message))

    logger.info("Бот запущен...")
    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
