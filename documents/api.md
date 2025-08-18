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

**cURL:**
curl "http://127.0.0.1:8000/api/v1/lookup?english=lesion"

### 2) POST `/add`

Creates a new entry: one English term, one meaning, one Spanish term, plus examples.

**Request body (JSON)**
- `lemma` (string) – English term, e.g. `"bruise"`
- `pos` (string) – one of: `"noun" | "verb" | "adj" | "adv"`
- `meaning` (string) – definition/description
- `spanish_term` (string) – Spanish equivalent
- `gender` (string) – `"m" | "f" | "n"`
- `examples` (array of `[language, text]`) – optional

**Example**
```json
{
  "lemma": "contusion",
  "pos": "noun",
  "meaning": "Injury causing discoloration of the skin",
  "spanish_term": "contusión",
  "gender": "f",
  "examples": [["en","He had a contusion."], ["es","Tuvo una contusión."]]
