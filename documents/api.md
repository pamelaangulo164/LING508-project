# 📘 Flask API Documentation

This file documents the available endpoints in the Flask API for the Bilingual Medical Dictionary project.

## 🔍 `/api/v1/lookup` [GET]
Looks up an English term and returns its dictionary entry.

### Request
```
GET /api/v1/lookup?english=fever
```

### Query Parameters
- `english` (string, required): The English word to look up.

### Example
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/lookup?english=fever"
```

### Successful Response (200)
```json
{
  "term": "fever",
  "pos": "noun",
  "term_id": "123",
  "meanings": [
    {
      "meaning_id": "456",
      "description": "A medical condition with elevated body temperature",
      "spanish_terms": [
        {"term_id": "789", "term": "fiebre", "gender": "feminine"}
      ],
      "examples": [
        {"example_id": "321", "language": "en", "text": "She has a high fever."}
      ]
    }
  ]
}
```

### Error Response (404)
```json
{ "error": "not found" }
```

---

## ➕ `/api/v1/add` [POST]
Adds a new entry to the bilingual dictionary.

### Request
```
POST /api/v1/add
Content-Type: application/json
```

### Body Parameters (JSON)
```json
{
  "lemma": "fever",
  "pos": "noun",
  "meaning_desc": "A medical condition with elevated body temperature",
  "spanish_term": "fiebre",
  "gender": "feminine",
  "examples": [
    ["en", "He has a fever."],
    ["es", "Él tiene fiebre."]
  ]
}
```

### Example
```bash
curl -X POST http://127.0.0.1:8000/api/v1/add   -H "Content-Type: application/json"   -d '{
        "lemma": "fever",
        "pos": "noun",
        "meaning_desc": "A medical condition with elevated body temperature",
        "spanish_term": "fiebre",
        "gender": "feminine",
        "examples": [["en", "He has a fever."], ["es", "Él tiene fiebre."]]
      }'
```

### Successful Response (200)
Returns the added entry.
```json
{
  "term": "fever",
  "pos": "noun",
  "term_id": "...",
  "meanings": [...]
}
```

### Error Response (400)
```json
{ "error": "invalid payload" }
```

---

## 📘 `/api/v1/english-lesson` [GET]
Returns a basic English–Spanish lesson with static sample data.

### Request
```
GET /api/v1/english-lesson
```

### Example
```bash
curl -X GET http://127.0.0.1:8000/api/v1/english-lesson
```

### Successful Response (200)
```json
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

## ❤️ `/api/v1/health` [GET]
Health check endpoint.

### Example
```bash
curl -X GET http://127.0.0.1:8000/api/v1/health
```

### Response (200)
```json
{ "status": "ok" }
```
