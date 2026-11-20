
import streamlit as st
from database import get_user_by_email, verify_password


def login_user(email, password):
    user = get_user_by_email(email)

    if user and verify_password(password, user["password"]):
        st.session_state["user"] = {
            "id": user["id"],
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "student_id": user["student_id"]
        }
        return True, "Login successful."

    return False, "Invalid email or password."


def logout_user():
    st.session_state.pop("user", None)
    st.rerun()


def get_current_user():
    return st.session_state.get("user")


def is_logged_in():
    return get_current_user() is not None


def is_admin():
    user = get_current_user()
    return user is not None and user["role"] == "admin"
