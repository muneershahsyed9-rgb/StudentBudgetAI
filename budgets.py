from database import get_connection


def save_budget(category, monthly_limit):
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO budgets (category, monthly_limit)
                VALUES (%s, %s)
                ON CONFLICT(category)
                DO UPDATE SET monthly_limit = EXCLUDED.monthly_limit
                """,
                (category, monthly_limit)
            )

        connection.commit()

    finally:
        connection.close()


def get_budgets():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT * FROM budgets ORDER BY category")
            budgets = cursor.fetchall()

        return budgets

    finally:
        connection.close()