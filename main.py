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
import pytz

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
    timezone = pytz.timezone('Europe/Kiev')
    trigger = CronTrigger(day_of_week='mon-fri', hour=7, minute=00, timezone=timezone)
    scheduler.add_job(daily_tracker, trigger)
    scheduler.start()
    print("Планировщик запущен...")


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
async def joke(inter):
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
        message = await inter.channel.send(f"`🟢` {item['name']} зараз вільний\n", delete_after=72_000)
        item['message_id'] = message.id
        await message.add_reaction(item['emoji'])
    await inter.send(content="Ручний виклик - Оновлюю список трекерів", ephemeral=False)


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

    timezone = pytz.timezone('Europe/Kiev')  # Установите вашу временную зону
    current_time = datetime.datetime.now(timezone).strftime("%H:%M")

    for item in items:
        if payload.message_id == item.get('message_id') and str(payload.emoji) == item['emoji']:
            if add:
                if item['status'] is None:
                    # Занимаем
                    item['status'] = user
                    await message.edit(content=f"`🔴` {item['name']} зайняв(ла) {user.mention} o {current_time}\n")
                    await channel.send(f'{current_time} - {user.mention} зараз на трекері {item["name"]}', delete_after=28800)

            else:
                if item['status'] == user and '**Upwork**' in item['name']:
                    upwork_time = current_time
                    item['status'] = None
                    await message.edit(content=f"`🟡` {item['name']} вільний з {current_time}, але зачекай ще ~10 хвилин")
                    await channel.send(f'{current_time} - {user.mention} звільнив(ла) трекер {item["name"]}', delete_after=28800)

                    await asyncio.sleep(600)
                    if item['status'] == None:
                        await message.edit(content=f"`🟢` {item['name']} вільний з {upwork_time}\n")

                elif item['status'] == user:
                    item['status'] = None
                    await message.edit(content=f"`🟢` {item['name']} вільний з {current_time}\n")
                    await channel.send(f'{current_time} - {user.mention} звільнив(ла) трекер {item["name"]}', delete_after=28800)

translator = Translator()

@bot.message_command(name="Text 🠒 Ru")
async def translate_message(inter, message: disnake.Message):
    try:
        translated = translator.translate(message.content, dest='ru')

        # Создаем кнопку "Опубликовать"
        publish_button = disnake.ui.Button(label="Цей переклад бачите лише Ви, натисніть тут, щоб опублікувати переклад в чат", style=disnake.ButtonStyle.blurple)
        delete_button = disnake.ui.Button(label="Видалити переклад", style=disnake.ButtonStyle.red)

        async def publish_callback(button_interaction):
            await inter.channel.send(f"**Text 🠒 Ru:**\n\n{translated.text}")  # Отправляем переведенное сообщение как обычный текст
            await button_interaction.response.edit_message(content="Повідомлення опубліковано", view=None)
            await button_interaction.delete_original_message()

        async def delete_callback(button_interaction):
            await button_interaction.response.edit_message(content="Переклад видалено", view=None)
            await button_interaction.delete_original_message()  # Удаление первоначального сообщения


        publish_button.callback = publish_callback
        delete_button.callback = delete_callback

        view = disnake.ui.View()
        view.add_item(delete_button)
        view.add_item(publish_button)


        await inter.response.send_message(f"{translated.text}\n.", view=view, ephemeral=True)
    except Exception as e:
        await inter.response.send_message(f"Помилка при перекладі: {str(e)}\n\nБудь ласка, надішліть це повідомлення <@236912374685106176>", ephemeral=True)

@bot.message_command(name="Text 🠒 Ua")
async def translate_message(inter, message: disnake.Message):
    try:
        translated = translator.translate(message.content, dest='uk')

        # Создаем кнопку "Опубликовать"
        publish_button = disnake.ui.Button(label="Цей переклад бачите лише Ви, натисніть тут, щоб опублікувати переклад в чат", style=disnake.ButtonStyle.blurple)
        delete_button = disnake.ui.Button(label="Видалити переклад", style=disnake.ButtonStyle.red)

        async def publish_callback(button_interaction):
            await inter.channel.send(f"**Text 🠒 Ua:**\n\n{translated.text}")  # Отправляем переведенное сообщение как обычный текст
            await button_interaction.response.edit_message(content="Повідомлення опубліковано", view=None)
            await button_interaction.delete_original_message()

        async def delete_callback(button_interaction):
            await button_interaction.response.edit_message(content="Переклад видалено", view=None)
            await button_interaction.delete_original_message()  # Удаление первоначального сообщения


        delete_button.callback = delete_callback
        publish_button.callback = publish_callback

        view = disnake.ui.View()
        view.add_item(delete_button)
        view.add_item(publish_button)

        await inter.response.send_message(f"{translated.text}\n.", view=view, ephemeral=True)
    except Exception as e:
        await inter.response.send_message(f"Помилка при перекладі: {str(e)}\n\nБудь ласка, надішліть це повідомлення <@236912374685106176>", ephemeral=True)

@bot.message_command(name="Text 🠒 Eng")
async def translate_message(inter, message: disnake.Message):
    try:
        translated = translator.translate(message.content, dest='en')

        # Создаем кнопку "Опубликовать"
        publish_button = disnake.ui.Button(label="Цей переклад бачите лише Ви, натисніть тут, щоб опублікувати переклад в чат", style=disnake.ButtonStyle.blurple)
        delete_button = disnake.ui.Button(label="Видалити переклад", style=disnake.ButtonStyle.red)

        async def publish_callback(button_interaction):
            await inter.channel.send(f"**Text 🠒 Eng:**\n\n{translated.text}")  # Отправляем переведенное сообщение как обычный текст
            await button_interaction.response.edit_message(content="Повідомлення опубліковано", view=None)
            await button_interaction.delete_original_message()

        async def delete_callback(button_interaction):
            await button_interaction.response.edit_message(content="Переклад видалено", view=None)
            await button_interaction.delete_original_message()  # Удаление первоначального сообщения

        publish_button.callback = publish_callback
        delete_button.callback = delete_callback

        view = disnake.ui.View()
        view.add_item(delete_button)
        view.add_item(publish_button)

        await inter.response.send_message(f"{translated.text}\n.", view=view, ephemeral=True)
    except Exception as e:
        await inter.response.send_message(f"Помилка при перекладі: {str(e)}\n\nБудь ласка, надішліть це повідомлення <@236912374685106176>", ephemeral=True)


@bot.event
async def on_raw_reaction_add(payload):
    await process_reaction(payload, True)


@bot.event
async def on_raw_reaction_remove(payload):
    await process_reaction(payload, False)


async def daily_tracker():
    channel = bot.get_channel(1218888187087421453)  #ID трекерный-движ
    if channel:
        for item in items:
            message = await channel.send(f"`🟢` {item['name']} зараз вільний\n", delete_after=72_000)
            item['message_id'] = message.id
            await message.add_reaction(item['emoji'])


bot.run(os.getenv("TOKEN"))
