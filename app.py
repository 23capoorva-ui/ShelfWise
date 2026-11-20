
import streamlit as st

from database import initialize_database, register_user
from auth import login_user, logout_user, get_current_user
from admin import show_admin
from student import show_student


st.set_page_config(
    page_title="ShelfWise | Library Management",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize database
initialize_database()

# Custom styling
st.markdown("""
<style>
    .stApp {
        background-color: #f5f7fb;
    }

    [data-testid="stSidebar"] {
        background-color: #10243a;
    }

    [data-testid="stSidebar"] * {
        color: #ffffff;
    }

    .main-title {
        color: #10243a;
        font-size: 42px;
        font-weight: 800;
        margin-bottom: 0;
    }

    .subtitle {
        color: #64748b;
        font-size: 16px;
    }

    div.stButton > button {
        border-radius: 8px;
        background-color: #137c80;
        color: white;
        border: none;
        font-weight: 600;
        padding: 10px 18px;
    }

    div.stButton > button:hover {
        background-color: #0e6266;
        color: white;
    }

    [data-testid="stMetric"] {
        background-color: white;
        border: 1px solid #e5eaf1;
        padding: 18px;
        border-radius: 12px;
    }
</style>
""", unsafe_allow_html=True)


def show_authentication():
    st.markdown(
        '<p class="main-title">📚 ShelfWise</p>',
        unsafe_allow_html=True
    )
    st.markdown(
        '<p class="subtitle">Your digital library, simplified.</p>',
        unsafe_allow_html=True
    )

    st.divider()

    left, right = st.columns([1, 1])

    with left:
        st.markdown("## Welcome to ShelfWise")
        st.write(
            "Discover books, borrow your favourites, "
            "and manage your library activities in one place."
        )

        st.markdown("### What you can do")
        st.write("📖 Explore the book collection")
        st.write("📚 Borrow and return books")
        st.write("📅 Track borrowing deadlines")
        st.write("📊 Manage your borrowing history")

    with right:
        tab1, tab2 = st.tabs(["Login", "Register"])

        with tab1:
            st.subheader("Sign in")

            email = st.text_input(
                "Email address", key="login_email"
            )
            password = st.text_input(
                "Password",
                type="password",
                key="login_password"
            )

            if st.button("Login", use_container_width=True):
                if not email or not password:
                    st.error("Please enter your email and password.")
                else:
                    success, message = login_user(email, password)

                    if success:
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)

            st.caption(
                "Admin demo: admin@shelfwise.com / Admin@123"
            )

        with tab2:
            st.subheader("Create Student Account")

            name = st.text_input(
                "Full Name", key="register_name"
            )
            student_id = st.text_input(
                "Student ID", key="register_id"
            )
            new_email = st.text_input(
                "Email Address", key="register_email"
            )
            new_password = st.text_input(
                "Create Password",
                type="password",
                key="register_password"
            )
            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                key="register_confirm"
            )

            if st.button(
                "Register", use_container_width=True
            ):
                if not all([
                    name.strip(),
                    student_id.strip(),
                    new_email.strip(),
                    new_password,
                    confirm_password
                ]):
                    st.error("Please complete all fields.")

                elif "@" not in new_email or "." not in new_email:
                    st.error("Please enter a valid email address.")

                elif len(new_password) < 8:
                    st.error("Password must have at least 8 characters.")

                elif new_password != confirm_password:
                    st.error("Passwords do not match.")

                else:
                    success, message = register_user(
                        name,
                        new_email,
                        new_password,
                        student_id
                    )

                    if success:
                        st.success(
                            "Account created! You can now log in."
                        )
                    else:
                        st.error(message)


def main():
    user = get_current_user()

    if user is None:
        show_authentication()

    else:
        with st.sidebar:
            st.markdown("# 📚 ShelfWise")
            st.caption("Library Management System")
            st.divider()

            st.write(f"Welcome, **{user['name']}**")
            st.write(f"Role: {user['role'].title()}")

            st.divider()

            if st.button("Logout", use_container_width=True):
                logout_user()

            st.divider()
            st.caption("ShelfWise v1.0")

        if user["role"] == "admin":
            show_admin()
        else:
            show_student()


if __name__ == "__main__":
    main()
