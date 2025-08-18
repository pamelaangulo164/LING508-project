# Bilingual Medical Dictionary — API Documentation

**Base URL:** `http://127.0.0.1:8000/api/v1`  
**Authentication:** none (local development)  
**Content-Type:** `application/json; charset=utf-8`

---

## Endpoints

### 1) GET `/lookup`

Looks up an existing English lemma and returns its entry.

**Query parameters**
- `english` (string, required): the English lemma to look up.

**Responses**

- **200 OK**
  ```json
  {
    "english_term": "lesion",
    "pos": "noun",
    "meanings": [
      {
        "description": "Pathological change; abnormal tissue",
        "spanish_terms": [
          { "term": "lesión", "gender": "f" }
        ],
        "examples": [
          { "language": "en", "text": "The MRI showed a brain lesion." },
          { "language": "es", "text": "La resonancia mostró una lesión cerebral." }
        ]
      }
    ]
  }
  
**400 Bad Request**
{"error":"missing ?english=..."}

**404 Not Found**
{"error":"not found"}
