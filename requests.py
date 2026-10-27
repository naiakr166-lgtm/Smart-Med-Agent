
from data import minimum_stock
from database import (
    get_connection,
    load_inventory,
    approve_request_transaction
)
from coordination_agent import execute_transfer


def create_request(hospital, medicine, quantity, source="Manual"):
    hospitals = load_inventory()

    if hospital not in hospitals:
        return {"error": "Hospital not found"}

    if medicine not in minimum_stock:
        return {"error": "Medicine not found"}

    try:
        quantity = int(quantity)
    except (ValueError, TypeError):
        return {"error": "Invalid quantity"}

    if quantity <= 0:
        return {"error": "Quantity must be positive"}

    if source not in ("Manual", "AI"):
        return {"error": "Invalid request source"}

    connection = get_connection()

    try:
        cursor = connection.execute("""
            INSERT INTO medicine_requests
            (hospital, medicine, quantity, source, status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            hospital,
            medicine,
            quantity,
            source,
            "Pending Approval"
        ))

        connection.commit()

        return {
            "id": cursor.lastrowid,
            "hospital": hospital,
            "medicine": medicine,
            "quantity": quantity,
            "source": source,
            "status": "Pending Approval"
        }

    finally:
        connection.close()


def get_requests():
    connection = get_connection()

    try:
        rows = connection.execute("""
            SELECT id, hospital, medicine, quantity,
                   source, status, supplied_by
            FROM medicine_requests
            ORDER BY id
        """).fetchall()

        return [dict(row) for row in rows]

    finally:
        connection.close()


def generate_ai_requests():
    hospitals = load_inventory()
    existing_requests = get_requests()

    for hospital, medicines in hospitals.items():
        for medicine, stock in medicines.items():
            minimum = minimum_stock[medicine]

            if stock < minimum:
                existing = any(
                    r["hospital"] == hospital
                    and r["medicine"] == medicine
                    and r["source"] == "AI"
                    and r["status"] == "Pending Approval"
                    for r in existing_requests
                )

                if not existing:
                    new_request = create_request(
                        hospital,
                        medicine,
                        minimum - stock,
                        "AI"
                    )

                    if "error" not in new_request:
                        existing_requests.append(new_request)

    return get_requests()


def update_request_status(request_id, action):
    try:
        request_id = int(request_id)
    except (ValueError, TypeError):
        return {"error": "Invalid request ID"}

    if action not in ("Approve", "Reject"):
        return {"error": "Invalid action"}

    if action == "Approve":
        return approve_request_transaction(
            request_id,
            minimum_stock
        )

    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")

        row = connection.execute("""
            SELECT id, hospital, medicine, quantity,
                   source, status, supplied_by
            FROM medicine_requests
            WHERE id = ?
        """, (request_id,)).fetchone()

        if row is None:
            connection.rollback()
            return {"error": "Request not found"}

        req = dict(row)

        if req["status"] != "Pending Approval":
            connection.rollback()
            return {"error": "Request already processed"}

        connection.execute("""
            UPDATE medicine_requests
            SET status = 'Rejected'
            WHERE id = ?
        """, (request_id,))

        connection.commit()

        req["status"] = "Rejected"
        return req

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()
