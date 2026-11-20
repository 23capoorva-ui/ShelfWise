
from datetime import date
from database import get_connection


# 1. Reserve a book
def reserve_book(user_id, book_id):
    conn = get_connection()

    try:
        conn.execute("BEGIN IMMEDIATE")

        book = conn.execute("""
            SELECT id, available_copies
            FROM books
            WHERE id = ?
        """, (book_id,)).fetchone()

        if not book:
            conn.rollback()
            return False, "Book not found."

        existing = conn.execute("""
            SELECT id FROM reservations
            WHERE user_id = ?
            AND book_id = ?
            AND status IN ('Waiting', 'Ready')
        """, (user_id, book_id)).fetchone()

        if existing:
            conn.rollback()
            return False, "You already reserved this book."

        active_count = conn.execute("""
            SELECT COUNT(*) FROM reservations
            WHERE user_id = ?
            AND status IN ('Waiting', 'Ready')
        """, (user_id,)).fetchone()[0]

        if active_count >= 3:
            conn.rollback()
            return False, "Maximum 3 active reservations allowed."

        if book["available_copies"] > 0:
            conn.rollback()
            return False, "This book is available. You can borrow it directly."

        conn.execute("""
            INSERT INTO reservations (
                user_id,
                book_id,
                reservation_date,
                status
            )
            VALUES (?, ?, ?, 'Waiting')
        """, (
            user_id,
            book_id,
            date.today().isoformat()
        ))

        conn.commit()
        return True, "Reservation created successfully."

    except Exception as error:
        conn.rollback()
        return False, f"Reservation failed: {error}"

    finally:
        conn.close()


# 2. Get reservations of a student
def get_user_reservations(user_id):
    with get_connection() as conn:
        return conn.execute("""
            SELECT
                reservations.*,
                books.title,
                books.author,
                books.category
            FROM reservations
            JOIN books
                ON books.id = reservations.book_id
            WHERE reservations.user_id = ?
            ORDER BY reservations.id DESC
        """, (user_id,)).fetchall()


# 3. Get all reservations for admin
def get_all_reservations():
    with get_connection() as conn:
        return conn.execute("""
            SELECT
                reservations.*,
                books.title,
                books.author,
                users.name AS student_name,
                users.student_id
            FROM reservations
            JOIN books
                ON books.id = reservations.book_id
            JOIN users
                ON users.id = reservations.user_id
            ORDER BY reservations.reservation_date ASC,
                     reservations.id ASC
        """).fetchall()


# 4. Cancel a reservation
def cancel_reservation(reservation_id, user_id=None):
    conn = get_connection()

    try:
        if user_id is None:
            cursor = conn.execute("""
                UPDATE reservations
                SET status = 'Cancelled'
                WHERE id = ?
                AND status IN ('Waiting', 'Ready')
            """, (reservation_id,))
        else:
            cursor = conn.execute("""
                UPDATE reservations
                SET status = 'Cancelled'
                WHERE id = ?
                AND user_id = ?
                AND status IN ('Waiting', 'Ready')
            """, (reservation_id, user_id))

        conn.commit()

        if cursor.rowcount > 0:
            return True, "Reservation cancelled successfully."

        return False, "Active reservation not found."

    except Exception as error:
        conn.rollback()
        return False, f"Cancellation failed: {error}"

    finally:
        conn.close()


# 5. Update reservation waiting queue
def update_reservation_queue(book_id):
    conn = get_connection()

    try:
        conn.execute("BEGIN IMMEDIATE")

        book = conn.execute("""
            SELECT available_copies
            FROM books
            WHERE id = ?
        """, (book_id,)).fetchone()

        if not book:
            conn.rollback()
            return False, "Book not found."

        available = book["available_copies"]

        waiting = conn.execute("""
            SELECT id
            FROM reservations
            WHERE book_id = ?
            AND status = 'Waiting'
            ORDER BY reservation_date ASC, id ASC
        """, (book_id,)).fetchall()

        ready_count = conn.execute("""
            SELECT COUNT(*)
            FROM reservations
            WHERE book_id = ?
            AND status = 'Ready'
        """, (book_id,)).fetchone()[0]

        slots = max(0, available - ready_count)

        for index, reservation in enumerate(waiting):
            if index < slots:
                status = "Ready"
            else:
                status = "Waiting"

            conn.execute("""
                UPDATE reservations
                SET status = ?
                WHERE id = ?
            """, (status, reservation["id"]))

        conn.commit()
        return True, "Reservation queue updated."

    except Exception as error:
        conn.rollback()
        return False, f"Queue update failed: {error}"

    finally:
        conn.close()
