import os
import psycopg
from psycopg.rows import dict_row
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


def get_connection():
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is missing from the .env file")

    return psycopg.connect(
        DATABASE_URL,
        row_factory=dict_row
    )


def initialize_database():
    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id BIGSERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    amount DOUBLE PRECISION NOT NULL CHECK(amount > 0),
                    transaction_type TEXT NOT NULL
                        CHECK(transaction_type IN ('income', 'expense')),
                    category TEXT NOT NULL,
                    transaction_date TEXT NOT NULL
                )
            """)

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id BIGSERIAL PRIMARY KEY,
                    category TEXT NOT NULL UNIQUE,
                    monthly_limit DOUBLE PRECISION NOT NULL
                        CHECK(monthly_limit > 0)
                )
            """)

        connection.commit()

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
    print("StudentBudgetAI Neon database initialized successfully!")