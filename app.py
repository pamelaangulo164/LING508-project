from flask import Flask, jsonify, request
from services.service import DictionaryService

def create_app():
    app = Flask(__name__)
    service = DictionaryService()

    @app.route("/api/v1/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok"})

    @app.route("/api/v1/lookup", methods=["GET"])
    def lookup():
        english = request.args.get("english")
        if not english:
            return jsonify({"error": "missing ?english=..."}), 400
        entry = service.lookup(english)
        if entry:
            return jsonify(entry)
        else:
            return jsonify({"error": "not found"}), 404

    @app.route("/api/v1/add", methods=["POST"])
    def add():
        data = request.get_json()
        required_fields = ["english", "spanish", "pos", "category"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "invalid payload"}), 400
        success = service.add_entry(
            data["english"],
            data["spanish"],
            data["pos"],
            data["category"]
        )
        return jsonify({"result": "ok" if success else "error"})

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=8000)
