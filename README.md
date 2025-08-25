# Bilingual Medical Dictionary API

This project is a bilingual medical dictionary designed for interpreters and healthcare professionals, supporting English-to-Spanish terminology with example sentences, part of speech information, and more.

---

## Getting Started

### Requirements

- **Python 3.11+**
- **Docker** and **Docker Compose** (for database)
- `pip` for installing Python dependencies

---

### Run with Docker

```
docker-compose up --build
```

This launches a MySQL database container.

---

### Run the Flask API Server

```
$env:PYTHONPATH="."
$env:FLASK_APP="api.app"
python -m flask run --port 8000
```

This runs the API at: [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## API Documentation

### `/api/v1/health`  
**Method**: `GET`  
**Description**: Health check endpoint  
**Response**:
```
{ "status": "ok" }
```

---

### `/api/v1/lookup?english=fever`  
**Method**: `GET`  
**Query Param**:  
- `english` – the English word to look up

**Example**:
```
curl http://127.0.0.1:8000/api/v1/lookup?english=fever
```

**Success Response**:
```
{
  "term": "fever",
  "pos": "noun",
  "term_id": "1",
  "meanings": [...]
}
```

**Error**:
```
{ "error": "not found" }
```

---

### `/api/v1/add`  
**Method**: `POST`  
**Content-Type**: `application/json`  
**Payload**:
```
{
  "lemma": "fever",
  "pos": "noun",
  "meaning_desc": "An elevated body temperature.",
  "spanish_term": "fiebre",
  "gender": "feminine",
  "examples": [
    ["en", "He has a fever."],
    ["es", "Él tiene fiebre."]
  ]
}
```

**Example curl**:
```
curl -X POST http://127.0.0.1:8000/api/v1/add   -H "Content-Type: application/json"   -d '{...}'
```

**Success Response**:
```
{ "term": "fever", ... }
```

**Error Response**:
```
{ "error": "invalid payload" }
```

---

### `/api/v1/english-lesson`  
**Method**: `GET`  
**Description**: Returns a small English lesson of common medical terms  
**Response**:
```
{
  "lesson_title": "Basic Medical Terms",
  "terms": [
    {"english": "fever", "spanish": "fiebre", "pos": "noun"},
    {"english": "cough", "spanish": "tos", "pos": "noun"},
    {"english": "headache", "spanish": "dolor de cabeza", "pos": "noun"}
  ]
}
```

---

## Project Structure

```
/api
  app.py         ← Flask app and routes
/services
  service.py     ← Business logic
/models          ← Data classes (EnglishTerm, Meaning, etc.)
/db
  repository.py  ← DB access layer
/docs
  api.md         ← API documentation
  use_case.md    ← Use case description
  uml.md         ← UML diagrams
```

---

## Example Use Case

A medical professional or student wants to look up the word "fever" to see its Spanish translation and example sentences. Learning what part of speech the word belongs to and gender categorization is also necessary for correct use.

```
curl http://127.0.0.1:8000/api/v1/lookup?english=fever
```
