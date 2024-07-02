import disnake  # https://ru.guide.disnake.dev/interactions/slash-commands
from disnake.ext import commands, tasks
import datetime
import asyncio
import random
import requests
import os
from googletrans import Translator
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

intents = disnake.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

command_sync_flags = commands.CommandSyncFlags.default()
command_sync_flags.sync_commands_debug = True

bot = commands.Bot(command_prefix='-', command_sync_flags=command_sync_flags, intents=intents)

items = [{'emoji': '⌚', 'name': '**Upwork** Pavlo', 'status': None, 'message_id': None},
         {'emoji': '⌚', 'name': '**Upwork** Artem', 'status': None, 'message_id': None},
         {'emoji': '⌚', 'name': '**Hubstuff** Pavlo', 'status': None, 'message_id': None},
         {'emoji': '⌚', 'name': '**Hubstuff** "SoundBox"', 'status': None, 'message_id': None},
         {'emoji': '⌚', 'name': '**Clockify**', 'status': None, 'message_id': None},
         {'emoji': '⌚', 'name': '**Hubstuff** Varvara', 'status': None, 'message_id': None}]

magic_ball_responses = ["Безсумнівно", "Вирішено", "Ніяких сумнівів", "Однозначно так", "Можеш бути впевнений у цьому",
                        "Мені здається — «так»", "Скоріш за все", "Хороші перспективи", "Знаки говорять — «так»", "Так",
                        "Зараз не можна передбачити", "Сконцентруйся і спитай знову", "Навіть не думай",
                        "Моя відповідь — «ні»", "За моїми даними — «ні»", "Перспективи не дуже хороші",
                        "Дуже сумнівно", "Можливо так, можливо ні", "Можливо у паралельному всесвіті", "👍", "👎"]

magic_ball_chumba = ['', ', Чумба']


@bot.slash_command(description="Запитай магічну кулю (питання має відповідати на так/ні)")
async def magicball(inter, question: str):
    response = random.choice(magic_ball_responses)
    ischumba = random.choice(magic_ball_chumba)
    await inter.response.send_message(f"*{question.strip('?')}?*\nМоя відповідь: **{response}{ischumba}**")


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        await bot.tree.sync()  # Синхронизация слэш-команд
        print("Slash commands have been synchronized.")
    except Exception as e:
        print(f"Error during command synchronization: {e}")
    scheduler = AsyncIOScheduler()
    trigger = CronTrigger(day_of_week='mon-fri', hour=22, minute=34)  # Установите время отправки (9:00 утра)
    scheduler.add_job(daily_tracker, trigger)
    scheduler.start()


@bot.slash_command(description="Отримати прогноз погоди")
async def weather(inter, city: str = 'Dnipro'):
    api_key = os.getenv("WEATHER_API_KEY")
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric"
    response = requests.get(url).json()

    if response.get("main"):

        temp = response["main"]["temp"]
        description = response["weather"][0]["description"]
        sunset = datetime.datetime.fromtimestamp(response["sys"]["sunset"], tz=datetime.timezone(
            datetime.timedelta(seconds=response['timezone']))).strftime("%H:%M")
        sunrise = datetime.datetime.fromtimestamp(response["sys"]["sunrise"], tz=datetime.timezone(
            datetime.timedelta(seconds=response['timezone']))).strftime("%H:%M")
        wind = response['wind']["speed"]
        clouds = response["clouds"]["all"]
        dt = datetime.datetime.fromtimestamp(response["dt"], tz=datetime.timezone(
            datetime.timedelta(seconds=response['timezone']))).strftime("%H:%M")
        country = response["sys"]["country"]
        city = response["name"]
        icon_url = f"http://openweathermap.org/img/wn/{response['weather'][0]['icon']}@2x.png"

        embed = disnake.Embed(title=f"**{city} :flag_{country.lower()}:**")
        embed.set_thumbnail(url=icon_url)
        embed.add_field(name="🌡️ Температура", value=f"{temp}°C", inline=True)
        embed.add_field(name="☁️ Хмарність", value=f"{clouds}%", inline=True)
        embed.add_field(name="🌬️ Вітер", value=f"{wind}m/s", inline=True)
        embed.add_field(name="🕒️ Місцевий час", value=f"{dt}", inline=True)
        embed.add_field(name="☀️ Схід сонця", value=f"{sunrise}", inline=True)
        embed.add_field(name="🌑 Захід сонця", value=f"{sunset}", inline=True)

        await inter.response.send_message(embed=embed)
    else:
        await inter.response.send_message(f"Не вдалося отримати погоду для міста {city}")


