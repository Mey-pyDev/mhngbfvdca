import disnake #https://ru.guide.disnake.dev/interactions/slash-commands
from disnake.ext import commands, tasks
import datetime
import asyncio
import random

intents = disnake.Intents.default()
intents.message_content = True
intents.reactions = True
intents.members = True

command_sync_flags = commands.CommandSyncFlags.default()
command_sync_flags.sync_commands_debug = True

bot = commands.Bot(command_prefix='-', command_sync_flags=command_sync_flags, intents=intents)

items = [{'emoji': '⌚', 'name': '**Upwork** Pavlo', 'status': None, 'message_id': None},
         {'emoji': '⌚', 'name': '**Hubstuff** Pavlo', 'status': None, 'message_id': None},
         {'emoji': '⌚', 'name': '**Hubstuff** "SoundBox"', 'status': None, 'message_id': None},
         {'emoji': '⌚', 'name': '**Clockify**', 'status': None, 'message_id': None},
         {'emoji': '⌚', 'name': '**Hubstuff** Varvara', 'status': None, 'message_id': None},]
log = []
magic_ball_responses = ["Бесспорно", "Предрешено", "Никаких сомнений", "Определённо да", "Можешь быть уверен в этом",
                        "Мне кажется — «да»", "Вероятнее всего", "Хорошие перспективы", "Знаки говорят — «да»",
                        "Да", "Пока не ясно, попробуй снова", "Спроси позже", "Лучше не рассказывать",
                        "Сейчас нельзя предсказать", "Сконцентрируйся и спроси опять", "Даже не думай",
                        "Мой ответ — «нет»", "По моим данным — «нет»", "Перспективы не очень хорошие", "Весьма сомнительно"]


@bot.slash_command(description="Задать вопрос магическому шару")
async def magicball(inter, question: str):
    response = random.choice(magic_ball_responses)
    await inter.response.send_message(f"*{question.capitalize().strip('?')}?*\nМой ответ: **{response}**")


@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}')
    try:
        await bot.tree.sync()  # Синхронизация слэш-команд
        print("Slash commands have been synchronized.")
    except Exception as e:
        print(f"Error during command synchronization: {e}")

@bot.slash_command(name='tracker', description='Вывести список трекеров')
async def items_command(inter):
    await inter.response.defer()
    for item in items:
        message = await inter.channel.send(f"`🟢` {item['name']} свободен\n")
        item['message_id'] = message.id
        await message.add_reaction(item['emoji'])
    # await inter.send(content="Tracker list ↓\n\n", ephemeral=False)

@bot.slash_command(name='log', description='Показать журнал использования трекеров')
async def log_command(inter, member: disnake.Member = None):
    await inter.response.defer()  # Уведомляем Discord, что команда обрабатывается
    if log:
        if member:
            log_entries = [f"{entry['time']} - {entry['item']} {entry['action']} {entry['user'].mention}" for entry in log if entry['user'] == member]
            if log_entries:
                message = await inter.edit_original_message(content=f">>> Журнал использования трекеров для {member.mention}:\n" + "\n".join(log_entries))
            else:
                message = await inter.edit_original_message(content=f">>> Журнал использования трекеров для {member.mention} пуст.")
        else:
            log_entries = [f"{entry['time']} - {entry['item']} {entry['action']} {entry['user'].mention}" for entry in log]
            message = await inter.edit_original_message(content=">>> Журнал использования трекеров:\n" + "\n".join(log_entries))
    else:
        message = await inter.edit_original_message(content=">>> Журнал использования трекеров пуст.")

    await delete_message_after_delay(inter.channel, message, delay=300)

async def delete_message_after_delay(channel, message, delay):
    await asyncio.sleep(delay)
    await message.delete()

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
                    # Занимаем пункт
                    item['status'] = user
                    await message.edit(content=f"`🔴` {item['name']} занят {user.mention}\n")
                    await channel.send(f'{user.mention} сейчас на трекере {item["name"]}', delete_after=60)
                    # Добавляем запись в журнал
                    log.append({
                        'time': datetime.datetime.now().strftime("%H:%M:%S"),
                        'action': 'занял',
                        'item': item['name'],
                        'user': user
                    })

                else:
                    # Пункт уже занят другим пользователем
                    await channel.send(f'{user.mention}, этот трекер уже занят {item["status"].mention}.', delete_after=5)
                    await message.remove_reaction(payload.emoji, user)
            else:
                if item['status'] == user:
                    # Освобождаем
                    item['status'] = None
                    await message.edit(content=f"`🟢` {item['name']} свободен\n")
                    await channel.send(f'{user.mention} вышел с трекера {item["name"]}', delete_after=60)
                    # Добавляем запись в журнал
                    log.append({
                        'time': datetime.datetime.now().strftime("%H:%M:%S"),
                        'action': 'освободил',
                        'item': item['name'],
                        'user': user
                    })

@bot.event
async def on_raw_reaction_add(payload):
    await process_reaction(payload, True)

@bot.event
async def on_raw_reaction_remove(payload):
    await process_reaction(payload, False)

bot.run('MTI0NzU0MTY2NjU2MzQ4OTg2NA.GsTV9S.H6HAPkA03QiyDlhh3AH2yODmAL7-s6QzyAzmh4')
