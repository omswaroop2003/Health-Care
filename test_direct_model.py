#!/usr/bin/env python3
"""
Direct test of the AI model loading and prediction
"""

import os
import pickle
import pandas as pd
import numpy as np

def test_direct_model():
    """Test loading the model directly"""
    try:
        # Load the model directly from the known working path
        model_path = "ml_pipeline/models/triage_classifier.pkl"
        scaler_path = "ml_pipeline/models/feature_processor.pkl"
        features_path = "ml_pipeline/models/triage_classifier_features.pkl"

        print("Loading AI model files...")
        print(f"Model path: {model_path}")
        print(f"Model exists: {os.path.exists(model_path)}")
        print(f"Scaler exists: {os.path.exists(scaler_path)}")
        print(f"Features exists: {os.path.exists(features_path)}")

        if os.path.exists(model_path):
            with open(model_path, 'rb') as f:
                model = pickle.load(f)
            print("✓ Model loaded successfully")

            scaler = None
            if os.path.exists(scaler_path):
                with open(scaler_path, 'rb') as f:
                    scaler = pickle.load(f)
                print("✓ Scaler loaded successfully")

            feature_names = None
            if os.path.exists(features_path):
                with open(features_path, 'rb') as f:
                    feature_names = pickle.load(f)
                print("✓ Feature names loaded successfully")
                print(f"Number of features: {len(feature_names)}")

            # Test prediction with sample data
            print("\nTesting model prediction...")

            # Sample patient data (matching the features from training)
            sample_features = [
                180,    # bp_systolic
                95,     # bp_diastolic
                120,    # heart_rate
                37.0,   # temperature (Celsius)
                95,     # o2_saturation
                22,     # respiratory_rate
                45,     # age
                1.0,    # gender_male
                0.0,    # is_infant
                0.0,    # is_child
                0.0,    # is_elderly
                8,      # pain_scale
                0.0,    # is_unresponsive
                0.0,    # is_altered
                0.0,    # bleeding
                1.0,    # breathing_difficulty
                0.0,    # trauma_indicator
                2.0,    # chronic_conditions_count
                1.0,    # medications_count
                0.0,    # has_allergies
                0.0,    # previous_admissions
                85,     # pulse_pressure
                0.67,   # shock_index
                1.0,    # bp_abnormal
                1.0,    # hr_abnormal
                1.0,    # o2_abnormal
                0.0,    # temp_abnormal
                1.0,    # rr_abnormal
                5.0     # vital_abnormality_count
            ]

            # Ensure we have the right number of features
            print(f"Sample features length: {len(sample_features)}")

            if scaler:
                sample_features_scaled = scaler.transform([sample_features])
            else:
                sample_features_scaled = [sample_features]

            prediction = model.predict(sample_features_scaled)[0]
            probabilities = model.predict_proba(sample_features_scaled)[0]
            confidence = float(np.max(probabilities))

            print(f"✓ Prediction: ESI Level {prediction}")
            print(f"✓ Confidence: {confidence:.1%}")
            print(f"✓ Probabilities: {probabilities}")

            return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_direct_model()