
from data import minimum_stock
from database import load_inventory


def check_inventory():
    alerts = []

    hospitals = load_inventory()

    for hospital, medicines in hospitals.items():
        for medicine, quantity in medicines.items():

            minimum = minimum_stock[medicine]

            if quantity < minimum:
                alerts.append({
                    "hospital": hospital,
                    "medicine": medicine,
                    "current_stock": quantity,
                    "minimum_stock": minimum,
                    "shortage": minimum - quantity
                })

    return alerts


if __name__ == "__main__":
    alerts = check_inventory()

    print("SMART MED-AGENT | INVENTORY MONITORING")

    for alert in alerts:
        print(
            f"ALERT: {alert['hospital']} "
            f"has low {alert['medicine']} stock "
            f"({alert['current_stock']} units)"
        )
