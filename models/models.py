from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import List


class PartOfSpeech(Enum):
    NOUN = "noun"
    ADJECTIVE = "adjective"
    VERB = "verb"
    OTHER = "other"


class Gender(Enum):
    MASCULINE = "m"
    FEMININE = "f"
    INVARIABLE = "inv"


@dataclass(slots=True)
class EnglishTerm:
    term: str
    pos: PartOfSpeech
    term_id: uuid.UUID = field(default_factory=uuid.uuid4, init=False)
    meanings: List["Meaning"] = field(default_factory=list, init=False)

    def add_meaning(self, meaning: "Meaning") -> None:
        if meaning.english_term is not self:
            raise ValueError("Meaning.english_term must reference this EnglishTerm")
        self.meanings.append(meaning)
    def to_dict(self) -> dict:
    return {
        "term_id": str(self.term_id),
        "term": self.term,
        "pos": self.pos.value,
        "meanings": [m.to_dict() for m in self.meanings],
    }


@dataclass(slots=True)
class Meaning:
    description: str
    english_term: EnglishTerm
    meaning_id: uuid.UUID = field(default_factory=uuid.uuid4, init=False)
    spanish_terms: List["SpanishTerm"] = field(default_factory=list, init=False)
    examples: List["Example"] = field(default_factory=list, init=False)

    def add_spanish_term(self, term: "SpanishTerm") -> None:
        if term.meaning is not self:
            raise ValueError("SpanishTerm.meaning must reference this Meaning")
        self.spanish_terms.append(term)

    def add_example(self, example: "Example") -> None:
        if example.meaning is not self:
            raise ValueError("Example.meaning must reference this Meaning")
        self.examples.append(example)

    def to_dict(self) -> dict:
    return {
        "meaning_id": str(self.meaning_id),
        "description": self.description,
        "english_term_id": str(self.english_term_id) if hasattr(self, "english_term_id") else None,
        "spanish_terms": [t.to_dict() for t in self.spanish_terms],
        "examples": [e.to_dict() for e in self.examples],
    }


@dataclass(slots=True)
class SpanishTerm:
    term: str
    gender: Gender
    meaning: Meaning
    term_id: uuid.UUID = field(default_factory=uuid.uuid4, init=False)

    def __post_init__(self) -> None:
        if self not in self.meaning.spanish_terms:
            self.meaning.spanish_terms.append(self)
            
    def to_dict(self) -> dict:
    return {
        "term_id": str(self.term_id),
        "term": self.term,
        "gender": self.gender.value,
        "meaning_id": str(self.meaning_id),
    }

@dataclass(slots=True)
class Example:
    language: str
    text: str
    meaning: Meaning
    example_id: uuid.UUID = field(default_factory=uuid.uuid4, init=False)

    def __post_init__(self) -> None:
        if self not in self.meaning.examples:
            self.meaning.examples.append(self)
            
def to_dict(self) -> dict:
    return {
        "example_id": str(self.example_id),
        "language": self.language,
        "text": self.text,
        "meaning_id": str(self.meaning_id),
    }
