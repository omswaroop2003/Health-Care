
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier, VotingClassifier
from sklearn.linear_model import LogisticRegression
from xgboost import XGBClassifier
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score
import joblib
import os
from typing import Tuple

class TriageModelTrainer:
    """Train ML model for ESI triage classification"""

    def __init__(self):
        self.scaler = StandardScaler()
        self.model = None
        self.feature_columns = None

    def prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare features for training"""
        features = pd.DataFrame()

        # Vital signs features
        features["bp_systolic"] = df["bp_systolic"]
        features["bp_diastolic"] = df["bp_diastolic"]
        features["heart_rate"] = df["heart_rate"]
        features["temperature"] = df["temperature"]
        features["o2_saturation"] = df["o2_saturation"]
        features["respiratory_rate"] = df["respiratory_rate"]

        # Demographics
        features["age"] = df["age"]
        features["is_male"] = (df["gender"] == "Male").astype(int)

        # Age groups
        features["is_infant"] = (df["age"] < 2).astype(int)
        features["is_child"] = ((df["age"] >= 2) & (df["age"] < 12)).astype(int)
        features["is_elderly"] = (df["age"] >= 65).astype(int)

        # Symptoms
        features["pain_scale"] = df["pain_scale"]
        features["is_unresponsive"] = (df["consciousness_level"] == "Unresponsive").astype(int)
        features["is_altered"] = df["consciousness_level"].isin(["Voice", "Pain"]).astype(int)
        features["has_bleeding"] = df["bleeding"].astype(int)
        features["has_breathing_difficulty"] = df["breathing_difficulty"].astype(int)
        features["has_trauma"] = df["trauma_indicator"].astype(int)

        # Medical history
        features["num_chronic_conditions"] = df["chronic_conditions"].apply(len)
        features["medications_count"] = df["medications_count"]
        features["has_allergies"] = df["allergies"].apply(lambda x: len(x) > 0).astype(int)
        features["previous_admissions"] = df["previous_admissions"]

        # Calculated features
        features["pulse_pressure"] = features["bp_systolic"] - features["bp_diastolic"]
        features["shock_index"] = features["heart_rate"] / features["bp_systolic"]

        # Vital signs abnormality scores
        features["bp_abnormal"] = (
            ((features["bp_systolic"] < 90) | (features["bp_systolic"] > 180)) |
            ((features["bp_diastolic"] < 60) | (features["bp_diastolic"] > 110))
        ).astype(int)

        features["hr_abnormal"] = (
            (features["heart_rate"] < 50) | (features["heart_rate"] > 120)
        ).astype(int)

        features["o2_abnormal"] = (features["o2_saturation"] < 92).astype(int)

        features["temp_abnormal"] = (
            (features["temperature"] < 35.5) | (features["temperature"] > 38.5)
        ).astype(int)

        features["rr_abnormal"] = (
            (features["respiratory_rate"] < 10) | (features["respiratory_rate"] > 30)
        ).astype(int)

        # Total abnormality score
        features["vital_abnormality_count"] = (
            features["bp_abnormal"] + features["hr_abnormal"] +
            features["o2_abnormal"] + features["temp_abnormal"] +
            features["rr_abnormal"]
        )

        self.feature_columns = features.columns.tolist()
        return features

    def train_model(self, X_train: pd.DataFrame, y_train: pd.Series) -> None:
        """Train ensemble model"""

        # Scale features
        X_train_scaled = self.scaler.fit_transform(X_train)

        # Create individual models
        rf_model = RandomForestClassifier(
            n_estimators=100,
            max_depth=10,
            min_samples_split=5,
            random_state=42,
            class_weight="balanced"
        )

        xgb_model = XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=42,
            use_label_encoder=False,
            eval_metric='mlogloss'
        )

        lr_model = LogisticRegression(
            max_iter=1000,
            random_state=42,
            class_weight="balanced"
        )

        # Create voting ensemble
        self.model = VotingClassifier(
            estimators=[
                ('rf', rf_model),
                ('xgb', xgb_model),
                ('lr', lr_model)
            ],
            voting='soft',
            weights=[0.6, 0.3, 0.1]
        )

        # Train the ensemble
        self.model.fit(X_train_scaled, y_train)

        # Cross-validation
        cv_scores = cross_val_score(self.model, X_train_scaled, y_train, cv=5)
        print(f"Cross-validation accuracy: {cv_scores.mean():.3f} (+/- {cv_scores.std() * 2:.3f})")

    def evaluate_model(self, X_test: pd.DataFrame, y_test: pd.Series) -> dict:
        """Evaluate model performance"""
        X_test_scaled = self.scaler.transform(X_test)
        y_pred = self.model.predict(X_test_scaled)

        # Calculate metrics
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred, output_dict=True)
        confusion = confusion_matrix(y_test, y_pred)

        print(f"\nModel Accuracy: {accuracy:.3f}")
        print("\nClassification Report:")
        print(classification_report(y_test, y_pred))
        print("\nConfusion Matrix:")
        print(confusion)

        return {
            "accuracy": accuracy,
            "classification_report": report,
            "confusion_matrix": confusion.tolist()
        }

    def get_feature_importance(self) -> pd.DataFrame:
        """Get feature importance from the Random Forest model"""
        rf_model = self.model.estimators_[0]
        importance = pd.DataFrame({
            'feature': self.feature_columns,
            'importance': rf_model.feature_importances_
        }).sort_values('importance', ascending=False)

        return importance

    def save_model(self, model_path: str, scaler_path: str) -> None:
        """Save trained model and scaler"""
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)
        joblib.dump(self.feature_columns, model_path.replace('.pkl', '_features.pkl'))
        print(f"Model saved to {model_path}")
        print(f"Scaler saved to {scaler_path}")


def main():
    # Load data
    print("Loading training data...")
    train_df = pd.read_csv("../../data/train_patients.csv")

    # Parse JSON columns
    for col in ['chronic_conditions', 'allergies']:
        train_df[col] = train_df[col].apply(eval)

    # Initialize trainer
    trainer = TriageModelTrainer()

    # Prepare features
    print("Preparing features...")
    X = trainer.prepare_features(train_df)
    y = train_df["true_esi_level"]

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    # Train model
    print("Training model...")
    trainer.train_model(X_train, y_train)

    # Evaluate model
    print("Evaluating model...")
    metrics = trainer.evaluate_model(X_test, y_test)

    # Feature importance
    print("\nTop 10 Most Important Features:")
    importance = trainer.get_feature_importance()
    print(importance.head(10))

    # Save model
    trainer.save_model(
        "../models/triage_classifier.pkl",
        "../models/feature_processor.pkl"
    )

    print("\nTraining completed successfully!")


if __name__ == "__main__":
    main()