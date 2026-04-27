# Алгоритм розрахунку чергових

async def calculate_duty_students_with_lock(target_date, pool):
    # Використовується в ранковому cron з блокуванням рядків
    async with pool.acquire() as conn:
        async with conn.transaction(isolation='repeatable_read'):
            step1 = await conn.fetch("""
                SELECT id FROM students
                WHERE is_active = true
                  AND role != 'guest'
                  AND NOT EXISTS (SELECT 1 FROM absence_log WHERE student_id=students.id AND absent_date=$1 AND is_cancelled=false)
                  AND (last_duty_date IS NULL OR last_duty_date < $1 - INTERVAL '1 day')
                ORDER BY consecutive_duty_skip DESC, last_duty_date ASC NULLS FIRST, id ASC
                LIMIT 3
                FOR UPDATE
            """, target_date)
            step1_ids = [r['id'] for r in step1]
            if len(step1_ids) < 3:
                step2 = await conn.fetch("""
                    SELECT id FROM students
                    WHERE is_active = true
                      AND NOT EXISTS (SELECT 1 FROM absence_log WHERE student_id=students.id AND absent_date=$1 AND is_cancelled=false)
                      AND id != ALL($2::int[])
                    ORDER BY consecutive_duty_skip DESC, last_duty_date ASC NULLS FIRST, id ASC
                    LIMIT $3
                    FOR UPDATE
                """, target_date, step1_ids, 3 - len(step1_ids))
                step2_ids = [r['id'] for r in step2]
            else:
                step2_ids = []
            final_ids = step1_ids + step2_ids
            return final_ids