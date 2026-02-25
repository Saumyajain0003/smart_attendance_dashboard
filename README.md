# AcademiQ: Smart Attendance & Early Warning System 📊🤖

**AcademiQ** is a production-grade predictive analytics platform designed to transform raw student data into actionable academic insights. By combining a high-performance **FastAPI** backend with a modern **React** frontend and **Machine Learning**, AcademiQ proactively identifies "At-Risk" students before they fall through the cracks.


## 📸 Project Walkthrough

### **1. AI-Driven Analytics Dashboard**
The main interface provides high-level statistics pulled directly from the PostgreSQL backend, showing total enrollment and average class attendance using glassmorphism aesthetics.
![Dashboard Screenshot](screenshots/Dashboard.png)

### **2. Managed Database (Neon PostgreSQL)**
AcademiQ is fully integrated with Neon's serverless PostgreSQL. The backend automatically initializes these tables on first launch, ensuring a production-ready data schema.
![Database Schema](screenshots/tables%20created%20.png)

### **3. Smart Data Ingestion**
Every CSV import triggers an idempotent pipeline. It identifies unique students, handles conflicts gracefully, and propagates data instantly across the analytics layer.
![Data Ingestion Proof](screenshots/data%20ingested%20in%20neondb.png)

### **4. Predictive Risk Registry**
The core "Smart" feature. The registry identifies students needing intervention based on low attendance or failing term marks, with real-time AI prediction confidence.
![At-Risk Registry](screenshots/Atrisk%20Students.png)

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

## 📂 CSV Import Template

To ensure successful data ingestion, your CSV file must follow this exact header structure:

| Header | Description | Example |
| :--- | :--- | :--- |
| `name` | Full name of the student | John Doe |
| `email` | Unique student email | john@example.com |
| `student_code` | Unique identification code | S1001 |
| `term1` | First term marks (0-100) | 85 |
| `term2` | Second term marks (0-100) | 78 |
| `term3` | Third term marks (0-100) | 92 |
| `attendance_score` | Overall attendance percentage | 88.5 |

### **Sample Row**
```csv
name,email,student_code,term1,term2,term3,attendance_score
Saumya Jain,saumya@example.com,S1234,90,85,88,95.5
```

---

## 📂 Architecture & Data Flow

1.  **Ingestion**: CSV data is uploaded via `/students/upload-csv`. 
2.  **Processing**: The backend identifies unique students by `student_code` or `email` and updates records in PostgreSQL.
3.  **Analytics**: The AI model (`student_model.joblib`) analyzes the new data to generate passing probabilities.
4.  **Visualization**: The React frontend polls the `/attendance/at-risk` and `/stats` endpoints to display real-time insights.

---

## 📝 License
 Built with ❤️ by Saumya Jain.
