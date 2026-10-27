
from inventory_agent import check_inventory
from prediction_agent import predict_shortages
from coordination_agent import coordinate_supplies


def run_system():
    print("=" * 50)
    print("SMART MED-AGENT | MULTI-AGENT SYSTEM")
    print("=" * 50)

    # Agent 1: Inventory Monitoring
    print("\n[AGENT 1] INVENTORY MONITORING")

    alerts = check_inventory()

    for alert in alerts:
        print(
            f"ALERT: {alert['hospital']} | "
            f"{alert['medicine']} | "
            f"Shortage: {alert['shortage']} units"
        )

    # Agent 2: Shortage Prediction
    print("\n[AGENT 2] SHORTAGE PREDICTION")

    predictions = predict_shortages()

    for prediction in predictions:
        if prediction["risk"] == "HIGH":
            print(
                f"HIGH RISK: {prediction['hospital']} | "
                f"{prediction['medicine']} | "
                f"{prediction['days_left']} days left"
            )

    # Agent 3: Supply Coordination
    print("\n[AGENT 3] SUPPLY COORDINATION")

    recommendations = coordinate_supplies()

    for rec in recommendations:
        print(
            f"TRANSFER {rec['quantity']} "
            f"{rec['medicine']} units "
            f"FROM {rec['from']} "
            f"TO {rec['to']} "
            f"| {rec['status']}"
        )

    print("\nSYSTEM ANALYSIS COMPLETED")


if __name__ == "__main__":
    run_system()
