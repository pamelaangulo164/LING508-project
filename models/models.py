from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List
from uuid import uuid4, UUID

class PartOfSpeech(Enum):
    NOUN = "noun"
    VERB = "verb"
    ADJ  = "adj"
    ADV  = "adv"

class Gender(Enum):
    MASCULINE = "m"
    FEMININE  = "f"
    NEUTER    = "n"
    COMMON    = "c"

@dataclass
class EnglishTerm:
    term: str
    pos: PartOfSpeech
    term_id: UUID = field(default_factory=uuid4)
    meanings: List["Meaning"] = field(default_factory=list)

    def add_meaning(self, meaning: "Meaning") -> None:
        if meaning not in self.meanings:
            self.meanings.append(meaning)

@dataclass
class Meaning:
    description: str
    english_term: EnglishTerm
    meaning_id: UUID = field(default_factory=uuid4)
    spanish_terms: List["SpanishTerm"] = field(default_factory=list)
    examples: List["Example"] = field(default_factory=list)

    def add_spanish_term(self, st: "SpanishTerm") -> None:
        if st not in self.spanish_terms:
            self.spanish_terms.append(st)

    def add_example(self, ex: "Example") -> None:
        if ex not in self.examples:
            self.examples.append(ex)

@dataclass
class SpanishTerm:
    term: str
    gender: Gender
    meaning: Meaning
    term_id: UUID = field(default_factory=uuid4)

@dataclass
class Example:
    language: str
    text: str
    meaning: Meaning
    example_id: UUID = field(default_factory=uuid4)

def serialize_entry(et: EnglishTerm) -> dict:
    return {
        "english_term": et.term,
        "pos": et.pos.value,
        "meanings": [
            {
                "description": m.description,
                "spanish_terms": [
                    {"term": st.term, "gender": st.gender.value}
                    for st in m.spanish_terms
                ],
                "examples": [
                    {"language": ex.language, "text": ex.text}
                    for ex in m.examples
                ],
            }
            for m in et.meanings
        ],
    }
