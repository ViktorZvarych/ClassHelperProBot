# ClassHelperProBot

A Telegram bot designed to assist with class management and student support.

## Features

- Student enrollment and tracking
- Class schedule management
- Assignment notifications
- Q&A support
- Grade tracking

## Installation

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up your Telegram bot token in `.env`
4. Run the bot: `python main.py`

## Usage

Start the bot with `/start` command in Telegram and follow the prompts.

## Requirements

- Python 3.8+
- python-telegram-bot library
- python-dotenv

## Configuration

Create a `.env` file with:

```
TELEGRAM_BOT_TOKEN=your_token_here
```

1. Telegram: BOT_TOKEN (від @BotFather)
Як отримати:

Відкрийте Telegram і знайдіть бота @BotFather. Це офіційний сервіс для керування ботами.
Розпочніть діалог і надішліть команду /newbot.
Дотримуйтесь інструкцій: спочатку введіть ім'я вашого бота (як воно буде відображатися), а потім юзернейм, який обов'язково має закінчуватися на bot (наприклад, ClassHelperProBot).
Після цього BotFather надішле повідомлення з вашим унікальним токеном. Він виглядає приблизно так: 1234567890:ABCDefghIJKLMNOPQRSTUVWXyz.

2. База даних: DATABASE_URL (від Supabase)
Як отримати:

Створіть проєкт на Supabase. Це буде безкоштовною хмарною базою даних для вашого бота.
Створіть підключення. Вам потрібно Connection string. Вам потрібен рядок URI з портом 5432 (Direct connection). Скопіюйте його.
Важливо: У скопійованому рядку замініть [YOUR-PASSWORD] на пароль, який ви встановили під час створення проєкту Supabase. Ось приклад готового рядка:
text
postgresql://postgres:ВАШ_ПАРОЛЬ@db.XXXXXXXXXXXX.supabase.co:5432/postgres

3. Сховище станів: REDIS_URL (від Redis Cloud або Upstash)
Як отримати:

Зареєструйте безкоштовний акаунт на Redis Cloud або Upstash (Upstash часто простіший для старту).
Після реєстрації створіть нову базу даних, обравши безкоштовний план.
Після створення бази даних вам буде надано публічну адресу (endpoint), порт та пароль.
Сформуйте з них URL-адресу для змінної REDIS_URL. Вона має виглядати так:
text
redis://default:ВАШ_ПАРОЛЬ@адреса-вашої-бд.redis-cloud.com:порт
Де адреса-вашої-бд виглядає як redis-12345.c123.us-east-1-2.ec2.redns.redis-cloud.com.

4. Хостинг: RENDER_EXTERNAL_URL (від Render)
Як отримати:

Зареєструйтесь на Render і створіть новий Web Service.
Підключіть ваш GitHub-репозиторій з кодом бота.
Важливо: Не заповнюйте цю змінну зараз! Вам потрібно спочатку задеплоїти бота. Після успішного деплою Render автоматично надасть вашому сервісу публічну URL-адресу, яка закінчується на .onrender.com. Скопіюйте її з інформаційної панелі вашого сервісу. Наприклад: https://classhelperprobot.onrender.com.

5. ID та токени для безпеки
CRON_SECRET_TOKEN:

Як отримати: Це довільний, дуже складний набір символів. Найкраще згенерувати його за допомогою менеджера паролів або онлайн-генератора паролів. Довжина має бути не менше 32 символів.

GROUP_CHAT_ID:

Як отримати: Є два способи отримати ID вашої групи (він завжди від'ємний і починається з -100).

Спосіб 1 (найпростіший): Додайте в групу бота @getmyid_bot. Після додавання він одразу надішле ID групи.
Спосіб 2 (ручний):
Зробіть вашу групу публічною.
Додайте вашого бота ClassHelperProBot до цієї групи та надішліть будь-яке повідомлення.
Клацніть правою кнопкою миші по цьому повідомленню та оберіть "Copy Message Link". Ви отримаєте посилання виду https://t.me/c/194XXXX987/11.
Число 194XXXX987 — це і є ID вашої групи без префікса. Ваша змінна GROUP_CHAT_ID має виглядати так: -100194XXXX987.
SUPER_ADMIN_IDS:

Як отримати: Це ваш особистий Telegram ID.

Відкрийте бота @getmyid_bot у Telegram.
Натисніть /start. Він одразу надішле вам ваш числовий ID.
Скопіюйте це число (наприклад, 123456789). Ви можете вказати кілька ID через кому.

6. Час та моніторинг
TIMEZONE: Встановіть значення Europe/Kyiv. Це вже вказано у вашому шаблоні.

SENTRY_DSN (Опціонально):

Як отримати: Якщо ви хочете відстежувати помилки бота, зареєструйтесь на Sentry.io і створіть новий проєкт для Python. На етапі налаштування ви отримаєте ваш унікальний DSN-рядок. Якщо моніторинг не потрібен, залиште це поле порожнім.
