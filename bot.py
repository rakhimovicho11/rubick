import asyncio
import random
import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.bot import DefaultBotProperties
from bracket_visual import generate_bracket_image

# Загрузка переменных из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME")

# Настройка бота
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

# Данные
registered_teams = []
registered_players = set()
registered_dota_ids = set()
match_results = {}  # ✅ добавлено

# FSM состояния
class Registration(StatesGroup):
    waiting_for_team_name = State()
    waiting_for_team_players = State()

# Главное меню
main_menu = InlineKeyboardMarkup(inline_keyboard=[
    [
        InlineKeyboardButton(text="✨ Зарегистрировать команду", callback_data="register"),
        InlineKeyboardButton(text="📝 Команды", callback_data="show_commands"),
    ],
    [
        InlineKeyboardButton(text="❓ Помощь", callback_data="help"),
        InlineKeyboardButton(text="ℹ️ О боте", callback_data="about"),
    ],
])

# Команды
async def set_commands():
    commands = [
        BotCommand(command="start", description="Запустить бота и открыть меню"),
        BotCommand(command="help", description="Получить помощь и инструкции"),
        BotCommand(command="register", description="Зарегистрировать команду"),
        BotCommand(command="about", description="Узнать о боте и турнирах"),
        BotCommand(command="report_result", description="Отправить результат матча"),
        BotCommand(command="generate_bracket", description="Начать генерацию турнирной сетки (может только администратор)"),
    ]
    await bot.set_my_commands(commands)

# Командные обработчики
@dp.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "🎉 <b>Привет, чемпион!</b>\n\n"
        "Добро пожаловать в Лавку Рубика 🧩 — место, где рождаются легенды!\n\n"
        "Здесь ты сможешь легко и быстро зарегистрировать свою команду на наши турниры.\n\n"
        "<i>Готов показать скилл и взорвать сцену? Давай начнем!</i>",
        reply_markup=main_menu
    )

@dp.message(Command("register"))
async def cmd_register(message: Message, state: FSMContext):
    if len(registered_teams) >= 16:
        await message.answer("❌ Регистрация завершена! Все 16 слотов заняты.")
        return
    await message.answer("🚀 Введи название своей команды:")
    await state.set_state(Registration.waiting_for_team_name)

@dp.message(Command("help"))
async def cmd_help(message: Message):
    await message.answer(
        "❓ <b>Нужна помощь?</b>\n\n"
        "Если у тебя возникли проблемы с регистрацией команды или возникли другие вопросы, пиши администратору: <b>@laziz_rahimovich</b>\n\n"
        "Также не забудь подписаться на наш канал: <a href='https://t.me/rubickshop'>@rubickshop</a>",
        disable_web_page_preview=True,
        reply_markup=main_menu
    )

@dp.message(Command("about"))
async def cmd_about(message: Message):
    await message.answer(
        "🧩 <b>О боте Лавки Рубика</b>\n\n"
        "Этот бот создан, чтобы помочь тебе и твоей команде легко и быстро регистрироваться на турниры нашего канала.\n"
        "Здесь собираются только лучшие игроки, которые горят желанием побеждать и развиваться!\n\n"
        "🔥 Наш канал: <a href='https://t.me/rubickshop'>@rubickshop</a>\n"
        "🚀 Готовься к эпичным матчам и незабываемым эмоциям!\n\n"
        "Если есть вопросы — просто напиши мне в личку: <b>@laziz_rahimovich</b>.",
        disable_web_page_preview=True,
        reply_markup=main_menu
    )

