import hashlib
import secrets
import sqlite3
from pathlib import Path
from typing import Any


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = BASE_DIR / "hrm.db"


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def clean_optional(value: str | None) -> str | None:
    if value is None:
        return None

    value = value.strip()

    return value if value else None


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000,
    ).hex()

    return f"{salt}${password_hash}"


def verify_password(password: str, stored_password: str) -> bool:
    try:
        salt, password_hash = stored_password.split("$")
    except ValueError:
        return False

    check_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        100000,
    ).hex()

    return secrets.compare_digest(check_hash, password_hash)


def initialize_database() -> None:
    with get_connection() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS employees (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                employee_code TEXT NOT NULL UNIQUE,
                name TEXT NOT NULL,
                gender TEXT,
                phone TEXT,
                email TEXT UNIQUE,
                department TEXT,
                position TEXT,
                salary REAL NOT NULL DEFAULT 0,
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT 'admin',
                status TEXT NOT NULL DEFAULT 'active',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        admin = connection.execute(
            """
            SELECT id
            FROM users
            WHERE username = ?
            """,
            ("admin",),
        ).fetchone()

        if admin is None:
            connection.execute(
                """
                INSERT INTO users (
                    name,
                    username,
                    password_hash,
                    role,
                    status
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    "Administrator",
                    "admin",
                    hash_password("admin123"),
                    "admin",
                    "active",
                ),
            )

        connection.commit()


def login_user(username: str, password: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        user = connection.execute(
            """
            SELECT *
            FROM users
            WHERE username = ?
              AND status = 'active'
            """,
            (username.strip(),),
        ).fetchone()

        if user is None:
            return None

        user_data = dict(user)

        if not verify_password(password, user_data["password_hash"]):
            return None

        user_data.pop("password_hash", None)

        return user_data


def add_employee(
    employee_code: str,
    name: str,
    gender: str | None,
    phone: str | None,
    email: str | None,
    department: str | None,
    position: str | None,
    salary: float,
) -> dict[str, Any]:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            INSERT INTO employees (
                employee_code,
                name,
                gender,
                phone,
                email,
                department,
                position,
                salary
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                employee_code.strip(),
                name.strip(),
                clean_optional(gender),
                clean_optional(phone),
                clean_optional(email),
                clean_optional(department),
                clean_optional(position),
                salary,
            ),
        )

        connection.commit()

        employee = connection.execute(
            """
            SELECT *
            FROM employees
            WHERE id = ?
            """,
            (cursor.lastrowid,),
        ).fetchone()

        return dict(employee)


def get_all_employees() -> list[dict[str, Any]]:
    with get_connection() as connection:
        employees = connection.execute(
            """
            SELECT *
            FROM employees
            ORDER BY id DESC
            """
        ).fetchall()

        return [dict(employee) for employee in employees]


def get_employee_by_id(employee_id: int) -> dict[str, Any] | None:
    with get_connection() as connection:
        employee = connection.execute(
            """
            SELECT *
            FROM employees
            WHERE id = ?
            """,
            (employee_id,),
        ).fetchone()

        return dict(employee) if employee else None


def get_employee_by_code(employee_code: str) -> dict[str, Any] | None:
    with get_connection() as connection:
        employee = connection.execute(
            """
            SELECT *
            FROM employees
            WHERE employee_code = ?
            """,
            (employee_code,),
        ).fetchone()

        return dict(employee) if employee else None


def search_employees(keyword: str) -> list[dict[str, Any]]:
    search_value = f"%{keyword.strip()}%"

    with get_connection() as connection:
        employees = connection.execute(
            """
            SELECT *
            FROM employees
            WHERE employee_code LIKE ?
               OR name LIKE ?
               OR phone LIKE ?
               OR email LIKE ?
               OR department LIKE ?
               OR position LIKE ?
            ORDER BY id DESC
            """,
            (
                search_value,
                search_value,
                search_value,
                search_value,
                search_value,
                search_value,
            ),
        ).fetchall()

        return [dict(employee) for employee in employees]


def update_employee(
    employee_id: int,
    employee_code: str,
    name: str,
    gender: str | None,
    phone: str | None,
    email: str | None,
    department: str | None,
    position: str | None,
    salary: float,
    status: str,
) -> dict[str, Any] | None:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE employees
            SET
                employee_code = ?,
                name = ?,
                gender = ?,
                phone = ?,
                email = ?,
                department = ?,
                position = ?,
                salary = ?,
                status = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (
                employee_code.strip(),
                name.strip(),
                clean_optional(gender),
                clean_optional(phone),
                clean_optional(email),
                clean_optional(department),
                clean_optional(position),
                salary,
                status,
                employee_id,
            ),
        )

        connection.commit()

        if cursor.rowcount == 0:
            return None

        employee = connection.execute(
            """
            SELECT *
            FROM employees
            WHERE id = ?
            """,
            (employee_id,),
        ).fetchone()

        return dict(employee) if employee else None


def remove_employee(employee_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            UPDATE employees
            SET
                status = 'inactive',
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (employee_id,),
        )

        connection.commit()

        return cursor.rowcount > 0


def delete_employee_permanently(employee_id: int) -> bool:
    with get_connection() as connection:
        cursor = connection.execute(
            """
            DELETE FROM employees
            WHERE id = ?
            """,
            (employee_id,),
        )

        connection.commit()

        return cursor.rowcount > 0


def get_total_payroll_budget() -> float:
    with get_connection() as connection:
        result = connection.execute(
            """
            SELECT COALESCE(SUM(salary), 0) AS total
            FROM employees
            WHERE status = 'active'
            """
        ).fetchone()

        return float(result["total"])
