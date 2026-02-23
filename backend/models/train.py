import sqlite3
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "database.db")
MODEL_PATH = os.path.join(os.path.dirname(__file__), "student_model.joblib")

def train_model():
    # 1. Load Data from SQLite
    if not os.path.exists(DB_PATH):
        print(f"Error: Database not found at {DB_PATH}. Run seed_data.py first.")
        return

    conn = sqlite3.connect(DB_PATH)
    query = "SELECT term1, term2, term3, attendance_score, final_passed FROM grades"
    df = pd.read_sql_query(query, conn)
    conn.close()

    if df.empty:
        print("Error: No data in 'grades' table. Run seed_data.py first.")
        return

    print(f"Dataset loaded: {len(df)} records.")

    # 2. Features and Target
    X = df[['term1', 'term2', 'term3', 'attendance_score']]
    y = df['final_passed']

    # 3. Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. Initialize Models
    models = {
        "Random Forest": RandomForestClassifier(n_estimators=100, random_state=42),
        "Logistic Regression": LogisticRegression(max_iter=1000, random_state=42)
    }

    best_model = None
    best_accuracy = 0
    best_model_name = ""

    print("\n--- Training and Comparing Models ---")
    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        accuracy = accuracy_score(y_test, y_pred)
        
        print(f"{name} Accuracy: {accuracy:.2%}")
        
        if accuracy >= best_accuracy:
            best_accuracy = accuracy
            best_model = model
            best_model_name = name

    # 5. Final Evaluation for Best Model
    print(f"\n🏆 Champion Model: {best_model_name} ({best_accuracy:.2%})")
    y_final_pred = best_model.predict(X_test)
    print("\nFinal Classification Report:")
    print(classification_report(y_test, y_final_pred))

    # 6. Feature Importance (Only for RF, as LogReg uses coefficients)
    if best_model_name == "Random Forest":
        importances = best_model.feature_importances_
        features = X.columns
        print("\nFeature Importances (Best Model):")
        for f, imp in zip(features, importances):
            print(f"- {f}: {imp:.4f}")

    # 7. Save the best model
    joblib.dump(best_model, MODEL_PATH)
    print(f"\nModel saved to: {MODEL_PATH}")
    
    # Save metadata about which model was used
    with open(os.path.join(os.path.dirname(__file__), "model_info.txt"), "w") as f:
        f.write(f"Model Type: {best_model_name}\nAccuracy: {best_accuracy:.4f}")

if __name__ == "__main__":
    train_model()