@dp.message(Command("reset_data"))
async def reset_data(message: Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ У тебя нет прав.")
    registered_teams.clear()
    registered_players.clear()
    registered_dota_ids.clear()
    match_results.clear()
    await message.answer("✅ Все данные сброшены!")


@dp.message(Command("generate_bracket"))
async def manual_generate(message: Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Только админ может генерировать сетку.")
        return
    if len(registered_teams) < 16:
        await message.answer("⏳ Нужно 16 зарегистрированных команд.")
        return
    await generate_bracket()
    await message.answer("✅ Сетка сгенерирована и отправлена капитанам!")

from datetime import datetime, timedelta

async def generate_bracket():
    global tournament_bracket, match_id_counter, current_round
    sorted_teams = sorted(registered_teams, key=lambda x: x['avg_mmr'])
    random.shuffle(sorted_teams)
    tournament_bracket = []
    match_id_counter = 1
    current_round = 1

    # Время начала первого матча — через 2 часа
    base_start_time = datetime.now() + timedelta(hours=2)

    for i in range(0, 16, 2):
        match_time = base_start_time + timedelta(hours=i // 2)

        match = {
            "team1": sorted_teams[i],
            "team2": sorted_teams[i + 1],
            "match_id": match_id_counter,
            "start_time": match_time
        }
        tournament_bracket.append(match)

        # Создаем задачу на напоминания
        asyncio.create_task(schedule_reminders(
            match["team1"], match["team2"], match["match_id"], match["start_time"]
        ))

        match_id_counter += 1

    # Генерация изображения сетки
    bracket_data = [[(match["team1"]["name"], match["team2"]["name"]) for match in tournament_bracket]]
    file_path = generate_bracket_image(bracket_data)

    # Рассылка картинки капитанам
    for match in tournament_bracket:
        for captain_id in (match["team1"]["captain_id"], match["team2"]["captain_id"]):
            await bot.send_photo(captain_id, photo=open(file_path, "rb"))

    # Сообщение админу
    match_list = "\n".join([
        f"Матч #{match['match_id']}: {match['team1']['name']} vs {match['team2']['name']}"
        for match in tournament_bracket
    ])
    await bot.send_message(ADMIN_ID, f"📊 <b>Турнирная сетка — Раунд 1</b>\n\n{match_list}")

    await notify_round_matches()


async def notify_round_matches():
    for team1, team2, match_id in tournament_bracket:
        text = (
            f"🏆 <b>Турнир Rubick Cup — Раунд {current_round}</b>\n\n"
            f"🎮 Матч <b>#{match_id}</b>\n"
            f"<b>{team1['name']}</b> vs <b>{team2['name']}</b>\n\n"
            f"📌 Капитаны, после матча используйте команду:\n"
            f"<code>/report_result {match_id} Имя_Победителя</code>\n"
        )
        try:
            await bot.send_message(team1['captain_id'], text)
            await bot.send_message(team2['captain_id'], text)
        except Exception as e:
            await bot.send_message(ADMIN_ID, f"❗ Ошибка при уведомлении капитанов: {e}")

@dp.message(Command("report_result"))
async def report_result_handler(message: Message):
    args = message.text.split()[1:]
    if len(args) < 2:
        await message.answer("❌ Используй: /report_result MATCH_ID ИМЯ_ПОБЕДИТЕЛЯ")
        return

    try:
        match_id = int(args[0])
    except ValueError:
        await message.answer("❌ MATCH_ID должен быть числом.")
        return

    winner_name = " ".join(args[1:]).strip().lower()
    match = next((m for m in tournament_bracket if m[2] == match_id), None)
    if not match:
        await message.answer(f"❌ Матч #{match_id} не найден.")
        return

    team1, team2, _ = match
    if winner_name not in (team1["name"].lower(), team2["name"].lower()):
        await message.answer("❌ Победитель должен быть одной из команд в этом матче.")
        return

    if match_id in match_results:
        await message.answer("⚠️ Результат уже был отправлен.")
        return

    if message.from_user.id not in (team1["captain_id"], team2["captain_id"]):
        await message.answer("❌ Только капитан участвующей команды может отправлять результат.")
        return

    match_results[match_id] = winner_name
    loser = team2 if winner_name == team1["name"].lower() else team1

    await message.answer(f"✅ Результат принят! Победила команда <b>{winner_name.title()}</b>.")
    await bot.send_message(
        ADMIN_ID,
        f"⚔️ Результат матча #{match_id}:\n"
        f"✅ Победитель: <b>{winner_name.title()}</b>\n"
        f"❌ Проигравший: <b>{loser['name']}</b>"
    )

# Callback-кнопки
@dp.callback_query(lambda c: c.data == "register")
async def register_callback(callback: CallbackQuery, state: FSMContext):
    if len(registered_teams) >= 16:
        await callback.message.answer("❌ Регистрация завершена! Все 16 слотов заняты.")
        await callback.answer()
        return
    await callback.message.answer("🚀 Введи название своей команды:")
    await state.set_state(Registration.waiting_for_team_name)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "help")
async def callback_help(callback: CallbackQuery):
    await callback.message.answer(
        "❓ <b>Нужна помощь?</b>\n\n"
        "Если у тебя возникли проблемы с регистрацией команды или возникли другие вопросы, пиши администратору: <b>@laziz_rahimovich</b>\n\n"
        "Также не забудь подписаться на наш канал: <a href='https://t.me/rubickshop'>@rubickshop</a>",
        disable_web_page_preview=True,
        reply_markup=main_menu
    )
    await callback.answer()

@dp.callback_query(lambda c: c.data == "about")
async def callback_about(callback: CallbackQuery):
    await callback.message.answer(
        "🧩 <b>О боте Лавки Рубика</b>\n\n"
        "Этот бот создан, чтобы помочь тебе и твоей команде легко и быстро регистрироваться на турниры нашего канала.\n"
        "Здесь собираются только лучшие игроки, которые горят желанием побеждать и развиваться!\n\n"
        "🔥 Наш канал: <a href='https://t.me/rubickshop'>@rubickshop</a>\n"
        "🚀 Готовься к эпичным матчам и незабываемым эмоциям!\n\n"
        "Если есть вопросы — просто напиши мне в личку: <b>@laziz_rahimovich</b>.",
        disable_web_page_preview=True,
        reply_markup=main_menu
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data == "show_commands")
async def show_commands_callback(callback: CallbackQuery):
    await callback.message.answer(
        "📝 <b>Доступные команды бота:</b>\n"
        "/start – Главное меню\n"
        "/register – Регистрация команды\n"
        "/report_result – Отправить результат матча\n"
        "/help – Обратиться за помощью\n"
        "/about – Информация о турнире",
        reply_markup=main_menu
    )
    await callback.answer()

# Обработка регистрации
@dp.message(Registration.waiting_for_team_name)
async def process_team_name(message: Message, state: FSMContext):
    name = message.text.strip()
    if not name:
        await message.answer("❌ Название команды не может быть пустым.")
        return
    if any(team["name"].lower() == name.lower() for team in registered_teams):
        await message.answer("❌ Такое имя уже занято.")
        return
    await state.update_data(team_name=name)
    await message.answer("✍️ Теперь введи игроков (5 строк):\n@user DotaID MMR")
    await state.set_state(Registration.waiting_for_team_players)

@dp.message(Registration.waiting_for_team_players)
async def process_players(message: Message, state: FSMContext):
    lines = message.text.strip().splitlines()
    if len(lines) != 5:
        await message.answer("❌ Нужно ровно 5 игроков.")
        return

    team_data = []
    usernames_in_team = set()
    dota_ids_in_team = set()
    user_ids_to_check = []

    for i, line in enumerate(lines, 1):
        parts = line.split()
        if len(parts) != 3:
            await message.answer(f"❌ Ошибка в строке {i}. Формат: @user DotaID MMR")
            return
        username, dota_id, mmr = parts
        if not dota_id.isdigit() or not mmr.isdigit():
            await message.answer(f"❌ DotaID и MMR должны быть числами. Строка {i}")
            return
        if username in registered_players or dota_id in registered_dota_ids:
            await message.answer(f"❌ Игрок {username} или DotaID {dota_id} уже участвует.")
            return
        if username in usernames_in_team or dota_id in dota_ids_in_team:
            await message.answer(f"❌ Дубликат в команде: {username} / {dota_id}")
            return
        usernames_in_team.add(username)
        dota_ids_in_team.add(dota_id)
        team_data.append((username, dota_id, int(mmr)))

    # Чекаем подписку у всех участников команды
    failed_usernames = []
    for username in usernames_in_team:
        try:
            user = await bot.get_chat(username)
            member = await bot.get_chat_member(CHANNEL_USERNAME, user.id)
            if member.status not in ("member", "administrator", "creator"):
                failed_usernames.append(username)
        except:
            failed_usernames.append(username)

    if failed_usernames:
        await message.answer(
            f"❌ Эти участники команды не подписаны на канал {CHANNEL_USERNAME}:\n" +
            "\n".join(failed_usernames) +
            "\n\nПопроси их подписаться и попробуй снова."
        )
        return

    data = await state.get_data()
    team_name = data["team_name"]

    registered_teams.append({
        "name": team_name,
        "players": team_data,
        "avg_mmr": sum(p[2] for p in team_data) // 5,
        "captain_id": message.from_user.id
    })

    for username, dota_id, _ in team_data:
        registered_players.add(username)
        registered_dota_ids.add(dota_id)

    await message.answer(f"✅ Команда <b>{team_name}</b> зарегистрирована!", reply_markup=main_menu)
    await bot.send_message(
        ADMIN_ID,
        f"🔥 Новая команда: <b>{team_name}</b>\n" +
        "\n".join(f"{u} | {d}" for u, d, _ in team_data)
    )
    await state.clear()


# Проверка подписки
async def is_user_subscribed(user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False

# Webhook (aiohttp)
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME')}{WEBHOOK_PATH}"

async def on_startup(bot: Bot):
    await set_commands()
    await bot.set_webhook(WEBHOOK_URL)
    print(f"✅ Webhook установлен: {WEBHOOK_URL}")

async def on_shutdown(bot: Bot):
    await bot.delete_webhook()
    print("🛑 Webhook удалён")

async def main():
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)
    return app

# Напоминания перед матчами
async def schedule_reminders(team1, team2, match_id, match_time):
    now = datetime.now()
    in_1h = (match_time - timedelta(hours=1)) - now
    in_30m = (match_time - timedelta(minutes=30)) - now

    if in_1h.total_seconds() > 0:
        await asyncio.sleep(in_1h.total_seconds())
        await send_reminder(team1, team2, match_id, "⏰ До матча остался 1 час!")

    if in_30m.total_seconds() > 0:
        await asyncio.sleep(in_30m.total_seconds())
        await send_reminder(team1, team2, match_id, "⏳ До матча осталось 30 минут!")

async def send_reminder(team1, team2, match_id, text):
    message = (
        f"{text}\n\n"
        f"🎮 Матч <b>#{match_id}</b>: <b>{team1['name']}</b> vs <b>{team2['name']}</b>\n"
        f"📌 Подготовьтесь заранее!"
    )
    try:
        await bot.send_message(team1["captain_id"], message)
        await bot.send_message(team2["captain_id"], message)
    except Exception as e:
        await bot.send_message(ADMIN_ID, f"❗ Ошибка при отправке напоминания: {e}")

if __name__ == "__main__":
    web.run_app(main(), host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
