# Ідемпотентний скрипт ініціалізації БД
-- ============================================================
-- ClassHelperProBot — Initial Database Setup
-- Version 9.0 | Idempotent
-- ============================================================

-- ─────────── ТАБЛИЦІ ───────────

CREATE TABLE IF NOT EXISTS students (
    id                    SERIAL PRIMARY KEY,
    full_name             TEXT NOT NULL,
    telegram_id           BIGINT NULL UNIQUE,
    role                  TEXT NOT NULL DEFAULT 'student'
                              CHECK (role IN ('student','starosta','zamstarosta','redactor')),
    group_name            TEXT NOT NULL DEFAULT 'all'
                              CHECK (group_name IN ('A', 'B', 'all')),
    is_active             BOOLEAN NOT NULL DEFAULT true,
    absent_date           DATE NULL,
    last_duty_date        DATE NULL,
    consecutive_duty_skip INT NOT NULL DEFAULT 0,
    created_at            TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at            TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS absence_log (
    id           SERIAL PRIMARY KEY,
    student_id   INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    absent_date  DATE NOT NULL,
    is_cancelled BOOLEAN NOT NULL DEFAULT false,
    created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(student_id, absent_date)
);

CREATE TABLE IF NOT EXISTS subjects (
    id   SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS timetable (
    id          SERIAL PRIMARY KEY,
    day_of_week INT NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    lesson_num  INT NOT NULL CHECK (lesson_num BETWEEN 1 AND 12),
    subject_id  INT REFERENCES subjects(id) ON DELETE SET NULL,
    cabinet     TEXT,
    teacher     TEXT,
    week_type   TEXT NOT NULL
                    CHECK (week_type IN ('numerator', 'denominator', 'both')),
    group_name  TEXT NOT NULL
                    CHECK (group_name IN ('A', 'B', 'all')),
    UNIQUE(day_of_week, lesson_num, week_type, group_name)
);

CREATE TABLE IF NOT EXISTS homework (
    id          SERIAL PRIMARY KEY,
    subject_id  INT REFERENCES subjects(id) ON DELETE SET NULL,
    due_date    DATE NOT NULL,
    description TEXT NOT NULL CHECK (length(description) BETWEEN 1 AND 500),
    is_control  BOOLEAN NOT NULL DEFAULT false,
    is_active   BOOLEAN NOT NULL DEFAULT true,
    added_by    BIGINT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS duty_log (
    id              SERIAL PRIMARY KEY,
    duty_date       DATE NOT NULL,
    student_id      INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    status          TEXT NOT NULL
                        CHECK (status IN ('pending', 'completed', 'replaced', 'absent')),
    replaced_by_id  INT NULL REFERENCES students(id) ON DELETE SET NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(duty_date, student_id),
    CONSTRAINT duty_log_replaced_check CHECK (
        (status = 'replaced' AND replaced_by_id IS NOT NULL AND replaced_by_id != student_id)
        OR (status != 'replaced' AND replaced_by_id IS NULL)
    ),
    CONSTRAINT duty_log_completed_check CHECK (
        status != 'completed' OR replaced_by_id IS NULL
    )
);

CREATE TABLE IF NOT EXISTS duty_log_archive (
    id              INT NOT NULL,
    duty_date       DATE NOT NULL,
    student_id      INT NOT NULL,
    status          TEXT NOT NULL,
    replaced_by_id  INT NULL,
    created_at      TIMESTAMPTZ NOT NULL,
    updated_at      TIMESTAMPTZ NOT NULL,
    archived_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS holidays (
    id          SERIAL PRIMARY KEY,
    start_date  DATE NOT NULL,
    end_date    DATE NOT NULL,
    description TEXT,
    CHECK (end_date >= start_date)
);

CREATE TABLE IF NOT EXISTS bot_messages (
    id              SERIAL PRIMARY KEY,
    chat_id         BIGINT NOT NULL,
    message_id      INT NOT NULL,
    type            TEXT NOT NULL,
    duty_date       DATE NOT NULL,
    evening_payload JSONB NOT NULL,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(chat_id, type, duty_date)
);

CREATE TABLE IF NOT EXISTS week_config (
    id              INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    semester_start  DATE NOT NULL,
    first_week_type TEXT NOT NULL
                        CHECK (first_week_type IN ('numerator', 'denominator')),
    is_active       BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS cron_runs (
    id        SERIAL PRIMARY KEY,
    endpoint  TEXT NOT NULL,
    run_date  DATE NOT NULL,
    ran_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(endpoint, run_date)
);

CREATE TABLE IF NOT EXISTS class_info (
    id                  INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    class_number        INT NOT NULL CHECK (class_number BETWEEN 1 AND 11),
    class_letter        TEXT NOT NULL CHECK (length(class_letter) BETWEEN 1 AND 2),
    academic_year_start DATE NOT NULL,
    is_current          BOOLEAN NOT NULL DEFAULT true
);

CREATE TABLE IF NOT EXISTS failed_jobs (
    id          SERIAL PRIMARY KEY,
    job_type    TEXT NOT NULL,
    payload     JSONB,
    error       TEXT NOT NULL,
    attempts    INT NOT NULL DEFAULT 1,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- ─────────── ІНДЕКСИ ───────────

CREATE INDEX IF NOT EXISTS idx_students_telegram_id    ON students(telegram_id);
CREATE INDEX IF NOT EXISTS idx_students_is_active      ON students(is_active);

CREATE UNIQUE INDEX IF NOT EXISTS one_starosta
    ON students(role)
    WHERE role = 'starosta' AND is_active = true;

CREATE INDEX IF NOT EXISTS idx_absence_active
    ON absence_log(student_id, absent_date)
    WHERE is_cancelled = false;

CREATE INDEX IF NOT EXISTS idx_absence_log_absent_date
    ON absence_log(absent_date)
    WHERE is_cancelled = false;

CREATE INDEX IF NOT EXISTS idx_absence_log_student_id  ON absence_log(student_id);

CREATE INDEX IF NOT EXISTS idx_timetable_day_week_group
    ON timetable(day_of_week, week_type, group_name);

CREATE INDEX IF NOT EXISTS idx_homework_due_date
    ON homework(due_date)
    WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_homework_subject_due
    ON homework(subject_id, due_date)
    WHERE is_active = true;

CREATE INDEX IF NOT EXISTS idx_duty_log_duty_date      ON duty_log(duty_date);
CREATE INDEX IF NOT EXISTS idx_duty_log_student_id     ON duty_log(student_id);

CREATE INDEX IF NOT EXISTS idx_duty_log_replaced_by_id
    ON duty_log(replaced_by_id)
    WHERE replaced_by_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_duty_log_archive_duty_date
    ON duty_log_archive(duty_date);

CREATE INDEX IF NOT EXISTS idx_duty_log_archive_student_id
    ON duty_log_archive(student_id);

CREATE INDEX IF NOT EXISTS idx_holidays_dates          ON holidays(start_date, end_date);

-- ─────────── ТРИГЕР ───────────

CREATE OR REPLACE FUNCTION sync_absent_cache()
RETURNS TRIGGER AS $$
BEGIN
  IF TG_OP = 'DELETE' THEN
    UPDATE students
    SET absent_date = NULL, updated_at = now()
    WHERE id = OLD.student_id
      AND absent_date = OLD.absent_date;
    RETURN OLD;
  END IF;

  IF NEW.is_cancelled = false THEN
    UPDATE students
    SET absent_date = NEW.absent_date, updated_at = now()
    WHERE id = NEW.student_id;
  ELSE
    UPDATE students
    SET absent_date = NULL, updated_at = now()
    WHERE id = NEW.student_id
      AND absent_date = NEW.absent_date;
  END IF;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_sync_absent_cache ON absence_log;

CREATE TRIGGER trg_sync_absent_cache
AFTER INSERT OR UPDATE OR DELETE ON absence_log
FOR EACH ROW EXECUTE FUNCTION sync_absent_cache();

-- ─────────── ПОЧАТКОВІ ДАНІ ───────────

-- Початкова конфігурація класу (змінити перед запуском!)
INSERT INTO class_info (id, class_number, class_letter, academic_year_start)
VALUES (1, 7, 'А', '2025-09-01')
ON CONFLICT (id) DO NOTHING;

-- Початкова конфігурація тижнів (змінити semester_start і first_week_type!)
INSERT INTO week_config (id, semester_start, first_week_type, is_active)
VALUES (1, '2026-01-13', 'numerator', true)
ON CONFLICT (id) DO NOTHING;

-- ─────────── ПРЕДМЕТИ (ПРИКЛАД — замінити на реальні!) ───────────

INSERT INTO subjects (name) VALUES
    ('Алгебра'),
    ('Англійська мова'),
    ('Біологія'),
    ('Всесвітня історія'),
    ('Географія'),
    ('Геометрія'),
    ('Громадянська освіта'),
    ('Зарубіжна література'),
    ('ЗБД'),
    ('Інформатика'),
    ('Історія України'),
    ('Музичне мистецтво'),
    ('Образотворче мистецтво'),
    ('Основи медіаграмотності'),
    ('Трудове навчанн'),
    ('Художня праця'),
    ('Українська література'),
    ('Українська мова'),
    ('Фізика'),
    ('Фізична культура'),
    ('Хімія')
ON CONFLICT (name) DO NOTHING;