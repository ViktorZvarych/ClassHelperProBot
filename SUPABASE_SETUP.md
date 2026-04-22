# Інструкція для адміна Supabase

#### Крок 1. Створення проєкту Supabase

1. Зайдіть на [supabase.com](https://supabase.com) → «New Project».
2. Введіть назву проєкту (наприклад, `classhelperprobot`).
3. Виберіть регіон, найближчий до України: **Frankfurt (eu-central-1)**.
4. Встановіть надійний пароль для бази даних (збережіть в менеджері паролів).
5. Натисніть «Create new project» і дочекайтесь ініціалізації (~2 хвилини).

#### Крок 2. Отримання DATABASE_URL

1. Перейдіть: **Settings → Database**.
2. У розділі «Connection string» виберіть тип **URI**.
3. Скопіюйте рядок виду: `postgresql://postgres:[PASSWORD]@db.[REF].supabase.co:5432/postgres`
4. Замініть `[PASSWORD]` на пароль, встановлений у кроці 1.
5. Збережіть як змінну `DATABASE_URL` у `.env` і на Render.

#### Крок 3. Виконання міграції

1. Перейдіть: **SQL Editor → New query**.
2. Відкрийте файл `migrations/001_init_db.sql` з репозиторію.
3. Скопіюйте весь вміст у SQL Editor.
4. Натисніть **Run** (або `Ctrl+Enter`).
5. Переконайтеся, що виконання завершилось без помилок (знизу з'явиться `Success`).
6. Перейдіть у **Table Editor** і перевірте, що всі таблиці створені: `students`, `absence_log`, `subjects`, `timetable`, `homework`, `duty_log`, `duty_log_archive`, `holidays`, `bot_messages`, `week_config`, `cron_runs`, `class_info`, `failed_jobs`.

#### Крок 4. Налаштування розкладу

1. Перейдіть: **Table Editor → `timetable`**.
2. Натисніть **Insert row** для кожного уроку.
3. Значення полів:
   - `day_of_week`: 0 = Пн, 1 = Вт, 2 = Ср, 3 = Чт, 4 = Пт.
   - `lesson_num`: номер уроку в розкладі (1, 2, 3...).
   - `subject_id`: ID предмета з таблиці `subjects`.
   - `cabinet`: рядок (наприклад, `"310"`) або порожньо.
   - `teacher`: прізвище та ім'я вчителя або порожньо.
   - `week_type`: `'numerator'` (чисельник), `'denominator'` (знаменник), або `'both'` (обидва).
   - `group_name`: `'all'`, `'A'`, або `'B'`.

**Приклад:** математика у вівторок (lesson 1), для всіх, обидва тижні, каб. 204:
```sql
INSERT INTO timetable (day_of_week, lesson_num, subject_id, cabinet, week_type, group_name)
SELECT 1, 1, id, '204', 'both', 'all' FROM subjects WHERE name = 'Математика';
