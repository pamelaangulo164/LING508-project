from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import List
from uuid import UUID, uuid4


class PartOfSpeech(str, Enum):
    NOUN = "noun"
    VERB = "verb"
    ADJ  = "adj"

class Gender(str, Enum):
    MASCULINE = "m"
    FEMININE  = "f"

@dataclass
class EnglishTerm:
    term: str
    pos: PartOfSpeech
    term_id: UUID = field(default_factory=uuid4)
    meanings: List["Meaning"] = field(default_factory=list, init=False)

    def add_meaning(self, meaning: "Meaning") -> None:
        self.meanings.append(meaning)

@dataclass
class Meaning:
    description: str
    english_term: EnglishTerm
    meaning_id: UUID = field(default_factory=uuid4)
    spanish_terms: List["SpanishTerm"] = field(default_factory=list, init=False)
    examples: List["Example"] = field(default_factory=list, init=False)

    def __post_init__(self) -> None:
        self.english_term.add_meaning(self)

    def add_spanish_term(self, term: "SpanishTerm") -> None:
        self.spanish_terms.append(term)

    def add_example(self, ex: "Example") -> None:
        self.examples.append(ex)

    def to_dict(self) -> dict:
        return {
            "description": self.description,
            "spanish_terms": [
                {"term": s.term, "gender": s.gender.value} for s in self.spanish_terms
            ],
            "examples": [{"language": e.language, "text": e.text} for e in self.examples],
        }

@dataclass
class SpanishTerm:
    term: str
    gender: Gender
    meaning: Meaning
    term_id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self.meaning.add_spanish_term(self)

@dataclass
class Example:
    language: str   
    text: str
    meaning: Meaning
    example_id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        self.meaning.add_example(self)
