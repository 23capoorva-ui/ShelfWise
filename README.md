# 📚 ShelfWise – Library Management and Borrowing System

ShelfWise is a web-based Library Management System developed using **Python, Streamlit and SQLite**. It provides a simple platform for managing library books, student accounts, borrowing activities and reservations.

## 🎯 Project Overview

The main objective of ShelfWise is to simplify library operations by providing separate interfaces for administrators and students. It helps manage book availability, borrowing records and reservations through an easy-to-use web application.

## ✨ Key Features

### 👨‍💼 Admin Module
- Admin login and dashboard.
- Add and manage books.
- Manage student records.
- View borrowing records.
- Manage book returns.
- View and manage reservations.

### 👩‍🎓 Student Module
- Student registration and login.
- Explore available books.
- Borrow books.
- View currently borrowed books.
- Access borrowing history.
- Reserve unavailable books.
- View and cancel reservations.
- View personal profile.

### 📖 Library Management
- Book availability tracking.
- Borrowing and return management.
- Reservation queue management.
- Borrowing period and overdue fine tracking.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | Web application interface |
| SQLite | Database management |
| Pandas | Data handling |
| Plotly | Data visualization |

## 📂 Project Structure

```text
ShelfWise/
│
├── app.py
├── database.py
├── auth.py
├── borrowing.py
├── reservations.py
├── admin.py
├── student.py
├── requirements.txt
├── .gitignore
│
└── shelfwise.db
```

*Note: The SQLite database is created and maintained locally and is excluded from this public repository.*

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/23capoorva-ui/ShelfWise.git
```

### 2. Navigate to the project folder

```bash
cd ShelfWise
```

### 3. Create a virtual environment

```bash
python -m venv .venv
```

### 4. Activate the virtual environment (Windows)

```bash
.venv\Scripts\activate
```

### 5. Install dependencies

```bash
pip install -r requirements.txt
```

### 6. Run the application

```bash
python -m streamlit run app.py
```

The application will open in your browser.

## 🎓 Project Purpose

ShelfWise is developed as an academic project to demonstrate the practical application of Python programming, database management and web application development.

## 👩‍💻 Developer

**Project Name:** ShelfWise  
**Project Type:** Library Management System  
**Repository:** https://github.com/23capoorva-ui/ShelfWise

---

*ShelfWise – Making Library Management Simpler and Smarter.*
