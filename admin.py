
import random
from datetime import date, timedelta

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


# --------------------------------------------------
# SAMPLE ANALYTICS DATA
# --------------------------------------------------

def create_sample_analytics_data():

    rng = random.Random(42)

    sample_books = [
        ("Python Crash Course", "Programming"),
        ("Clean Code", "Computer Science"),
        ("The Alchemist", "Fiction"),
        ("Introduction to Algorithms", "Computer Science"),
        ("Atomic Habits", "Other"),
        ("Let Us C", "Programming"),
        ("The Theory of Everything", "Science"),
        ("A Brief History of Time", "Science"),
        ("Discrete Mathematics", "Mathematics"),
        ("Wings of Fire", "Biography")
    ]

    today = date.today()

    start_date = (
        today.replace(day=1) - pd.DateOffset(months=5)
    ).date()

    records = []

    for i in range(50):

        book, category = rng.choices(
            sample_books,
            weights=[9, 7, 6, 6, 5, 5, 4, 3, 3, 2],
            k=1
        )[0]

        borrowed_date = start_date + timedelta(
            days=rng.randint(
                0,
                max((today - start_date).days, 0)
            )
        )

        records.append({
            "Borrowing ID": i + 1,
            "Book Title": book,
            "Category": category,
            "Borrow Date": borrowed_date
        })

    return pd.DataFrame(records)


# --------------------------------------------------
# ANALYTICS DASHBOARD
# --------------------------------------------------

def show_sample_analytics():

    st.subheader("Library Analytics")

    st.caption(
        "Demonstration analytics using 50 synthetic borrowing "
        "records across six months. These are sample records "
        "and not actual student transactions."
    )

    df = create_sample_analytics_data()

    df["Borrow Date"] = pd.to_datetime(df["Borrow Date"])

    df["Month"] = (
        df["Borrow Date"].dt.to_period("M").dt.to_timestamp()
    )

    month_range = pd.date_range(
        start=df["Month"].min(),
        end=pd.Timestamp.today().replace(day=1),
        freq="MS"
    )

    monthly = (
        df.groupby("Month")
        .size()
        .reindex(month_range, fill_value=0)
        .rename_axis("Month")
        .reset_index(name="Borrowings")
    )

    popular_books = (
        df.groupby("Book Title")
        .size()
        .reset_index(name="Borrow Count")
        .sort_values("Borrow Count", ascending=False)
    )

    categories = (
        df.groupby("Category")
        .size()
        .reset_index(name="Borrow Count")
    )

    # SUMMARY METRICS

    c1, c2, c3 = st.columns(3)

    c1.metric("Sample Borrowings", len(df))
    c2.metric("Books Represented", df["Book Title"].nunique())
    c3.metric("Categories", df["Category"].nunique())

    st.divider()

    # CHART 1: MONTHLY BORROWING TREND

    st.subheader("1. Monthly Borrowing Trend")

    fig1 = px.line(
        monthly,
        x="Month",
        y="Borrowings",
        markers=True,
        title="Number of Borrowings per Month"
    )

    fig1.update_layout(
        xaxis_title="Month",
        yaxis_title="Borrowings"
    )

    st.plotly_chart(
        fig1,
        use_container_width=True
    )

    # CHART 2: MOST BORROWED BOOKS

    st.subheader("2. Most Borrowed Books")

    fig2 = px.bar(
        popular_books.head(10),
        x="Book Title",
        y="Borrow Count",
        text="Borrow Count",
        title="Top Borrowed Books"
    )

    fig2.update_layout(
        xaxis_title="Book Title",
        yaxis_title="Borrow Count"
    )

    fig2.update_xaxes(tickangle=-25)

    st.plotly_chart(
        fig2,
        use_container_width=True
    )

    # CHART 3: CATEGORY-WISE BORROWING

    st.subheader("3. Category-wise Borrowing")

    fig3 = px.pie(
        categories,
        names="Category",
        values="Borrow Count",
        title="Borrowings by Book Category",
        hole=0.35
    )

    st.plotly_chart(
        fig3,
        use_container_width=True
    )

    # KEY INSIGHTS

    st.divider()

    st.subheader("Key Insights from Sample Data")

    busiest_month = monthly.loc[
        monthly["Borrowings"].idxmax()
    ]

    popular_book = popular_books.iloc[0]

    popular_category = categories.sort_values(
        "Borrow Count",
        ascending=False
    ).iloc[0]

    st.write(
        f"1. **Busiest month:** "
        f"{busiest_month['Month'].strftime('%B %Y')} "
        f"has the highest sample borrowing count "
        f"({int(busiest_month['Borrowings'])})."
    )

    st.write(
        f"2. **Most borrowed book:** "
        f"{popular_book['Book Title']} "
        f"has been borrowed "
        f"{int(popular_book['Borrow Count'])} times."
    )

    st.write(
        f"3. **Popular category:** "
        f"{popular_category['Category']} "
        f"has the highest sample borrowing count "
        f"({int(popular_category['Borrow Count'])})."
    )

    with st.expander("View the 50 Sample Records"):

        st.dataframe(
            df,
            use_container_width=True,
            hide_index=True
        )


