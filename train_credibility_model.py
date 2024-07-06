import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib

# Mock data - replace with your actual dataset
data = {
    'url': ['https://example1.com', 'https://example2.com', 'https://example3.com'],
    'label': [1, 0, 1]
}
df = pd.DataFrame(data)

# Feature extraction - replace with your actual feature extraction
df['feature'] = df['url'].apply(lambda x: len(x))

X = df[['feature']]
y = df['label']

print("Splitting data into training and testing sets...")
# Split data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

print("Training the Random Forest model...")
# Train a Random Forest model
model = RandomForestClassifier()
model.fit(X_train, y_train)

print("Model trained successfully.")
# Save the model
joblib.dump(model, 'credibility_model.pkl')
print("Model saved as credibility_model.pkl.")
