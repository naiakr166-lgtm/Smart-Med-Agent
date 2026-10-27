
from flask import Flask, jsonify, request, render_template

from requests import (
    create_request,
    generate_ai_requests,
    get_requests,
    update_request_status
)

from inventory_agent import check_inventory
from prediction_agent import predict_shortages
from coordination_agent import coordinate_supplies
from database import get_connection, init_database, save_initial_inventory
from data import hospitals

app = Flask(__name__)

init_database()
save_initial_inventory(hospitals)

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/inventory")
def inventory():
    return jsonify(check_inventory())


@app.route("/predictions")
def predictions():
    return jsonify(predict_shortages())


@app.route("/coordination")
def coordination():
    return jsonify(coordinate_supplies())


@app.route("/requests", methods=["GET"])
def list_requests():
    return jsonify(get_requests())


@app.route("/requests/manual", methods=["POST"])
def manual_request():
    data = request.get_json(silent=True) or {}

    result = create_request(
        data.get("hospital"),
        data.get("medicine"),
        data.get("quantity"),
        "Manual"
    )

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result), 201


@app.route("/requests/ai", methods=["POST"])
def ai_requests():
    generate_ai_requests()
    return jsonify(get_requests())


@app.route("/requests/<int:request_id>/status", methods=["POST"])
def change_request_status(request_id):
    data = request.get_json(silent=True) or {}

    action = data.get("action")

    result = update_request_status(request_id, action)

    if "error" in result:
        return jsonify(result), 400

    return jsonify(result), 200


@app.route("/transfers/history", methods=["GET"])
def get_transfer_history():
    connection = get_connection()

    try:
        rows = connection.execute("""
            SELECT id, from_hospital, to_hospital,
                   medicine, quantity, status
            FROM transfer_history
            ORDER BY id DESC
        """).fetchall()

        transfers = []

        for row in rows:
            transfers.append({
                "id": row["id"],
                "from": row["from_hospital"],
                "to": row["to_hospital"],
                "medicine": row["medicine"],
                "quantity": row["quantity"],
                "status": row["status"]
            })

        return jsonify(transfers)

    finally:
        connection.close()


if __name__ == "__main__":
    app.run(debug=True, port=5001)
