import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

# Create a synthetic dataset for mental health risk prediction
def create_synthetic_data():
    np.random.seed(42)
    n_samples = 1000
    
    data = {
        'age': np.random.randint(18, 65, n_samples),
        'gender': np.random.choice([0, 1, 2], n_samples),  # 0: Male, 1: Female, 2: Other
        'family_history': np.random.choice([0, 1], n_samples), # 0: No, 1: Yes
        'work_interference': np.random.choice([0, 1, 2, 3], n_samples), # 0: Never, 1: Rarely, 2: Sometimes, 3: Often
        'benefits': np.random.choice([0, 1, 2], n_samples), # 0: No, 1: Yes, 2: Don't know
        'care_options': np.random.choice([0, 1, 2], n_samples), # 0: No, 1: Yes, 2: Not sure
    }
    
    df = pd.DataFrame(data)
    
    # Simple rule for risk: higher risk if family history, work interference, or lack of benefits
    # This is just to make the synthetic data somewhat predictable
    risk_score = (
        df['family_history'] * 2 + 
        df['work_interference'] * 1.5 - 
        df['benefits'] * 0.5 + 
        np.random.normal(0, 1, n_samples)
    )
    
    df['risk'] = (risk_score > 2).astype(int)
    return df

def train():
    print("Generating synthetic data...")
    df = create_synthetic_data()
    
    X = df.drop('risk', axis=1)
    y = df['risk']
    
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    print("Training model...")
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    accuracy = model.score(X_test, y_test)
    print(f"Model accuracy: {accuracy:.2f}")
    
    # Save the model
    if not os.path.exists('models'):
        os.makedirs('models')
    
    joblib.dump(model, 'models/mental_health_model.pkl')
    print("Model saved to models/mental_health_model.pkl")

if __name__ == "__main__":
    train()
