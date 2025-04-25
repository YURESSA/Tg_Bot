import os

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import (ReplyKeyboardMarkup, KeyboardButton,
                           Message, InlineKeyboardMarkup,
                           InlineKeyboardButton)
from aiogram.utils import executor
from dotenv import load_dotenv

load_dotenv()

api = os.getenv("API_TOKEN")
bot = Bot(token=api)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

MAX_QUESTION_LENGTH = 700
MAX_ANSWER_LENGTH = 2000
MAX_VISIBLE_QUESTIONS = 3

CURATOR_ID = os.getenv("CURATOR_ID")
user_data_storage = {}
pending_responses = {}


class UserState(StatesGroup):
    waiting_for_contact = State()
    waiting_for_question = State()


class CuratorState(StatesGroup):
    waiting_for_response = State()


from html import escape


def escape_html(text: str) -> str:
    """Экранирует HTML-символы в тексте"""
    return escape(text)


def get_contact_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('Отправить свой контакт ☎️', request_contact=True))
    return kb


def get_question_keyboard():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton('Задать еще вопрос'))
    return kb


def format_question_history(questions):
    """Форматирует историю вопросов для отображения"""
    if len(questions) <= MAX_VISIBLE_QUESTIONS:
        return "\n".join([f"{i + 1}. {q[:150]}{'...' if len(q) > 150 else ''}" for i, q in enumerate(questions)])

    visible = questions[-MAX_VISIBLE_QUESTIONS:]
    history_text = "\n".join(
        [f"{len(questions) - MAX_VISIBLE_QUESTIONS + i + 1}. {q[:150]}{'...' if len(q) > 150 else ''}"
         for i, q in enumerate(visible)])
    return f"📜 Последние {MAX_VISIBLE_QUESTIONS} вопроса (всего {len(questions)}):\n{history_text}"


def create_curator_keyboard(user_id, has_history=False):
    """Создает клавиатуру для сообщения куратору"""
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Ответить", callback_data=f"reply_{user_id}"))
    if has_history:
        kb.add(InlineKeyboardButton("Показать всю историю", callback_data=f"full_history_{user_id}"))
    return kb


def is_valid_message(message: types.Message, is_question: bool) -> bool:
    """Проверяет сообщение с учетом типа (вопрос или ответ)"""
    if not message.text:
        return False
    max_len = MAX_QUESTION_LENGTH if is_question else MAX_ANSWER_LENGTH
    return len(message.text) <= max_len


# Обработчики для студентов
@dp.message_handler(commands=['start'])
async def starting(message: types.Message):
    user_id = message.from_user.id
    if user_id not in user_data_storage:
        await message.answer('Привет! Это бот поддержки для участников олимпиады.')
        await message.answer('Для начала, поделись контактом для связи 👇',
                             reply_markup=get_contact_keyboard())
        await UserState.waiting_for_contact.set()
    else:
        await message.answer(f"Задайте свой вопрос куратору (не более {MAX_QUESTION_LENGTH} символов):",
                             reply_markup=types.ReplyKeyboardRemove())
        await UserState.waiting_for_question.set()


@dp.message_handler(content_types=['contact'], state=UserState.waiting_for_contact)
async def handle_contact(message: Message, state: FSMContext):
    contact = message.contact
    user_id = message.from_user.id

    if contact.user_id == user_id:
        user_data_storage[user_id] = {
            'phone_number': contact.phone_number,
            'full_name': message.from_user.full_name,
            'username': f"@{message.from_user.username}" if message.from_user.username else "Нет username",
            'questions': []
        }

        await message.answer(f"Спасибо! Теперь задайте свой вопрос куратору (не более {MAX_QUESTION_LENGTH} символов):",
                             reply_markup=types.ReplyKeyboardRemove())
        await UserState.waiting_for_question.set()
    else:
        await message.answer("Пожалуйста, отправьте именно свой контакт!",
                             reply_markup=get_contact_keyboard())


@dp.message_handler(text='Задать еще вопрос', state='*')
async def ask_another_question(message: types.Message):
    user_id = message.from_user.id
    if user_id in user_data_storage:
        await message.answer(f"Задайте свой вопрос куратору (не более {MAX_QUESTION_LENGTH} символов):",
                             reply_markup=types.ReplyKeyboardRemove())
        await UserState.waiting_for_question.set()
    else:
        await message.answer("Пожалуйста, сначала отправьте контакт через команду /start",
                             reply_markup=get_contact_keyboard())


