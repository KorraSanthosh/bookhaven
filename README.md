# 📚 BookHaven
**BookHaven** is a modern full-stack e-commerce platform for book enthusiasts, built using **FastAPI** and designed with a focus on performance, scalability, and user experience. It features a sleek Netflix-style UI, secure authentication, AI-powered recommendations, and complete order management.

---
## 🚀 Features

* 🔐 JWT-based user authentication
* 📖 Dynamic book catalog with search & filtering
* 🤖 AI-powered personalized recommendations
* 🛒 Cart, checkout, and order history system
* 🎨 Responsive Netflix-inspired dark UI
* ⚡ Fast and scalable backend using FastAPI

---

## 🛠️ Tech Stack

### Backend
* FastAPI
* Python
* MongoDB Atlas
* Motor (Async Driver)
* Pydantic

### Authentication
* JWT Authentication
* Passlib (bcrypt)
* Python-Jose

### Frontend
* **UI Framework:** Vanilla HTML5 & Modern CSS3
* **Interactivity:** Asynchronous JavaScript (Fetch API)
* **Design:** Premium Netflix-inspired Dark Mode
* **UX Features:** Real-time book search, Smooth hover effects, and Responsive layout

---

## ⚙️ Setup & Installation

### Clone Repository
```bash
git clone https://github.com/KorraSanthosh/bookhaven.git
cd bookhaven
```

### Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

### Run Application
```bash
uvicorn main:app --reload
```

Application runs at:
```text
http://127.0.0.1:8000
```

---

## 📂 Project Structure
```text
bookhaven/
├── routers/        # API routes
├── services/       # Business logic & recommendations
├── frontend/       # UI files
├── models.py       # Database models
├── schemas.py      # Pydantic schemas
├── main.py         # FastAPI entry point
└── requirements.txt
```

---

## 👨‍💻 Author
**Santhosh**
GitHub: [https://github.com/KorraSanthosh](https://github.com/KorraSanthosh)
