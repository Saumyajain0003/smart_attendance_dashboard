# AcademiQ: Smart Attendance & Early Warning System 📊🤖

**AcademiQ** is a production-grade predictive analytics platform designed to transform raw student data into actionable academic insights. By combining a high-performance **FastAPI** backend with a modern **React** frontend and **Machine Learning**, AcademiQ proactively identifies "At-Risk" students before they fall through the cracks.

---

## 🌟 Key Features

-   **AI-Powered Risk Prediction**: Uses Scikit-learn (Random Forest) to predict the probability of a student passing based on attendance patterns and term marks.
-   **Automated Data Ingestion**: Robust CSV upload pipeline with idempotent "UPSERT" logic (handles 100+ records seamlessly).
-   **Production Database Architecture**: Fully integrated with **PostgreSQL (Neon.tech)** for scalable, persistent data storage.
-   **Dynamic Risk Registry**: Real-time filtering and calculation of "At-Risk" status (Dual-Risk: Attendance < 75% OR Grades < 50%).
-   **Live Statistics**: Instant dashboard stats showing "Total Enrolled" and "Average Class Attendance."
-   **Micro-Animation UI**: A premium, "Dark Mode" glassmorphism interface built for high user engagement.

---

## 🛠️ Tech Stack

### **Backend**
-   **FastAPI**: High-performance asynchronous API framework.
-   **SQLAlchemy**: Professional ORM for database abstraction.
-   **PostgreSQL**: Production-grade relational database (via Neon).
-   **Scikit-Learn**: Machine Learning library for predictive modeling.

### **Frontend**
-   **React + Vite**: Ultra-fast, modern web framework.
-   **Vanilla CSS**: Custom styling with glassmorphism and micro-animations.
-   **Recharts**: Data visualization for performance analytics.

---

## 🚀 Quick Start

### 1. Prerequisites
- Python 3.9+
- Node.js & npm
- A PostgreSQL connection string (e.g., from Neon.tech)

### 2. Setup Environment
Create a `.env` file in the root directory:
```env
DATABASE_URL=postgresql://user:password@host/dbname?sslmode=require
```

### 3. Unified Launch
The project includes a single entry point to launch both the backend and frontend simultaneously:
```bash
# 1. Activate your virtual environment
source .venv/bin/activate  # Mac/Linux
# 2. Run the unified launcher
python start_app.py
```
-   **Dashboard**: `http://localhost:5173`
-   **API Docs**: `http://localhost:8000/docs`

---

## 📂 Architecture & Data Flow

1.  **Ingestion**: CSV data is uploaded via `/students/upload-csv`. 
2.  **Processing**: The backend identifies unique students by `student_code` or `email` and updates records in PostgreSQL.
3.  **Analytics**: The AI model (`student_model.joblib`) analyzes the new data to generate passing probabilities.
4.  **Visualization**: The React frontend polls the `/attendance/at-risk` and `/stats` endpoints to display real-time insights.

---

## 📝 License
 Built with ❤️ by Saumya Jain.
