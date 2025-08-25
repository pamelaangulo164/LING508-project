from __future__ import annotations

from typing import Iterable, Optional, Dict, Any
from models import (
    EnglishTerm,
    Meaning,
    SpanishTerm,
    Example,
    PartOfSpeech,
    Gender,
)
from db.repository import Repository


class DictionaryService:
    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    def lookup_english(self, lemma: str) -> Optional[EnglishTerm]:
        lemma = (lemma or "").strip()
        if not lemma:
            raise ValueError("lemma is required")
        return self.repo.load_english_term(lemma)

    def add_entry(
        self,
        lemma: str,
        pos: PartOfSpeech,
        meaning_desc: str,
        spanish_term: str,
        gender: Gender,
        examples: Iterable[tuple[str, str]] = (),
    ) -> EnglishTerm:
        if not (lemma and lemma.strip()):
            raise ValueError("lemma is required")
        if not (meaning_desc and meaning_desc.strip()):
            raise ValueError("meaning_desc is required")
        if not (spanish_term and spanish_term.strip()):
            raise ValueError("spanish_term is required")

        et = EnglishTerm(term=lemma.strip(), pos=pos)
        m = Meaning(description=meaning_desc.strip(), english_term=et)
        st = SpanishTerm(term=spanish_term.strip(), gender=gender, meaning=m)
        ex_objs = [
            Example(language=lang.strip(), text=text.strip(), meaning=m)
            for (lang, text) in examples
            if lang and text and lang.strip() and text.strip()
        ]

        self.repo.persist_entry_graph(et, m, st, ex_objs)
        reloaded = self.repo.load_english_term(et.term)
        return reloaded or et

    def serialize_entry(self, et: EnglishTerm) -> Dict[str, Any]:
        return {
            "term": et.term,
            "pos": et.pos.value,
            "term_id": str(et.term_id),
            "meanings": [
                {
                    "meaning_id": str(m.meaning_id),
                    "description": m.description,
                    "spanish_terms": [
                        {
                            "term_id": str(st.term_id),
                            "term": st.term,
                            "gender": st.gender.value,
                        }
                        for st in m.spanish_terms
                    ],
                    "examples": [
                        {
                            "example_id": str(ex.example_id),
                            "language": ex.language,
                            "text": ex.text,
                        }
                        for ex in m.examples
                    ],
                }
                for m in et.meanings
            ],
        }

    def lookup_english_as_dict(self, lemma: str) -> Optional[Dict[str, Any]]:
        et = self.lookup_english(lemma)
        return self.serialize_entry(et) if et else None

    def add_entry_as_dict(
        self,
        lemma: str,
        pos: PartOfSpeech,
        meaning_desc: str,
        spanish_term: str,
        gender: Gender,
        examples: Iterable[tuple[str, str]] = (),
    ) -> Dict[str, Any]:
        et = self.add_entry(lemma, pos, meaning_desc, spanish_term, gender, examples)
        return self.serialize_entry(et)

    def get_english_lesson(self) -> dict:
        return {
        "lesson_title": "Basic Medical Terms",
        "terms": [
            {"english": "fever", "spanish": "fiebre", "pos": "noun"},
            {"english": "cough", "spanish": "tos", "pos": "noun"},
            {"english": "headache", "spanish": "dolor de cabeza", "pos": "noun"},
            ]
        }
