
# Телеграм-бот поддержки

Это телеграм-бот, предназначенный для управления вопросами и ответами между студентами и кураторами во время мероприятия (например, олимпиады или конкурса). Он позволяет студентам задавать вопросы, а кураторам — отвечать на них. Бот также собирает контактные данные студентов для удобного общения.

## Возможности

- **Для студентов:**
  - Задавать вопросы куратору.
  - Возможность задать новый вопрос.
  - Предоставить контактные данные для связи.
  
- **Для кураторов:**
  - Отвечать на вопросы студентов.
  - Просматривать полную историю вопросов от конкретного студента.
  - Просматривать историю вопросов от каждого студента.
  - Отправлять ответы обратно студентам.

## Требования

- Python 3.x
- Библиотеки:
  - `aiogram` — Асинхронный фреймворк для телеграм-ботов.
  - `python-dotenv` — Для загрузки переменных окружения из файла `.env`.

Для установки всех зависимостей, выполните команду:

```bash
pip install -r requirements.txt
```

## Настройка

### 1. Создайте файл `.env`

Создайте файл `.env` в корне проекта и добавьте следующие переменные окружения:

```plaintext
API_TOKEN=ваш_токен_бота_телеграм
CURATOR_ID=ваш_telegram_id_куратора
```

Замените `ваш_токен_бота_телеграм` на API токен, который вы получили от [BotFather](https://core.telegram.org/bots#botfather), а `ваш_telegram_id_куратора` — на Telegram ID куратора.

### 2. Установите зависимости

Запустите следующую команду для установки всех необходимых зависимостей:

```bash
pip install -r requirements.txt
```

### 3. Запустите бота

Запустите скрипт `main.py`, чтобы запустить бота:

```bash
python main.py
```

Бот начнет опрашивать обновления и сообщения.

### 4. Игнорирование Git

Не забудьте добавить файл `.env` в ваш `.gitignore`, чтобы избежать публикации конфиденциальной информации в вашем репозитории.

```plaintext
.env
```

## Структура проекта

- **`main.py`**: Основная логика бота, обработка взаимодействий с пользователями и управление состояниями.
- **`.env`**: Содержит конфиденциальные переменные окружения, такие как токен бота и ID куратора.
- **`requirements.txt`**: Список зависимостей, необходимых для работы проекта.

## Ошибки и их решение

- **Ошибка: `ModuleNotFoundError: No module named 'aiogram.contrib'`**
  - Модуль `aiogram.contrib` был устаревшим. Убедитесь, что вы используете правильную версию `aiogram`. Если вы используете `aiogram` версии 3.x, замените импорт `from aiogram.contrib.fsm_storage.memory import MemoryStorage` на `from aiogram.fsm.storage.memory import MemoryStorage`.

- **Ошибка: `ModuleNotFoundError: No module named 'python-dotenv'`**
  - Установите `python-dotenv`, выполнив команду:
  
    ```bash
    pip install python-dotenv
    ```

## Лицензия

Этот проект лицензирован на условиях MIT License — подробности смотрите в файле [LICENSE](LICENSE).
