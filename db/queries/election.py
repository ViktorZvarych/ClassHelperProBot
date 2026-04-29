async def get_active_election(conn):
    """Отримати активне голосування, якщо є."""
    row = await conn.fetchrow(
        """
        SELECT id, election_type, initiator_id, is_active, started_at, round, parent_id
        FROM elections
        WHERE is_active = true
        ORDER BY started_at DESC
        LIMIT 1
        """
    )
    return dict(row) if row else None

async def create_election(conn, election_type, initiator_id=None, parent_id=None, round=1):
    """Створити нове голосування."""
    return await conn.fetchval(
        """
        INSERT INTO elections (election_type, initiator_id, is_active, parent_id, round)
        VALUES ($1, $2, true, $3, $4)
        RETURNING id
        """,
        election_type, initiator_id, parent_id, round
    )

async def finish_election(conn, election_id):
    """Завершити голосування."""
    await conn.execute(
        """
        UPDATE elections
        SET is_active = false, finished_at = now()
        WHERE id = $1
        """,
        election_id
    )

async def cast_vote(conn, election_id, voter_id, candidate_id):
    """Віддати голос (INSERT ... ON CONFLICT DO NOTHING для унікальності)."""
    result = await conn.fetchval(
        """
        INSERT INTO election_votes (election_id, voter_id, candidate_id)
        VALUES ($1, $2, $3)
        ON CONFLICT (election_id, voter_id) DO NOTHING
        RETURNING id
        """,
        election_id, voter_id, candidate_id
    )
    return result is not None

async def has_voted(conn, election_id, voter_id):
    """Перевірити, чи проголосував виборець."""
    row = await conn.fetchrow(
        "SELECT id FROM election_votes WHERE election_id = $1 AND voter_id = $2",
        election_id, voter_id
    )
    return row is not None

async def get_election_results(conn, election_id):
    """Отримати результати виборів (кількість голосів за кожного кандидата)."""
    rows = await conn.fetch(
        """
        SELECT candidate_id, COUNT(*) as votes
        FROM election_votes
        WHERE election_id = $1
        GROUP BY candidate_id
        ORDER BY votes DESC
        """,
        election_id
    )
    return [dict(r) for r in rows]

async def get_non_voters(conn, election_id):
    """Отримати список студентів, які ще не проголосували."""
    rows = await conn.fetch(
        """
        SELECT s.id, s.telegram_id, s.full_name
        FROM students s
        WHERE s.is_active = true
          AND s.role != 'guest'
          AND s.telegram_id IS NOT NULL
          AND s.id NOT IN (
              SELECT voter_id FROM election_votes WHERE election_id = $1
          )
        """,
        election_id
    )
    return [dict(r) for r in rows]

async def get_candidates_by_ids(conn, candidate_ids):
    """Отримати список кандидатів за ID."""
    if not candidate_ids:
        return []
    rows = await conn.fetch(
        "SELECT id, full_name FROM students WHERE id = ANY($1::int[])",
        candidate_ids
    )
    return [dict(r) for r in rows]

async def set_student_role(conn, student_id, role):
    """Встановити роль студента."""
    await conn.execute(
        "UPDATE students SET role = $1, updated_at = now() WHERE id = $2",
        role, student_id
    )

async def reset_old_leadership(conn):
    """Скинути ролі старости та замстарости."""
    await conn.execute(
        "UPDATE students SET role = 'student', updated_at = now() WHERE role IN ('starosta', 'zamstarosta')"
    )

async def log_election_results(conn, election_id, results):
    """Записати підсумкові результати виборів."""
    for place, result in enumerate(results, start=1):
        await conn.execute(
            """
            INSERT INTO election_results_log (election_id, student_id, place, votes, role_awarded)
            VALUES ($1, $2, $3, $4, $5)
            """,
            election_id, result["candidate_id"], place, result["votes"], result.get("role_awarded")
        )

async def get_last_completed_election(conn):
    """Отримати останні завершені регулярні вибори."""
    row = await conn.fetchrow(
        """
        SELECT id FROM elections
        WHERE election_type = 'regular' AND is_active = false
        ORDER BY finished_at DESC
        LIMIT 1
        """
    )
    return dict(row) if row else None

async def get_election_results_by_place(conn, election_id, place):
    """Отримати кандидатів, які зайняли певне місце (може бути декілька)."""
    rows = await conn.fetch(
        """
        WITH ranked AS (
            SELECT candidate_id, COUNT(*) as votes,
                   RANK() OVER (ORDER BY COUNT(*) DESC) as place
            FROM election_votes
            WHERE election_id = $1
            GROUP BY candidate_id
        )
        SELECT candidate_id, votes FROM ranked WHERE place = $2
        """,
        election_id, place
    )
    return [dict(r) for r in rows]