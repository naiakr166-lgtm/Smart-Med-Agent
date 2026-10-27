
import sqlite3

DB_NAME = "smart_med.db"


def get_connection():
    connection = sqlite3.connect(DB_NAME)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS inventory (
            hospital TEXT NOT NULL,
            medicine TEXT NOT NULL,
            stock INTEGER NOT NULL,
            PRIMARY KEY (hospital, medicine)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS medicine_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hospital TEXT NOT NULL,
            medicine TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            source TEXT NOT NULL,
            status TEXT NOT NULL,
            supplied_by TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transfer_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            from_hospital TEXT NOT NULL,
            to_hospital TEXT NOT NULL,
            medicine TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            status TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def save_initial_inventory(hospitals):
    connection = get_connection()
    cursor = connection.cursor()

    for hospital, medicines in hospitals.items():
        for medicine, stock in medicines.items():
            cursor.execute("""
                INSERT OR IGNORE INTO inventory
                (hospital, medicine, stock)
                VALUES (?, ?, ?)
            """, (hospital, medicine, stock))

    connection.commit()
    connection.close()
    
def load_inventory():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT hospital, medicine, stock FROM inventory"
    )

    rows = cursor.fetchall()
    connection.close()

    hospitals = {}

    for row in rows:
        hospital = row["hospital"]
        medicine = row["medicine"]
        stock = row["stock"]

        if hospital not in hospitals:
            hospitals[hospital] = {}

        hospitals[hospital][medicine] = stock

    return hospitals


def save_transfer(from_hospital, to_hospital, medicine, quantity, minimum):
    if from_hospital == to_hospital:
        return {"error": "Hospitals must be different"}

    if type(quantity) is not int or quantity <= 0:
        return {"error": "Invalid quantity"}

    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")

        source = connection.execute("""
            SELECT stock FROM inventory
            WHERE hospital = ? AND medicine = ?
        """, (from_hospital, medicine)).fetchone()

        destination = connection.execute("""
            SELECT stock FROM inventory
            WHERE hospital = ? AND medicine = ?
        """, (to_hospital, medicine)).fetchone()

        if source is None or destination is None:
            connection.rollback()
            return {"error": "Hospital or medicine not found"}

        if source["stock"] - quantity < minimum:
            connection.rollback()
            return {"error": "Insufficient surplus stock"}

        connection.execute("""
            UPDATE inventory
            SET stock = stock - ?
            WHERE hospital = ? AND medicine = ?
        """, (quantity, from_hospital, medicine))

        connection.execute("""
            UPDATE inventory
            SET stock = stock + ?
            WHERE hospital = ? AND medicine = ?
        """, (quantity, to_hospital, medicine))

        cursor = connection.execute("""
            INSERT INTO transfer_history
            (from_hospital, to_hospital, medicine, quantity, status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            from_hospital,
            to_hospital,
            medicine,
            quantity,
            "Transferred"
        ))

        transfer = {
            "id": cursor.lastrowid,
            "from": from_hospital,
            "to": to_hospital,
            "medicine": medicine,
            "quantity": quantity,
            "status": "Transferred"
        }

        connection.commit()
        return transfer

    except sqlite3.Error:
        connection.rollback()
        return {"error": "Database transfer failed"}

    finally:
        connection.close()

def approve_request_transaction(request_id, minimum_stock):
    connection = get_connection()

    try:
        connection.execute("BEGIN IMMEDIATE")

        row = connection.execute("""
            SELECT id, hospital, medicine, quantity, source,
                   status, supplied_by
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

        receiving = req["hospital"]
        medicine = req["medicine"]
        quantity = req["quantity"]

        if medicine not in minimum_stock:
            connection.rollback()
            return {"error": "Medicine not found"}

        destination = connection.execute("""
            SELECT stock FROM inventory
            WHERE hospital = ? AND medicine = ?
        """, (receiving, medicine)).fetchone()

        if destination is None:
            connection.rollback()
            return {"error": "Destination inventory not found"}

        suppliers = connection.execute("""
            SELECT hospital, stock FROM inventory
            WHERE medicine = ? AND hospital != ?
            ORDER BY hospital
        """, (medicine, receiving)).fetchall()

        for supplier in suppliers:
            supplying = supplier["hospital"]
            surplus = supplier["stock"] - minimum_stock[medicine]

            if surplus < quantity:
                continue

            connection.execute("""
                UPDATE inventory
                SET stock = stock - ?
                WHERE hospital = ? AND medicine = ?
            """, (quantity, supplying, medicine))

            connection.execute("""
                UPDATE inventory
                SET stock = stock + ?
                WHERE hospital = ? AND medicine = ?
            """, (quantity, receiving, medicine))

            cursor = connection.execute("""
                INSERT INTO transfer_history
                (from_hospital, to_hospital, medicine, quantity, status)
                VALUES (?, ?, ?, ?, 'Transferred')
            """, (supplying, receiving, medicine, quantity))

            connection.execute("""
                UPDATE medicine_requests
                SET status = 'Approved', supplied_by = ?
                WHERE id = ?
            """, (supplying, request_id))

            connection.commit()

            req["status"] = "Approved"
            req["supplied_by"] = supplying
            req["transfer"] = {
                "id": cursor.lastrowid,
                "from": supplying,
                "to": receiving,
                "medicine": medicine,
                "quantity": quantity,
                "status": "Transferred"
            }

            return req

        connection.rollback()
        return {"error": "No hospital has enough surplus stock"}

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()

if __name__ == "__main__":
    from data import hospitals

    init_database()
    save_initial_inventory(hospitals)

    print("Smart Med-Agent database initialized successfully!")
    print("Hospital inventory saved successfully!")
