import logging
import telebot
from telebot.handler_backends import State, StatesGroup
from telebot.storage import StateMemoryStorage

from django.conf import settings

# Получение комманд
commands = settings.BOT_COMMANDS
state_storage = StateMemoryStorage()

# Инициализация бота
bot = telebot.TeleBot(
    settings.BOT_TOKEN,
    threaded=False,
    skip_pending=True,
    state_storage=state_storage
)

class UsersStates(StatesGroup):
    help_request = State()

# Установка комманд для бота
bot.set_my_commands(commands)

logging.info(f'@{bot.get_me().username} started')

logger = telebot.logger
logger.setLevel(logging.INFO)

logging.basicConfig(level=logging.INFO, filename="ai_log.log", filemode="w")