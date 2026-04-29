-- ============================================================
-- ClassHelperProBot — Elections System Setup
-- Version 1.0 | Idempotent
-- ============================================================

-- Видаляємо старі типи, якщо існують (обережно з існуючими даними)
DROP TYPE IF EXISTS election_type CASCADE;

-- Типи виборів
CREATE TYPE election_type AS ENUM ('regular', 'no_confidence', 'runoff');

-- Основна таблиця виборів
CREATE TABLE IF NOT EXISTS elections (
    id              SERIAL PRIMARY KEY,
    election_type   election_type NOT NULL,
    initiator_id    INT REFERENCES students(id) ON DELETE SET NULL,
    is_active       BOOLEAN NOT NULL DEFAULT true,
    started_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    finished_at     TIMESTAMPTZ,
    round           INT NOT NULL DEFAULT 1,
    parent_id       INT REFERENCES elections(id) ON DELETE SET NULL
);

-- Індекси для швидкого пошуку активних виборів
CREATE INDEX IF NOT EXISTS idx_elections_active ON elections(is_active) WHERE is_active = true;
CREATE INDEX IF NOT EXISTS idx_elections_parent ON elections(parent_id);

-- Голоси виборців
CREATE TABLE IF NOT EXISTS election_votes (
    id              SERIAL PRIMARY KEY,
    election_id     INT NOT NULL REFERENCES elections(id) ON DELETE CASCADE,
    voter_id        INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    candidate_id    INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE(election_id, voter_id)
);

CREATE INDEX IF NOT EXISTS idx_election_votes_election ON election_votes(election_id);
CREATE INDEX IF NOT EXISTS idx_election_votes_voter ON election_votes(voter_id);

-- Збереження результатів завершених виборів
CREATE TABLE IF NOT EXISTS election_results_log (
    id              SERIAL PRIMARY KEY,
    election_id     INT NOT NULL REFERENCES elections(id) ON DELETE CASCADE,
    student_id      INT NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    place           INT NOT NULL CHECK (place >= 1),
    votes           INT NOT NULL DEFAULT 0,
    role_awarded    TEXT CHECK (role_awarded IN ('starosta', 'zamstarosta', NULL)),
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_election_results_log_election ON election_results_log(election_id);