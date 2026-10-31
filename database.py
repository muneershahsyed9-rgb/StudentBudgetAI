
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

            # User accounts
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id BIGSERIAL PRIMARY KEY,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    password_salt TEXT NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # User login sessions
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id BIGSERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    token_hash TEXT NOT NULL UNIQUE,
                    expires_at TIMESTAMPTZ NOT NULL,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS sessions_user_id_idx
                ON sessions(user_id)
            """)

            # Transactions
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

            # Add ownership to existing transaction records.
            # Existing records remain unassigned.
            cursor.execute("""
                ALTER TABLE transactions
                ADD COLUMN IF NOT EXISTS user_id BIGINT
                REFERENCES users(id)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS transactions_user_id_idx
                ON transactions(user_id)
            """)

            # Budgets
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS budgets (
                    id BIGSERIAL PRIMARY KEY,
                    category TEXT NOT NULL,
                    monthly_limit DOUBLE PRECISION NOT NULL
                        CHECK(monthly_limit > 0)
                )
            """)

            # Add ownership to existing budget records.
            # Existing records remain unassigned.
            cursor.execute("""
                ALTER TABLE budgets
                ADD COLUMN IF NOT EXISTS user_id BIGINT
                REFERENCES users(id)
            """)

            # Remove the old global category uniqueness rule.
            cursor.execute("""
                ALTER TABLE budgets
                DROP CONSTRAINT IF EXISTS budgets_category_key
            """)

            # Each user can have their own budget for each category.
            cursor.execute("""
                CREATE UNIQUE INDEX IF NOT EXISTS budgets_user_category_idx
                ON budgets(user_id, category)
            """)

            cursor.execute("""
                CREATE INDEX IF NOT EXISTS budgets_user_id_idx
                ON budgets(user_id)
            """)

        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


if __name__ == "__main__":
    initialize_database()
    print("StudentBudgetAI database initialized successfully!")
