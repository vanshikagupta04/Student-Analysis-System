import pandas as pd
from backend.database import SessionLocal
from backend.models import Performance
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
import joblib
from sklearn.metrics import accuracy_score

# -------------------------
# 1. Load Data
# -------------------------
db = SessionLocal()
data = db.query(Performance).all()

if len(data) == 0:
    raise Exception("No data found in database. Add performance records first.")

df = pd.DataFrame([{
    "marks": d.marks,
    "subject": d.subject,
    "exam_type": d.exam_type
} for d in data])

# -------------------------
# 2. Encoding (IMPORTANT)
# -------------------------
subject_encoder = LabelEncoder()
exam_encoder = LabelEncoder()

df["subject_enc"] = subject_encoder.fit_transform(df["subject"])
df["exam_enc"] = exam_encoder.fit_transform(df["exam_type"])

# -------------------------
# 3. Target
# -------------------------
df["target"] = df["marks"].apply(lambda x: 1 if x >= 40 else 0)

# -------------------------
# 4. Features
# -------------------------
X = df[["marks", "subject_enc", "exam_enc"]]
y = df["target"]

# -------------------------
# 5. Train-Test Split
# -------------------------
if len(df) < 5:
    print("⚠️ Small dataset: training without split")
    X_train, y_train = X, y
else:
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

# -------------------------
# 6. Train Model
# -------------------------
model = RandomForestClassifier(random_state=42)
model.fit(X_train, y_train)

# -------------------------
# 7. Save Everything
# -------------------------
joblib.dump(model, "backend/model.pkl")
joblib.dump(subject_encoder, "backend/subject_encoder.pkl")
joblib.dump(exam_encoder, "backend/exam_encoder.pkl")

print("✅ Model + encoders saved successfully")
print(f"📊 Training samples: {len(df)}")

if len(df) >= 5:
    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)
    print(f"✅ Model Accuracy: {round(acc, 3)}")

import json

metrics = {
    "accuracy": float(acc) if len(df) >= 5 else None,
    "samples": len(df)
}

with open("backend/model_metrics.json", "w") as f:
    json.dump(metrics, f)

