
from database import load_inventory

# Simulated daily medicine consumption
daily_consumption = {
    "Paracetamol": 10,
    "Insulin": 5,
    "Amoxicillin": 4
}


def predict_shortages():
    predictions = []

    hospitals = load_inventory()

    for hospital, medicines in hospitals.items():
        for medicine, quantity in medicines.items():

            daily_use = daily_consumption[medicine]
            days_left = quantity / daily_use

            if days_left <= 5:
                risk = "HIGH"
            elif days_left <= 10:
                risk = "MEDIUM"
            else:
                risk = "LOW"

            predictions.append({
                "hospital": hospital,
                "medicine": medicine,
                "days_left": round(days_left, 1),
                "risk": risk
            })

    return predictions


if __name__ == "__main__":
    predictions = predict_shortages()

    print("SMART MED-AGENT | SHORTAGE PREDICTION")

    for prediction in predictions:
        print(
            f"{prediction['hospital']} | "
            f"{prediction['medicine']} | "
            f"{prediction['days_left']} days left | "
            f"Risk: {prediction['risk']}"
        )
