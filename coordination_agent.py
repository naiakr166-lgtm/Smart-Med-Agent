
from data import minimum_stock
from database import load_inventory, save_transfer
from inventory_agent import check_inventory

# Store completed medicine transfers
transfer_history = []


def coordinate_supplies():
    hospitals = load_inventory()
    recommendations = []
    alerts = check_inventory()

    for alert in alerts:
        receiving_hospital = alert["hospital"]
        medicine = alert["medicine"]
        shortage = alert["shortage"]

        for supplying_hospital, stock in hospitals.items():

            if supplying_hospital == receiving_hospital:
                continue

            available = stock.get(medicine, 0)
            minimum = minimum_stock[medicine]
            surplus = max(0, available - minimum)

            if surplus > 0 and shortage > 0:
                transfer_amount = min(surplus, shortage)

                recommendations.append({
                    "from": supplying_hospital,
                    "to": receiving_hospital,
                    "medicine": medicine,
                    "quantity": transfer_amount,
                    "status": "Pending Approval"
                })

                shortage -= transfer_amount

            if shortage == 0:
                break

    return recommendations



def execute_transfer(from_hospital, to_hospital, medicine, quantity):

    if medicine not in minimum_stock:
        return {"error": "Medicine not found"}

    if type(quantity) is not int or quantity <= 0:
        return {"error": "Invalid quantity"}

    minimum = minimum_stock[medicine]

    transfer = save_transfer(
        from_hospital,
        to_hospital,
        medicine,
        quantity,
        minimum
    )

    if "error" not in transfer:
        transfer_history.append(transfer)

    return transfer


if __name__ == "__main__":
    recommendations = coordinate_supplies()

    print("SMART MED-AGENT | SUPPLY COORDINATION")

    for rec in recommendations:
        print(
            f"TRANSFER {rec['quantity']} "
            f"{rec['medicine']} units "
            f"FROM {rec['from']} "
            f"TO {rec['to']} "
            f"| {rec['status']}"
        )
