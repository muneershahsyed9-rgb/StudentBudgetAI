
import hashlib
import hmac
import re
import secrets
from datetime import datetime, timedelta, timezone

from database import get_connection


SESSION_DAYS = 7
PBKDF2_ITERATIONS = 600_000


def hash_password(password, salt=None):
    if salt is None:
        salt = secrets.token_bytes(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        PBKDF2_ITERATIONS
    )

    return password_hash.hex(), salt.hex()


def validate_username(username):
    return bool(re.fullmatch(r"[A-Za-z0-9_]{3,30}", username))


def register_user(username, password):
    username = username.strip().lower()

    if not validate_username(username):
        return False, "Username must be 3–30 characters using letters, numbers, or underscores."

    if len(password) < 10 or len(password) > 128:
        return False, "Password must be between 10 and 128 characters."

    password_hash, password_salt = hash_password(password)

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO users (username, password_hash, password_salt)
                VALUES (%s, %s, %s)
                RETURNING id, username
                """,
                (username, password_hash, password_salt)
            )
            user = cursor.fetchone()

        connection.commit()
        return True, dict(user)

    except Exception as error:
        connection.rollback()

        if getattr(error, "sqlstate", None) == "23505":
            return False, "That username is already taken."

        raise

    finally:
        connection.close()


def authenticate_user(username, password):
    username = username.strip().lower()

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, username, password_hash, password_salt
                FROM users
                WHERE username = %s
                """,
                (username,)
            )
            user = cursor.fetchone()

        if user is None:
            return None

        calculated_hash, _ = hash_password(
            password,
            bytes.fromhex(user["password_salt"])
        )

        if not hmac.compare_digest(
            calculated_hash,
            user["password_hash"]
        ):
            return None

        return {
            "id": user["id"],
            "username": user["username"]
        }

    finally:
        connection.close()


def create_session(user_id):
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()
    expires_at = datetime.now(timezone.utc) + timedelta(days=SESSION_DAYS)

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO sessions (user_id, token_hash, expires_at)
                VALUES (%s, %s, %s)
                """,
                (user_id, token_hash, expires_at)
            )

        connection.commit()
        return token

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def get_user_from_session(token):
    if not token:
        return None

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT u.id, u.username
                FROM sessions s
                JOIN users u ON u.id = s.user_id
                WHERE s.token_hash = %s
                  AND s.expires_at > CURRENT_TIMESTAMP
                """,
                (token_hash,)
            )
            user = cursor.fetchone()

        return dict(user) if user else None

    finally:
        connection.close()


def delete_session(token):
    if not token:
        return

    token_hash = hashlib.sha256(token.encode("utf-8")).hexdigest()

    connection = get_connection()

    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "DELETE FROM sessions WHERE token_hash = %s",
                (token_hash,)
            )

        connection.commit()

    finally:
        connection.close()
