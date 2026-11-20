
import sqlite3
from datetime import date, timedelta

from database import get_connection

BORROWING_DAYS = 14
MAX_BOOKS = 3
FINE_PER_DAY = 5


def borrow_book(user_id, book_id):
    today = date.today()
    borrow_date = today.isoformat()
    due_date = (today + timedelta(days=BORROWING_DAYS)).isoformat()

    conn = get_connection()

    try:
        conn.execute("BEGIN IMMEDIATE")

        book = conn.execute(
            "SELECT * FROM books WHERE id = ?",
            (book_id,)
        ).fetchone()

        if not book:
            conn.rollback()
            return False, "Book not found."

        if book["available_copies"] <= 0:
            conn.rollback()
            return False, "No copies are currently available."

        active = conn.execute("""
            SELECT COUNT(*) FROM borrowings
            WHERE user_id = ? AND status = 'Borrowed'
        """, (user_id,)).fetchone()[0]

        if active >= MAX_BOOKS:
            conn.rollback()
            return False, "You have reached the maximum limit of 3 books."

        existing = conn.execute("""
            SELECT id FROM borrowings
            WHERE user_id = ? AND book_id = ? AND status = 'Borrowed'
        """, (user_id, book_id)).fetchone()

        if existing:
            conn.rollback()
            return False, "You have already borrowed this book."

        conn.execute("""
            INSERT INTO borrowings
            (user_id, book_id, borrow_date, due_date, status)
            VALUES (?, ?, ?, ?, 'Borrowed')
        """, (user_id, book_id, borrow_date, due_date))

        conn.execute("""
            UPDATE books
            SET available_copies = available_copies - 1
            WHERE id = ?
        """, (book_id,))

        conn.commit()
        return True, f"Book borrowed successfully! Return by {due_date}."

    except Exception as error:
        conn.rollback()
        return False, f"Borrowing failed: {error}"

    finally:
        conn.close()


def return_book(borrowing_id):
    today = date.today()
    conn = get_connection()

    try:
        conn.execute("BEGIN IMMEDIATE")

        record = conn.execute("""
            SELECT * FROM borrowings
            WHERE id = ? AND status = 'Borrowed'
        """, (borrowing_id,)).fetchone()

        if not record:
            conn.rollback()
            return False, "Active borrowing record not found."

        due_date = date.fromisoformat(record["due_date"])
        late_days = max(0, (today - due_date).days)
        fine = late_days * FINE_PER_DAY

        conn.execute("""
            UPDATE borrowings
            SET return_date = ?, fine = ?, status = 'Returned'
            WHERE id = ?
        """, (today.isoformat(), fine, borrowing_id))

        conn.execute("""
            UPDATE books
            SET available_copies = available_copies + 1
            WHERE id = ?
        """, (record["book_id"],))

        conn.commit()

        if fine > 0:
            return True, f"Book returned. Late by {late_days} days. Fine: Rs. {fine}."

        return True, "Book returned successfully. No fine."

    except Exception as error:
        conn.rollback()
        return False, f"Return failed: {error}"

    finally:
        conn.close()


def get_user_borrowings(user_id):
    with get_connection() as conn:
        return conn.execute("""
            SELECT
                borrowings.*,
                books.title,
                books.author,
                books.category
            FROM borrowings
            JOIN books ON books.id = borrowings.book_id
            WHERE borrowings.user_id = ?
            ORDER BY borrowings.id DESC
        """, (user_id,)).fetchall()


def get_all_borrowings():
    with get_connection() as conn:
        return conn.execute("""
            SELECT
                borrowings.*,
                books.title,
                books.author,
                users.name AS student_name,
                users.student_id
            FROM borrowings
            JOIN books ON books.id = borrowings.book_id
            JOIN users ON users.id = borrowings.user_id
            ORDER BY borrowings.id DESC
        """).fetchall()