# --------------------------------------------------
# ADMIN DASHBOARD
# --------------------------------------------------

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
            "Analytics",
            "Manage Books",
            "Manage Students",
            "Borrowing Records",
            "Return Books",
            "Reservations"
        ]
    )

    # --------------------------------------------------
    # OVERVIEW
    # --------------------------------------------------

    if menu == "Overview":

        st.subheader("Library Overview")

        books = get_all_books()

        if books:

            df = pd.DataFrame(
                [dict(b) for b in books]
            )

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
                pd.DataFrame(
                    [dict(b) for b in books]
                ).head(5),
                use_container_width=True,
                hide_index=True
            )

    # --------------------------------------------------
    # ANALYTICS
    # --------------------------------------------------

    elif menu == "Analytics":

        show_sample_analytics()

    # --------------------------------------------------
    # MANAGE BOOKS
    # --------------------------------------------------

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

                    st.error(
                        "Title and author are required."
                    )

        st.divider()

        st.subheader("Existing Books")

        books = get_all_books()

        if books:

            df = pd.DataFrame(
                [dict(b) for b in books]
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            selected = st.selectbox(
                "Select a book to delete",
                options=[b["id"] for b in books],
                format_func=lambda x: next(
                    b["title"]
                    for b in books
                    if b["id"] == x
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

    # --------------------------------------------------
    # MANAGE STUDENTS
    # --------------------------------------------------

    elif menu == "Manage Students":

        st.subheader("Registered Students")

        users = [
            dict(u)
            for u in get_all_users()
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

    # --------------------------------------------------
    # BORROWING RECORDS
    # --------------------------------------------------

    elif menu == "Borrowing Records":

        st.subheader("All Borrowing Transactions")

        records = get_all_borrowings()

        if records:

            df = pd.DataFrame(
                [dict(r) for r in records]
            )

            st.dataframe(
                df,
                use_container_width=True,
                hide_index=True
            )

            csv = df.to_csv(
                index=False
            ).encode("utf-8")

            st.download_button(
                "Download Borrowing Report",
                csv,
                "shelfwise_borrowing_report.csv",
                "text/csv"
            )

        else:

            st.info("No borrowing transactions found.")

    # --------------------------------------------------
    # RETURN BOOKS
    # --------------------------------------------------

    elif menu == "Return Books":

        st.subheader("Process Book Returns")

        records = [
            dict(r)
            for r in get_all_borrowings()
            if r["status"] == "Borrowed"
        ]

        if records:

            selected = st.selectbox(
                "Select a borrowing record",
                options=[r["id"] for r in records],
                format_func=lambda x: next(
                    f'{r["student_name"]} - {r["title"]}'
                    for r in records
                    if r["id"] == x
                )
            )

            if st.button("Confirm Book Return"):

                success, message = return_book(selected)

                if success:

                    selected_record = next(
                        r
                        for r in records
                        if r["id"] == selected
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

            st.info(
                "There are no active books to return."
            )

    # --------------------------------------------------
    # RESERVATIONS
    # --------------------------------------------------

    elif menu == "Reservations":

        st.subheader("Book Reservation Management")

        reservations = [
            dict(r)
            for r in get_all_reservations()
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
                r
                for r in reservations
                if r["status"] in ("Waiting", "Ready")
            ]

            if active_reservations:

                st.divider()

                st.subheader(
                    "Manage Active Reservations"
                )

                selected = st.selectbox(
                    "Select reservation",
                    options=[
                        r["id"]
                        for r in active_reservations
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

            st.info(
                "No book reservations have been made yet."
            )
