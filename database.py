
import sqlite3
import hashlib
import secrets
from datetime import datetime

DB_NAME = "shelfwise.db"


def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def hash_password(password, salt=None):
    salt = salt or secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode(),
        salt.encode(),
        100000
    ).hex()
    return f"{salt}${hashed}"


def verify_password(password, stored_password):
    try:
        salt, stored_hash = stored_password.split("$")
        return hash_password(password, salt) == stored_password
    except (ValueError, AttributeError):
        return False


def initialize_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'student',
            student_id TEXT UNIQUE,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            isbn TEXT UNIQUE,
            title TEXT NOT NULL,
            author TEXT NOT NULL,
            category TEXT NOT NULL,
            publisher TEXT,
            year INTEGER,
            total_copies INTEGER NOT NULL DEFAULT 1,
            available_copies INTEGER NOT NULL DEFAULT 1,
            description TEXT,
            created_at TEXT NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS borrowings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            borrow_date TEXT NOT NULL,
            due_date TEXT NOT NULL,
            return_date TEXT,
            fine REAL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Borrowed',
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(book_id) REFERENCES books(id)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_borrowings_user
        ON borrowings(user_id)
    """)


    # Upgrade existing borrowing table safely
    columns = [
        row[1]
        for row in cursor.execute(
            "PRAGMA table_info(borrowings)"
        ).fetchall()
    ]

    if "fine_paid" not in columns:
        cursor.execute("""
            ALTER TABLE borrowings
            ADD COLUMN fine_paid REAL NOT NULL DEFAULT 0
        """)

    # Create reservations table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            book_id INTEGER NOT NULL,
            reservation_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Waiting',
            notified_at TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id),
            FOREIGN KEY(book_id) REFERENCES books(id)
        )
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reservations_book
        ON reservations(book_id, status, reservation_date)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reservations_user
        ON reservations(user_id, status)
    """)


    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_borrowings_book
        ON borrowings(book_id)
    """)

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_borrowings_status
        ON borrowings(status)
    """)

    # Create a default administrator if one does not exist.
    admin = cursor.execute(
        "SELECT id FROM users WHERE email = ?",
        ("admin@shelfwise.com",)
    ).fetchone()

    if not admin:
        cursor.execute("""
            INSERT INTO users
            (name, email, password, role, student_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            "ShelfWise Administrator",
            "admin@shelfwise.com",
            hash_password("Admin@123"),
            "admin",
            None,
            datetime.now().isoformat()
        ))

    # Insert sample books only when the catalogue is empty.
    count = cursor.execute(
        "SELECT COUNT(*) FROM books"
    ).fetchone()[0]

    if count == 0:
        sample_books = [
            ("9780132350884", "Clean Code", "Robert C. Martin",
             "Programming", "Prentice Hall", 2008, 5, 5,
             "A practical guide to writing clean and maintainable code."),

            ("9780262033848", "Introduction to Algorithms",
             "Thomas H. Cormen", "Computer Science",
             "MIT Press", 2009, 4, 4,
             "A comprehensive introduction to algorithms."),

            ("9780134685991", "Effective Java", "Joshua Bloch",
             "Programming", "Addison-Wesley", 2017, 3, 3,
             "Best practices for Java programming."),

            ("9780596007126", "Head First Design Patterns",
             "Eric Freeman", "Programming", "O'Reilly", 2004,
             3, 3, "Learn software design patterns visually."),

            ("9780141439518", "Pride and Prejudice",
             "Jane Austen", "Fiction", "Penguin Classics",
             1813, 4, 4, "A classic novel about love and society."),

            ("9780743273565", "The Great Gatsby",
             "F. Scott Fitzgerald", "Fiction", "Scribner",
             1925, 3, 3, "A classic American novel."),

            ("9780061120084", "To Kill a Mockingbird",
             "Harper Lee", "Fiction", "Harper Perennial",
             1960, 3, 3, "A novel exploring justice and morality."),

            ("9780131103627", "The C Programming Language",
             "Brian W. Kernighan", "Programming",
             "Prentice Hall", 1988, 4, 4,
             "A classic guide to the C programming language."),

            ("9781491950296", "Fluent Python",
             "Luciano Ramalho", "Programming",
             "O'Reilly", 2015, 2, 2,
             "Practical programming with Python."),

            ("9780451524935", "1984", "George Orwell",
             "Fiction", "Signet Classics", 1949, 3, 3,
             "A dystopian novel about surveillance and control.")
        ]

        cursor.executemany("""
            INSERT INTO books (
                isbn, title, author, category, publisher,
                year, total_copies, available_copies,
                description, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            (*book, datetime.now().isoformat())
            for book in sample_books
        ])

    conn.commit()
    conn.close()


