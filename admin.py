
import streamlit as st
import pandas as pd
import plotly.express as px

from database import (
    get_all_books,
    get_all_users,
    get_statistics,
    add_book,
    delete_book
)

from borrowing import get_all_borrowings, return_book

from reservations import (
    get_all_reservations,
    cancel_reservation,
    update_reservation_queue
)


def show_admin():
    st.title("Admin Dashboard")
    st.caption("Manage your library from one place.")

    stats = get_statistics()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Book Titles", stats["books"])
    c2.metric("Total Copies", stats["copies"])
    c3.metric("Available Copies", stats["available"])
    c4.metric("Registered Students", stats["students"])

    c5, c6 = st.columns(2)
    c5.metric("Active Borrowings", stats["borrowed"])
    c6.metric("Overdue Books", stats["overdue"])

    st.divider()

    menu = st.selectbox(
        "Select Management Section",
        [
            "Overview",
            "Manage Books",
            "Manage Students",
            "Borrowing Records",
            "Return Books",
            "Reservations"
        ]
    )

    # OVERVIEW
    if menu == "Overview":
        st.subheader("Library Overview")

        books = get_all_books()

        if books:
            df = pd.DataFrame([dict(b) for b in books])

            chart_data = df.groupby(
                "category"
            )["total_copies"].sum().reset_index()

            fig = px.pie(
                chart_data,
                names="category",
                values="total_copies",
                title="Books by Category",
                hole=0.4
            )

            st.plotly_chart(
                fig,
                use_container_width=True
            )

        st.subheader("Recently Added Books")

        if books:
            st.dataframe(
                pd.DataFrame([dict(b) for b in books]).head(5),
                use_container_width=True,
                hide_index=True
            )

    # MANAGE BOOKS
    elif menu == "Manage Books":
        st.subheader("Add New Book")

        with st.form("add_book_form"):
            isbn = st.text_input("ISBN")
            title = st.text_input("Book Title")
            author = st.text_input("Author")

            category = st.selectbox(
                "Category",
                [
                    "Programming",
                    "Computer Science",
                    "Fiction",
                    "Science",
                    "Mathematics",
                    "Biography",
                    "History",
                    "Other"
                ]
            )

            publisher = st.text_input("Publisher")

            year = st.number_input(
                "Publication Year",
                1000,
                2100,
                2024
            )

            copies = st.number_input(
                "Number of Copies",
                1,
                1000,
                1
            )

            description = st.text_area("Description")

            submitted = st.form_submit_button(
                "Add Book",
                use_container_width=True
            )

            if submitted:
                if title.strip() and author.strip():
                    success, message = add_book(
                        isbn,
                        title,
                        author,
                        category,
                        publisher,
                        int(year),
                        int(copies),
                        description
                    )

                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
                else:
                    st.error("Title and author are required.")

        st.divider()
        st.subheader("Existing Books")

        books = get_all_books()

        if books:
            df = pd.DataFrame([dict(b) for b in books])

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            selected = st.selectbox(
                "Select a book to delete",
                options=[b["id"] for b in books],
                format_func=lambda x: next(
                    b["title"] for b in books if b["id"] == x
                )
            )

            if st.button(
                "Delete Selected Book",
                type="secondary"
            ):
                success, message = delete_book(selected)

                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.warning(message)

        else:
            st.info("No books in the catalogue.")

    # MANAGE STUDENTS
    elif menu == "Manage Students":
        st.subheader("Registered Students")

        users = [
            dict(u) for u in get_all_users()
            if u["role"] == "student"
        ]

        if users:
            st.dataframe(
                pd.DataFrame(users),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No students registered yet.")

    # BORROWING RECORDS
    elif menu == "Borrowing Records":
        st.subheader("All Borrowing Transactions")

        records = get_all_borrowings()

        if records:
            df = pd.DataFrame([dict(r) for r in records])

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            csv = df.to_csv(index=False).encode("utf-8")

            st.download_button(
                "Download Borrowing Report",
                csv,
                "shelfwise_borrowing_report.csv",
                "text/csv"
            )
        else:
            st.info("No borrowing transactions found.")

    # RETURN BOOKS
    elif menu == "Return Books":
        st.subheader("Process Book Returns")

        records = [
            dict(r) for r in get_all_borrowings()
            if r["status"] == "Borrowed"
        ]

        if records:
            selected = st.selectbox(
                "Select a borrowing record",
                options=[r["id"] for r in records],
                format_func=lambda x: next(
                    f'{r["student_name"]} - {r["title"]}'
                    for r in records if r["id"] == x
                )
            )

            if st.button("Confirm Book Return"):
                success, message = return_book(selected)

                if success:
                    selected_record = next(
                        r for r in records if r["id"] == selected
                    )

                    queue_success, queue_message = (
                        update_reservation_queue(
                            selected_record["book_id"]
                        )
                    )

                    st.success(message)

                    if not queue_success:
                        st.warning(queue_message)

                    st.rerun()
                else:
                    st.error(message)

        else:
            st.info("There are no active books to return.")

    # RESERVATIONS
    elif menu == "Reservations":
        st.subheader("Book Reservation Management")

        reservations = [
            dict(r) for r in get_all_reservations()
        ]

        if reservations:
            df = pd.DataFrame(reservations)

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            waiting = [
                r for r in reservations
                if r["status"] == "Waiting"
            ]

            ready = [
                r for r in reservations
                if r["status"] == "Ready"
            ]

            cancelled = [
                r for r in reservations
                if r["status"] == "Cancelled"
            ]

            a, b, c = st.columns(3)
            a.metric("Waiting", len(waiting))
            b.metric("Ready", len(ready))
            c.metric("Cancelled", len(cancelled))

            active_reservations = [
                r for r in reservations
                if r["status"] in ("Waiting", "Ready")
            ]

            if active_reservations:
                st.divider()
                st.subheader("Manage Active Reservations")

                selected = st.selectbox(
                    "Select reservation",
                    options=[
                        r["id"] for r in active_reservations
                    ],
                    format_func=lambda x: next(
                        f'{r["student_name"]} - '
                        f'{r["title"]} ({r["status"]})'
                        for r in active_reservations
                        if r["id"] == x
                    )
                )

                if st.button(
                    "Cancel Selected Reservation",
                    type="secondary"
                ):
                    success, message = cancel_reservation(
                        selected
                    )

                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

        else:
            st.info("No book reservations have been made yet.")
