
from database import get_connection


def save_budget(user_id, category, monthly_limit):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO budgets (user_id, category, monthly_limit)
                VALUES (%s, %s, %s)
                ON CONFLICT (user_id, category)
                DO UPDATE SET monthly_limit = EXCLUDED.monthly_limit
                """,
                (user_id, category, monthly_limit)
            )

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_budgets(user_id):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, category, monthly_limit
                FROM budgets
                WHERE user_id = %s
                ORDER BY category
                """,
                (user_id,)
            )
            budgets = cursor.fetchall()

        return budgets

    finally:
        connection.close()