@bot.slash_command(description="Отримати випадковий жарт")
async def joke(inter, language: str = None):
    if language.lower() in ("ua", "рідна", "українська", "ukr", 'укр', 'uk', 'ukrainian', 'ukraine'):
        url = "https://v2.jokeapi.dev/joke/Any?lang=uk"
    else:
        url = "https://v2.jokeapi.dev/joke/Any"
    response = requests.get(url).json()
    if response["type"] == "single":
        joke = response["joke"]
    else:
        joke = f"{response['setup']}\n{response['delivery']}"
    await inter.response.send_message(joke)


@bot.slash_command(name='tracker', description='Вивести список трекерів')
async def items_command(inter):
    await inter.response.defer()
    for item in items:
        message = await inter.channel.send(f"`🟢` {item['name']} вільний\n", delete_after=72_000)
        item['message_id'] = message.id
        await message.add_reaction(item['emoji'])
    await inter.send(content="╼╼╼╼", ephemeral=False)


# async def delete_message_after_delay(channel, message, delay):
#     await asyncio.sleep(delay)
#     await message.delete()

async def process_reaction(payload, add):
    guild = bot.get_guild(payload.guild_id)
    channel = guild.get_channel(payload.channel_id)
    message = await channel.fetch_message(payload.message_id)
    user = guild.get_member(payload.user_id)

    if user is None or user.bot:
        return

    if message.author != bot.user:
        return

    for item in items:
        if payload.message_id == item.get('message_id') and str(payload.emoji) == item['emoji']:
            if add:
                if item['status'] is None:
                    # Занимаем
                    item['status'] = user
                    await message.edit(content=f"`🔴` {item['name']} зайняв(ла) {user.mention}\n")
                    await channel.send(f'{user.mention} зараз на трекері {item["name"]}', delete_after=1800)

                # else:
                #     # занят другим пользователем
                #     await channel.send(f'{user.mention}, этот трекер уже занят {item["status"].mention}.',
                #                        delete_after=5)
                #     await message.remove_reaction(payload.emoji, user)
            else:
                if item['status'] == user:
                    # Освобождаем
                    item['status'] = None
                    await message.edit(content=f"`🟢` {item['name']} зараз вільний\n")
                    await channel.send(f'{user.mention} звільнив(ла) трекер {item["name"]}', delete_after=1800)

translator = Translator()

@bot.message_command(name="Text 🠒 English 🇬🇧")
async def translate_message(inter, message: disnake.Message):
    try:
        translated = translator.translate(message.content, dest='en')
        await inter.response.send_message(f"{translated.text}", ephemeral=True)
    except Exception as e:
        await inter.response.send_message(f"Помилка при перекладі: {str(e)}")

@bot.message_command(name="Text 🠒 Ru💩")
async def translate_message(inter, message: disnake.Message):
    try:
        translated = translator.translate(message.content, dest='ru')
        await inter.response.send_message(f"{translated.text}", ephemeral=True)
    except Exception as e:
        await inter.response.send_message(f"Помилка при перекладі: {str(e)}")

@bot.message_command(name="Text 🠒 UA 🇺🇦")
async def translate_message(inter, message: disnake.Message):
    try:
        translated = translator.translate(message.content, dest='uk')
        await inter.response.send_message(f"{translated.text}", ephemeral=True)
    except Exception as e:
        await inter.response.send_message(f"Помилка при перекладі: {str(e)}")

@bot.message_command(name="📄 Translate & Publish to English")
async def translate_message(inter, message: disnake.Message):
    try:
        translated = translator.translate(message.content, dest='en')
        await message.add_reaction("📄")  # Добавляем реакцию к оригинальному сообщению
        await inter.response.send_message(f"{translated.text}")
    except Exception as e:
        await inter.response.send_message(f"Помилка при перекладі: {str(e)}")

@bot.message_command(name="📄 Translate & Publish to Ru")
async def translate_message(inter, message: disnake.Message):
    try:
        translated = translator.translate(message.content, dest='ru')
        await message.add_reaction("📄")  # Добавляем реакцию к оригинальному сообщению
        await inter.response.send_message(f"{translated.text}")
    except Exception as e:
        await inter.response.send_message(f"Помилка при перекладі: {str(e)}")


@bot.event
async def on_raw_reaction_add(payload):
    await process_reaction(payload, True)


@bot.event
async def on_raw_reaction_remove(payload):
    await process_reaction(payload, False)


async def daily_tracker():
    channel = bot.get_channel('1014562370317725764')  # замените YOUR_CHANNEL_ID на ID вашего канала
    if channel:
        for item in items:
            message = await channel.send(f"`🟢` {item['name']} вільний\n", delete_after=72_000)
            item['message_id'] = message.id
            await message.add_reaction(item['emoji'])


bot.run(os.getenv("TOKEN"))
