from __future__ import annotations
from typing import Iterable, Optional, Dict, Any
from models import EnglishTerm, Meaning, SpanishTerm, Example, PartOfSpeech, Gender
from db.repository import Repository

class DictionaryService:
    """Service layer: implements use cases with repo dependency injected."""

    def __init__(self, repo: Repository):
        self.repo = repo

    # Use case 1: lookup an English term and return the full entry
    def lookup_english(self, lemma: str) -> Optional[Dict[str, Any]]:
        if not lemma or not lemma.strip():
            raise ValueError("lemma is required")
        et = self.repo.load_english_term(lemma.strip())
        return None if not et else self._to_dict(et)

    # Use case 2: add a new entry (English term + 1 meaning + 1 Spanish term + examples)
    def add_entry(
        self,
        lemma: str,
        pos: PartOfSpeech,
        meaning_desc: str,
        spanish_term: str,
        gender: Gender,
        examples: Iterable[tuple[str, str]] = (),
    ) -> Dict[str, Any]:
        if not lemma.strip() or not meaning_desc.strip() or not spanish_term.strip():
            raise ValueError("lemma, meaning_desc, spanish_term required")

        et = EnglishTerm(term=lemma.strip(), pos=pos)
        m  = Meaning(description=meaning_desc.strip(), english_term=et)
        st = SpanishTerm(term=spanish_term.strip(), gender=gender, meaning=m)

        ex_objs: list[Example] = []
        for (lang, text) in examples:
            lang = lang.lower().strip()
            if lang not in {"en", "es"}:
                raise ValueError("example language must be 'en' or 'es'")
            ex_objs.append(Example(language=lang, text=text, meaning=m))

        # Persist through repository (no SQL here)
        self.repo.insert_english_term(et)
        self.repo.insert_meaning(m)
        self.repo.link_meaning_english(m.meaning_id, et.term_id)
        self.repo.insert_spanish_term(st)
        self.repo.link_meaning_spanish(m.meaning_id, st.term_id)
        for ex in ex_objs:
            self.repo.insert_example(ex)

        return self._to_dict(et)

    # ---- helpers ----
    def _to_dict(self, et: EnglishTerm) -> Dict[str, Any]:
        return {
            "english_term": et.term,
            "pos": et.pos.value,
            "meanings": [
                {
                    "description": m.description,
                    "spanish_terms": [
                        {"term": st.term, "gender": st.gender.value} for st in m.spanish_terms
                    ],
                    "examples": [{"language": ex.language, "text": ex.text} for ex in m.examples],
                }
                for m in et.meanings
            ],
        }
