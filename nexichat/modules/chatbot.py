import random
from Abg.chat_status import adminsOnly
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.enums import ChatAction
from pyrogram.types import InlineKeyboardMarkup, Message

from config import MONGO_URL
from nexichat import nexichat
from nexichat.modules.helpers import CHATBOT_ON, is_admins

# MongoDB bağlantısını ayarlama
chatdb = MongoClient(MONGO_URL)
chatai = chatdb["Word"]["WordDb"]
daxxdb = chatdb["DAXXDb"]["DAXX"]

# Yanıt göndermek için işlev
async def send_reply(client, chat_id, response):
    await client.send_chat_action(chat_id, ChatAction.TYPING)
    if response["check"] == "sticker":
        await client.send_sticker(chat_id, response["text"])
    else:
        await client.send_message(chat_id, response["text"])

# Chatbot'u etkinleştirme/devre dışı bırakma komutu
@nexichat.on_cmd("chatbot", group_only=True)
@adminsOnly("can_delete_messages")
async def chaton_(_, m: Message):
    await m.reply_text(
        f"ᴄʜᴀᴛ: {m.chat.title}\n**ᴄʜᴏᴏsᴇ ᴀɴ ᴏᴩᴛɪᴏɴ ᴛᴏ ᴇɴᴀʙʟᴇ/ᴅɪsᴀʙʟᴇ ᴄʜᴀᴛʙᴏᴛ.**",
        reply_markup=InlineKeyboardMarkup(CHATBOT_ON),
    )

# Metin ve çıkartmalar için ortak mesaj işleyici
async def handle_message(client, message, is_sticker):
    if message.text and message.text.startswith(("!", "/", "?", "@", "#")):
        return
    
    is_daxx = daxxdb.find_one({"chat_id": message.chat.id})
    if is_daxx:
        return

    response = None
    if is_sticker:
        responses = list(chatai.find({"word": message.sticker.file_unique_id}))
    else:
        responses = list(chatai.find({"word": message.text}))
    
    if responses:
        response = random.choice(responses)
    
    if response:
        await send_reply(client, message.chat.id, response)

# Metin ve çıkartma mesajları için işleyiciler
@nexichat.on_message(
    (filters.text | filters.sticker | filters.group) & ~filters.private & ~filters.bot, group=4
)
async def chatbot_text(client: Client, message: Message):
    await handle_message(client, message, is_sticker=False)

@nexichat.on_message(
    (filters.sticker | filters.group) & ~filters.private & ~filters.bot, group=4
)
async def chatbot_sticker(client: Client, message: Message):
    await handle_message(client, message, is_sticker=True)
