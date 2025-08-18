# Bilingual Medical Dictionary – API

**Base URL:** `http://127.0.0.1:8000/api/v1`  
**Auth:** none (local dev)  
**Content-Type:** `application/json; charset=utf-8`

---

## Endpoints

### GET `/lookup`
Lookup an existing English lemma.

**Query params**
- `english` (string, required): the English lemma to look up.

**Response 200**
```json
{
  "english_term": "lesion",
  "pos": "noun",
  "meanings": [
    {
      "description": "Pathological change; abnormal tissue",
      "spanish_terms": [
        {"term": "lesión", "gender": "f"}
      ],
      "examples": [
        {"language": "en", "text": "The MRI showed a brain lesion."},
        {"language": "es", "text": "La resonancia mostró una lesión cerebral."}
      ]
    }
  ]
}