def get_all_books():
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM books ORDER BY title"
        ).fetchall()


def get_book(book_id):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM books WHERE id = ?",
            (book_id,)
        ).fetchone()


def get_all_users():
    with get_connection() as conn:
        return conn.execute(
            "SELECT id, name, email, role, student_id, created_at "
            "FROM users ORDER BY name"
        ).fetchall()


def get_user_by_email(email):
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM users WHERE email = ?",
            (email.strip().lower(),)
        ).fetchone()


def register_user(name, email, password, student_id):
    try:
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO users
                (name, email, password, role, student_id, created_at)
                VALUES (?, ?, ?, 'student', ?, ?)
            """, (
                name.strip(),
                email.strip().lower(),
                hash_password(password),
                student_id.strip(),
                datetime.now().isoformat()
            ))
        return True, "Registration successful."

    except sqlite3.IntegrityError:
        return False, "Email or student ID already exists."


def add_book(isbn, title, author, category, publisher,
             year, total_copies, description):
    try:
        with get_connection() as conn:
            conn.execute("""
                INSERT INTO books (
                    isbn, title, author, category, publisher,
                    year, total_copies, available_copies,
                    description, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                isbn.strip() or None,
                title.strip(),
                author.strip(),
                category,
                publisher.strip(),
                year,
                total_copies,
                total_copies,
                description.strip(),
                datetime.now().isoformat()
            ))
        return True, "Book added successfully."

    except sqlite3.IntegrityError as e:
        return False, f"Database error: {e}"


def update_book(book_id, isbn, title, author, category,
                publisher, year, total_copies, description):
    try:
        with get_connection() as conn:
            conn.execute("""
                UPDATE books
                SET isbn=?, title=?, author=?, category=?,
                    publisher=?, year=?, total_copies=?,
                    available_copies = available_copies + ?,
                    description=?
                WHERE id=?
            """, (
                isbn.strip() or None,
                title.strip(),
                author.strip(),
                category,
                publisher.strip(),
                year,
                total_copies,
                total_copies - get_book(book_id)["total_copies"],
                description.strip(),
                book_id
            ))
        return True, "Book updated successfully."

    except (sqlite3.IntegrityError, TypeError, KeyError):
        return False, "Could not update book. Check the ISBN and copies."


def delete_book(book_id):
    with get_connection() as conn:
        active = conn.execute("""
            SELECT COUNT(*) FROM borrowings
            WHERE book_id = ? AND status = 'Borrowed'
        """, (book_id,)).fetchone()[0]

        history = conn.execute("""
            SELECT COUNT(*) FROM borrowings WHERE book_id = ?
        """, (book_id,)).fetchone()[0]

        if active or history:
            return False, "This book has borrowing records and cannot be deleted."

        conn.execute("DELETE FROM books WHERE id = ?", (book_id,))
        return True, "Book deleted successfully."


def get_statistics():
    with get_connection() as conn:
        return {
            "books": conn.execute(
                "SELECT COUNT(*) FROM books"
            ).fetchone()[0],
            "copies": conn.execute(
                "SELECT COALESCE(SUM(total_copies), 0) FROM books"
            ).fetchone()[0],
            "available": conn.execute(
                "SELECT COALESCE(SUM(available_copies), 0) FROM books"
            ).fetchone()[0],
            "students": conn.execute(
                "SELECT COUNT(*) FROM users WHERE role = 'student'"
            ).fetchone()[0],
            "borrowed": conn.execute(
                "SELECT COUNT(*) FROM borrowings WHERE status = 'Borrowed'"
            ).fetchone()[0],
            "overdue": conn.execute("""
                SELECT COUNT(*) FROM borrowings
                WHERE status = 'Borrowed' AND due_date < ?
            """, (datetime.now().strftime("%Y-%m-%d"),)).fetchone()[0]
        }