@dp.message_handler(state=UserState.waiting_for_question, content_types=types.ContentTypes.TEXT)
async def handle_question(message: types.Message, state: FSMContext):
    if not is_valid_message(message, is_question=True):
        await message.answer(
            f"❌ Ваше сообщение слишком длинное. Пожалуйста, ограничьте вопрос {MAX_QUESTION_LENGTH} символами.")
        return

    user_id = message.from_user.id
    question = escape_html(message.text)  # Экранируем HTML-символы

    if user_id in user_data_storage:
        user_data = user_data_storage[user_id]
        user_data['questions'].append(question)

        # Форматируем историю вопросов
        question_history = format_question_history(user_data['questions'])
        has_history = len(user_data['questions']) > MAX_VISIBLE_QUESTIONS

        # Создаем компактное сообщение для куратора
        msg_text = (
            f"📌 Вопрос от {escape_html(user_data['full_name'])} (ID: <code>{user_id}</code>)\n"
            f"📱 {escape_html(user_data['username'])} | ☎️ {escape_html(user_data['phone_number'])}\n\n"
            f"❓ Вопрос:\n{question[:500]}{'...' if len(question) > 500 else ''}\n\n"
            f"{question_history}"
        )

        # Отправляем вопрос куратору
        msg = await bot.send_message(
            CURATOR_ID,
            msg_text,
            parse_mode="HTML",
            reply_markup=create_curator_keyboard(user_id, has_history)
        )

        # Сохраняем информацию для ответа
        pending_responses[msg.message_id] = {
            'user_id': user_id,
            'question': question
        }

        await message.answer("✅ Ваш вопрос отправлен куратору! Ожидайте ответа.",
                             reply_markup=get_question_keyboard())
        await state.finish()
    else:
        await message.answer("Произошла ошибка. Пожалуйста, начните снова через /start",
                             reply_markup=get_contact_keyboard())


# Обработчики для куратора
@dp.callback_query_handler(lambda c: c.data.startswith('reply_'))
async def process_reply_callback(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split('_')[1])
    await bot.answer_callback_query(callback_query.id)

    user_data = user_data_storage.get(user_id, {})

    await bot.send_message(
        callback_query.from_user.id,
        f"✍️ Напишите ответ для пользователя (не более {MAX_ANSWER_LENGTH} символов):\n\n"
        f"👤: {user_data.get('full_name', 'Неизвестно')}\n"
        f"📱: {user_data.get('username', 'Неизвестно')}\n"
        f"🆔: <code>{user_id}</code>\n\n"
        f"После отправки сообщения оно будет переслано пользователю.",
        parse_mode="HTML"
    )

    await CuratorState.waiting_for_response.set()
    await dp.current_state(user=callback_query.from_user.id).update_data(
        target_user_id=user_id
    )


@dp.callback_query_handler(lambda c: c.data.startswith('full_history_'))
async def show_full_history(callback_query: types.CallbackQuery):
    user_id = int(callback_query.data.split('_')[2])
    user_data = user_data_storage.get(user_id, {})

    if not user_data.get('questions'):
        await bot.answer_callback_query(callback_query.id, "История вопросов пуста")
        return

    # Если вопросов много (>10), отправляем файлом
    if len(user_data['questions']) > 10:
        filename = f"questions_{user_id}.txt"
        with open(filename, "w", encoding='utf-8') as f:
            f.write("\n".join([f"{i + 1}. {q}" for i, q in enumerate(user_data['questions'])]))

        await bot.send_document(
            callback_query.from_user.id,
            types.InputFile(filename),
            caption=f"📜 Полная история вопросов от {user_data['full_name']} (ID: {user_id})"
        )
        os.remove(filename)
    else:
        full_history = "\n".join([f"{i + 1}. {q}" for i, q in enumerate(user_data['questions'])])
        await bot.send_message(
            callback_query.from_user.id,
            f"📜 Полная история вопросов от {user_data['full_name']} (ID: {user_id}):\n\n{full_history}",
            parse_mode="HTML"
        )

    await bot.answer_callback_query(callback_query.id)


@dp.message_handler(state=CuratorState.waiting_for_response, content_types=types.ContentTypes.TEXT)
async def handle_curator_response(message: types.Message, state: FSMContext):
    if len(message.text) > MAX_ANSWER_LENGTH:
        await message.answer(
            f"❌ Ваш ответ слишком длинный. Пожалуйста, ограничьте ответ {MAX_ANSWER_LENGTH} символами.")
        return

    data = await state.get_data()
    user_id = data['target_user_id']

    if user_id in user_data_storage:
        try:
            await bot.send_message(
                user_id,
                f"📩 Ответ от куратора:\n\n{message.text}"
            )
            await message.answer("✅ Ответ успешно отправлен студенту!")
        except Exception as e:
            await message.answer(f"❌ Не удалось отправить ответ: {str(e)}")
    else:
        await message.answer("❌ Ошибка: пользователь не найден")

    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
