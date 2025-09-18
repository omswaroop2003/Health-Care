import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
from faker import Faker

fake = Faker()

class SyntheticPatientGenerator:
    """Generate realistic synthetic patient data for training and testing"""

    def __init__(self, seed: int = 42):
        random.seed(seed)
        np.random.seed(seed)
        self.fake = Faker()
        Faker.seed(seed)

        self.chief_complaints = {
            1: [  # ESI Level 1
                "cardiac arrest", "respiratory failure", "severe trauma",
                "unresponsive after accident", "active seizure",
                "severe allergic reaction with difficulty breathing"
            ],
            2: [  # ESI Level 2
                "chest pain with sweating", "stroke symptoms", "severe abdominal pain",
                "difficulty breathing", "severe bleeding from head wound",
                "altered mental status", "severe burn"
            ],
            3: [  # ESI Level 3
                "moderate abdominal pain", "asthma exacerbation", "kidney stone pain",
                "moderate laceration", "fever with vomiting", "moderate head injury",
                "broken bone suspected"
            ],
            4: [  # ESI Level 4
                "minor laceration", "sprained ankle", "sore throat",
                "mild headache", "minor burn", "ear pain", "back pain"
            ],
            5: [  # ESI Level 5
                "medication refill", "routine check-up", "minor rash",
                "common cold symptoms", "mild constipation"
            ]
        }

    def generate_patient(self, esi_level: int = None) -> Dict:
        """Generate a single patient with specified ESI level"""
        if esi_level is None:
            # Realistic distribution of ESI levels in ER
            esi_level = np.random.choice([1, 2, 3, 4, 5], p=[0.02, 0.08, 0.35, 0.40, 0.15])

        patient = {
            "age": self._generate_age(esi_level),
            "gender": random.choice(["Male", "Female"]),
            "arrival_time": datetime.now() - timedelta(minutes=random.randint(0, 120)),
            "chief_complaint": random.choice(self.chief_complaints[esi_level])
        }

        # Generate vital signs based on ESI level
        patient.update(self._generate_vital_signs(esi_level, patient["age"]))

        # Generate symptoms
        patient.update(self._generate_symptoms(esi_level))

        # Generate medical history
        patient.update(self._generate_medical_history(patient["age"]))

        # Add true ESI level for training
        patient["true_esi_level"] = esi_level

        return patient

    def _generate_age(self, esi_level: int) -> int:
        """Generate age based on ESI level"""
        if esi_level in [1, 2]:
            # Higher chance of elderly or very young
            if random.random() < 0.3:
                return random.randint(0, 5)  # Young children
            elif random.random() < 0.6:
                return random.randint(65, 95)  # Elderly
            else:
                return random.randint(20, 64)  # Adults
        else:
            # Normal age distribution
            return max(0, int(np.random.normal(40, 20)))

    def _generate_vital_signs(self, esi_level: int, age: int) -> Dict:
        """Generate vital signs based on ESI level and age"""
        vitals = {}

        if esi_level == 1:
            # Critical vital signs
            vitals["bp_systolic"] = random.choice([
                random.randint(60, 85),  # Very low
                random.randint(185, 220)  # Very high
            ])
            vitals["bp_diastolic"] = random.randint(40, 60) if vitals["bp_systolic"] < 90 else random.randint(110, 140)
            vitals["heart_rate"] = random.choice([
                random.randint(30, 45),  # Bradycardia
                random.randint(130, 180)  # Tachycardia
            ])
            vitals["o2_saturation"] = random.randint(70, 88)
            vitals["respiratory_rate"] = random.choice([
                random.randint(5, 9),  # Very low
                random.randint(32, 40)  # Very high
            ])
            vitals["temperature"] = random.choice([
                round(random.uniform(34.0, 35.5), 1),  # Hypothermia
                round(random.uniform(39.5, 41.0), 1)  # High fever
            ])

        elif esi_level == 2:
            # Abnormal vital signs
            vitals["bp_systolic"] = random.choice([
                random.randint(85, 95),
                random.randint(165, 185)
            ])
            vitals["bp_diastolic"] = random.randint(55, 65) if vitals["bp_systolic"] < 100 else random.randint(95, 110)
            vitals["heart_rate"] = random.choice([
                random.randint(45, 55),
                random.randint(110, 130)
            ])
            vitals["o2_saturation"] = random.randint(88, 92)
            vitals["respiratory_rate"] = random.randint(24, 32)
            vitals["temperature"] = round(random.uniform(35.5, 39.0), 1)

        elif esi_level == 3:
            # Slightly abnormal vital signs
            vitals["bp_systolic"] = random.randint(100, 160)
            vitals["bp_diastolic"] = random.randint(65, 95)
            vitals["heart_rate"] = random.randint(60, 110)
            vitals["o2_saturation"] = random.randint(93, 96)
            vitals["respiratory_rate"] = random.randint(18, 24)
            vitals["temperature"] = round(random.uniform(36.5, 38.5), 1)

        else:
            # Normal vital signs
            vitals["bp_systolic"] = random.randint(110, 140)
            vitals["bp_diastolic"] = random.randint(70, 85)
            vitals["heart_rate"] = random.randint(60, 90)
            vitals["o2_saturation"] = random.randint(96, 100)
            vitals["respiratory_rate"] = random.randint(12, 18)
            vitals["temperature"] = round(random.uniform(36.5, 37.5), 1)

        # Adjust for age
        if age < 10:
            vitals["heart_rate"] = min(180, vitals["heart_rate"] + 20)
            vitals["bp_systolic"] = max(70, vitals["bp_systolic"] - 20)

        return vitals

    def _generate_symptoms(self, esi_level: int) -> Dict:
        """Generate symptoms based on ESI level"""
        symptoms = {}

        if esi_level == 1:
            symptoms["pain_scale"] = random.randint(8, 10)
            symptoms["consciousness_level"] = random.choice(["Unresponsive", "Pain"])
            symptoms["bleeding"] = random.choice([True, False])
            symptoms["breathing_difficulty"] = True
            symptoms["trauma_indicator"] = random.choice([True, False])

        elif esi_level == 2:
            symptoms["pain_scale"] = random.randint(7, 10)
            symptoms["consciousness_level"] = random.choice(["Alert", "Voice"])
            symptoms["bleeding"] = random.random() < 0.3
            symptoms["breathing_difficulty"] = random.random() < 0.5
            symptoms["trauma_indicator"] = random.random() < 0.3

        elif esi_level == 3:
            symptoms["pain_scale"] = random.randint(4, 7)
            symptoms["consciousness_level"] = "Alert"
            symptoms["bleeding"] = random.random() < 0.2
            symptoms["breathing_difficulty"] = random.random() < 0.2
            symptoms["trauma_indicator"] = random.random() < 0.2

        elif esi_level == 4:
            symptoms["pain_scale"] = random.randint(2, 5)
            symptoms["consciousness_level"] = "Alert"
            symptoms["bleeding"] = random.random() < 0.1
            symptoms["breathing_difficulty"] = False
            symptoms["trauma_indicator"] = random.random() < 0.1

        else:
            symptoms["pain_scale"] = random.randint(0, 2)
            symptoms["consciousness_level"] = "Alert"
            symptoms["bleeding"] = False
            symptoms["breathing_difficulty"] = False
            symptoms["trauma_indicator"] = False

        return symptoms

    def _generate_medical_history(self, age: int) -> Dict:
        """Generate medical history based on age"""
        history = {}

        # Chronic conditions more likely with age
        num_conditions = 0
        if age > 60:
            num_conditions = random.randint(1, 4)
        elif age > 40:
            num_conditions = random.randint(0, 2)
        else:
            num_conditions = random.randint(0, 1)

        chronic_conditions = [
            "Diabetes", "Hypertension", "Heart Disease", "COPD",
            "Asthma", "Kidney Disease", "Cancer", "Arthritis"
        ]

        history["chronic_conditions"] = random.sample(
            chronic_conditions,
            min(num_conditions, len(chronic_conditions))
        )

        history["medications_count"] = num_conditions * random.randint(1, 3)

        # Allergies
        history["allergies"] = []
        if random.random() < 0.3:
            allergies = ["Penicillin", "Sulfa", "Latex", "Peanuts", "Shellfish"]
            history["allergies"] = random.sample(allergies, random.randint(1, 2))

        history["previous_admissions"] = random.randint(0, min(5, age // 10))

        return history

    def generate_dataset(self, n_samples: int = 1000) -> pd.DataFrame:
        """Generate a full dataset of synthetic patients"""
        patients = []

        # Generate with realistic ESI distribution
        esi_distribution = {
            1: int(n_samples * 0.02),
            2: int(n_samples * 0.08),
            3: int(n_samples * 0.35),
            4: int(n_samples * 0.40),
            5: int(n_samples * 0.15)
        }

        for esi_level, count in esi_distribution.items():
            for _ in range(count):
                patients.append(self.generate_patient(esi_level))

        # Shuffle the dataset
        random.shuffle(patients)

        return pd.DataFrame(patients)

    def generate_mass_casualty_event(self, n_patients: int = 50) -> List[Dict]:
        """Generate data for a mass casualty event scenario"""
        patients = []

        # Distribution for mass casualty
        distribution = {
            1: int(n_patients * 0.10),  # Critical
            2: int(n_patients * 0.20),  # Emergent
            3: int(n_patients * 0.30),  # Urgent
            4: int(n_patients * 0.30),  # Less urgent
            5: int(n_patients * 0.10),  # Walking wounded
        }

        base_time = datetime.now()

        for esi_level, count in distribution.items():
            for i in range(count):
                patient = self.generate_patient(esi_level)
                # All arrive within 30 minutes
                patient["arrival_time"] = base_time + timedelta(minutes=random.randint(0, 30))
                patient["mass_casualty_patient"] = True
                patient["incident"] = "Bus accident - Highway 101"
                patients.append(patient)

        return patients


if __name__ == "__main__":
    # Generate training data
    generator = SyntheticPatientGenerator()

    # Generate training dataset
    train_df = generator.generate_dataset(n_samples=5000)
    train_df.to_csv("../../data/train_patients.csv", index=False)

    # Generate validation dataset
    val_df = generator.generate_dataset(n_samples=1000)
    val_df.to_csv("../../data/val_patients.csv", index=False)

    # Generate mass casualty scenario
    mass_casualty = generator.generate_mass_casualty_event(50)
    pd.DataFrame(mass_casualty).to_csv("../../data/mass_casualty_scenario.csv", index=False)

    print(f"Generated {len(train_df)} training samples")
    print(f"Generated {len(val_df)} validation samples")
    print(f"Generated {len(mass_casualty)} mass casualty patients")
    print("\nESI Level Distribution in Training Set:")
    print(train_df["true_esi_level"].value_counts().sort_index())