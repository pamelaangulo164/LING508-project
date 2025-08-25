from flask import Flask, jsonify, request
from services.service import DictionaryService
from db.repository import Repository

def create_app():
    app = Flask(__name__)
    repo = Repository()
    service = DictionaryService(repo)

    @app.route("/api/v1/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok"})

    @app.route("/api/v1/lookup", methods=["GET"])
    def lookup():
        english = request.args.get("english")
        if not english:
            return jsonify({"error": "missing ?english=..."})
        entry = service.lookup_english_as_dict(english)
        if entry:
            return jsonify(entry)
        else:
            return jsonify({"error": "not found"}), 404

    @app.route("/api/v1/add", methods=["POST"])
    def add():
        data = request.get_json()
        required_fields = ["lemma", "pos", "meaning_desc", "spanish_term", "gender"]
        if not all(field in data for field in required_fields):
            return jsonify({"error": "invalid payload"}), 400
        try:
            entry = service.add_entry_as_dict(
                lemma=data["lemma"],
                pos=data["pos"],
                meaning_desc=data["meaning_desc"],
                spanish_term=data["spanish_term"],
                gender=data["gender"],
                examples=data.get("examples", [])
            )
            return jsonify(entry)
        except Exception as e:
            return jsonify({"error": str(e)}), 500

    @app.route("/api/v1/english-lesson", methods=["GET"])
    def get_english_lesson():
        try:
            lesson = service.get_english_lesson()
            return jsonify(lesson)
        except Exception as e:
            print("Error:", e)
            return jsonify({"error": "server error"}), 500

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, port=8000)
