
from database import get_connection


def save_budget(category, monthly_limit):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        """
        INSERT INTO budgets (category, monthly_limit)
        VALUES (?, ?)
        ON CONFLICT(category)
        DO UPDATE SET monthly_limit = excluded.monthly_limit
        """,
        (category, monthly_limit)
    )

    connection.commit()
    connection.close()


def get_budgets():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM budgets ORDER BY category")
    budgets = [dict(row) for row in cursor.fetchall()]

    connection.close()
    return budgets
