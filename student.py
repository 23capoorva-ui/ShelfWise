
import streamlit as st
import pandas as pd

from database import get_all_books
from borrowing import get_user_borrowings, borrow_book
from reservations import (
    reserve_book,
    get_user_reservations,
    cancel_reservation
)


def show_student():
    user = st.session_state["user"]
    user_id = user["id"]

    st.title(f"Welcome, {user['name']}!")
    st.caption("Discover books and manage your borrowing activity.")

    records = [
        dict(r) for r in get_user_borrowings(user_id)
    ]

    reservations = [
        dict(r) for r in get_user_reservations(user_id)
    ]

    active = [
        r for r in records if r["status"] == "Borrowed"
    ]

    today = pd.Timestamp.today().strftime("%Y-%m-%d")

    overdue = [
        r for r in active if r["due_date"] < today
    ]

    c1, c2, c3 = st.columns(3)
    c1.metric("Currently Borrowed", len(active))
    c2.metric("Overdue Books", len(overdue))
    c3.metric("Total Borrowings", len(records))

    st.divider()

    menu = st.selectbox(
        "Choose a section",
        [
            "Explore Books",
            "My Borrowings",
            "Borrowing History",
            "My Reservations",
            "My Profile"
        ]
    )

    # EXPLORE BOOKS
    if menu == "Explore Books":
        st.subheader("Explore Our Collection")

        books = [dict(b) for b in get_all_books()]

        search = st.text_input(
            "Search by book title, author or category",
            placeholder="Search books..."
        )

        category_options = ["All"] + sorted({
            b["category"] for b in books
        })

        category = st.selectbox(
            "Filter by category", category_options
        )

        filtered = [
            b for b in books
            if (
                search.lower() in (
                    str(b["title"]) + " " +
                    str(b["author"]) + " " +
                    str(b["category"])
                ).lower()
            )
            and (
                category == "All"
                or b["category"] == category
            )
        ]

        if not filtered:
            st.info("No matching books found.")

        for book in filtered:
            with st.container(border=True):
                st.subheader(book["title"])
                st.write(f"**Author:** {book['author']}")
                st.write(f"**Category:** {book['category']}")
                st.write(
                    f"**Publisher:** {book['publisher'] or 'N/A'}"
                )
                st.write(
                    f"**Available copies:** {book['available_copies']}"
                )

                if book["description"]:
                    st.write(book["description"])

                if book["available_copies"] > 0:
                    if st.button(
                        "Borrow This Book",
                        key=f"borrow_{book['id']}"
                    ):
                        success, message = borrow_book(
                            user_id, book["id"]
                        )

                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

                else:
                    st.warning("Currently unavailable.")

                    if st.button(
                        "Reserve This Book",
                        key=f"reserve_{book['id']}"
                    ):
                        success, message = reserve_book(
                            user_id, book["id"]
                        )

                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)

    # MY BORROWINGS
    elif menu == "My Borrowings":
        st.subheader("Currently Borrowed Books")

        if active:
            for record in active:
                with st.container(border=True):
                    st.write(f"**{record['title']}**")
                    st.write(f"Author: {record['author']}")
                    st.write(f"Borrowed: {record['borrow_date']}")
                    st.write(f"Due date: {record['due_date']}")

                    if record["due_date"] < today:
                        st.error("This book is overdue.")
                    else:
                        st.success("Active borrowing")

        else:
            st.info("You have no active borrowings.")

    # BORROWING HISTORY
    elif menu == "Borrowing History":
        st.subheader("Your Borrowing History")

        if records:
            df = pd.DataFrame(records)

            columns = [
                "title", "author", "borrow_date",
                "due_date", "return_date", "fine", "status"
            ]

            available_columns = [
                c for c in columns if c in df.columns
            ]

            st.dataframe(
                df[available_columns],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No borrowing history available.")

    # MY RESERVATIONS
    elif menu == "My Reservations":
        st.subheader("My Book Reservations")

        reservations = [
            dict(r) for r in get_user_reservations(user_id)
        ]

        if reservations:
            for reservation in reservations:
                with st.container(border=True):
                    st.write(f"**{reservation['title']}**")
                    st.write(f"Author: {reservation['author']}")
                    st.write(
                        f"Reservation date: "
                        f"{reservation['reservation_date']}"
                    )

                    status = reservation["status"]

                    if status == "Ready":
                        st.success(
                            "Your reservation is ready. "
                            "Please contact the library administrator."
                        )
                    elif status == "Waiting":
                        st.info("You are in the waiting queue.")
                    elif status == "Cancelled":
                        st.warning("Reservation cancelled.")

                    if status in ("Waiting", "Ready"):
                        if st.button(
                            "Cancel Reservation",
                            key=f"cancel_{reservation['id']}"
                        ):
                            success, message = cancel_reservation(
                                reservation["id"], user_id
                            )

                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)

        else:
            st.info("You have not made any reservations.")

    # MY PROFILE
    elif menu == "My Profile":
        st.subheader("Student Profile")

        st.write(f"**Name:** {user['name']}")
        st.write(f"**Email:** {user['email']}")
        st.write(
            f"**Student ID:** {user['student_id'] or 'N/A'}"
        )
        st.write("**Account Type:** Student")
