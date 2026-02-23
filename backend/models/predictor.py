import joblib
import os
import numpy as np

class StudentPredictor:
    def __init__(self):
        self.model_path = os.path.join(os.path.dirname(__file__), "student_model.joblib")
        self.model = None
        self.load_model()

    def load_model(self):
        if os.path.exists(self.model_path):
            self.model = joblib.load(self.model_path)
            print(f"Model loaded successfully from {self.model_path}")
        else:
            print("Warning: Model file not found. Please run train.py first.")

    def predict(self, term1, term2, term3, attendance_score):
        if self.model is None:
            return None, "Model not trained"
        
        # Prepare input
        features = np.array([[term1, term2, term3, attendance_score]])
        
        # Predict class
        prediction = int(self.model.predict(features)[0])
        
        # Predict probability for all classes
        probs = self.model.predict_proba(features)[0]
        
        # 'probability' now represents the confidence score for the PREDICTED class
        # (e.g. if we predict Fail, this is the probability of Fail)
        confidence = float(probs[prediction])
        
        return prediction, confidence
