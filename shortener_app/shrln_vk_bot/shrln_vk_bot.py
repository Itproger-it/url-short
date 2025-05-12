import os

from dotenv import load_dotenv
import aiohttp
from vkbottle.bot import Bot, Message
from vkbottle import Keyboard, KeyboardButtonColor, Text, CtxStorage

load_dotenv()

URLS: dict[str, str] = {"short":os.getenv("SHORT_LINK"), "decode": os.getenv("DECODE_LINK")}
VK_TOKEN = os.getenv("VK_TOKEN")

bot = Bot(token=VK_TOKEN)
ctx_storage = CtxStorage()


def main_keyboard() -> Keyboard:
    keyboard = (
        Keyboard(one_time=False, inline=False)
        .add(Text("Сократить ссылку"), color=KeyboardButtonColor.PRIMARY)
        .add(Text("Декодировать ссылку"), color=KeyboardButtonColor.PRIMARY)
    )
    return keyboard


def cancel_keyboard() -> Keyboard:
    keyboard = Keyboard(one_time=False, inline=False).add(
        Text("Cancel"), color=KeyboardButtonColor.NEGATIVE
    )
    return keyboard


@bot.on.message(text="Начать")
async def start(message: Message):
    await message.answer(
        "Привет! Выберите действие:",
        keyboard=main_keyboard(),
    )


@bot.on.message(text="Сократить ссылку")
async def shorten_link(message: Message):
    ctx_storage.set(message.from_id, "short")
    await message.answer(
        "Отправьте мне ссылку, которую вы хотите сократить, или нажмите 'Cancel'.",
        keyboard=cancel_keyboard(),
    )


@bot.on.message(text="Декодировать ссылку")
async def decode_link(message: Message):
    ctx_storage.set(message.from_id, "decode")
    await message.answer(
        "Отправьте мне сокращенную ссылку, чтобы я её раскодировал, или нажмите 'Cancel'.",
        keyboard=cancel_keyboard(),
    )


@bot.on.message(text="Cancel")
async def cancel(message: Message):
    if ctx_storage.get(message.from_id):
        ctx_storage.delete(message.from_id)
    await message.answer(
        "Отмена операции. Выберите действие:", keyboard=main_keyboard()
    )


@bot.on.message() 
async def handle_url(message: Message):
    user_input = message.text
    flag = False

    if not ctx_storage.get(message.from_id):
        flag = True
        await message.answer("Выберите операцию", keyboard=main_keyboard())


    elif user_input.startswith("http://") or user_input.startswith("https://"):
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            try:
                api_url = URLS[ctx_storage.get(message.from_id)]
                payload = {"target_url": user_input}

                async with session.post(api_url, json=payload) as response:
                    if response.status >= 200:
                        data = await response.json()
                        short_url = data.get("url", "Не удалось сократить")
                        await message.answer(f"{ctx_storage.get(message.from_id)} link: {short_url}")
                    else:
                        await message.answer(f"unknow error")
                ctx_storage.delete(message.from_id)
            except Exception as e:
                await message.answer(f"Произошла ошибка, повторите попытку")
    else:
        await message.answer("Это не похоже на ссылку. Пожалуйста, отправьте правильный URL.")

    if not flag:
        await message.answer("Что хотите сделать дальше?", keyboard=main_keyboard())


if __name__ == "__main__":
    bot.run_forever()
