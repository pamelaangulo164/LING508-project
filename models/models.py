from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List
from uuid import UUID, uuid4


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
    term_id: UUID = field(default_factory=uuid4, init=False)
    # Associations are by ID (no embedded objects)
    meaning_ids: List[UUID] = field(default_factory=list, init=False)

    def add_meaning_id(self, meaning_id: UUID) -> None:
        if meaning_id not in self.meaning_ids:
            self.meaning_ids.append(meaning_id)


@dataclass(slots=True)
class SpanishTerm:
    term: str
    gender: Gender
    term_id: UUID = field(default_factory=uuid4, init=False)
    # A Spanish term may map to one or more meanings
    meaning_ids: List[UUID] = field(default_factory=list, init=False)

    def add_meaning_id(self, meaning_id: UUID) -> None:
        if meaning_id not in self.meaning_ids:
            self.meaning_ids.append(meaning_id)


@dataclass(slots=True)
class Meaning:
    description: str
    meaning_id: UUID = field(default_factory=uuid4, init=False)
    # References to related terms by ID
    english_term_ids: List[UUID] = field(default_factory=list, init=False)
    spanish_term_ids: List[UUID] = field(default_factory=list, init=False)
    example_ids: List[UUID] = field(default_factory=list, init=False)

    def add_english_term_id(self, term_id: UUID) -> None:
        if term_id not in self.english_term_ids:
            self.english_term_ids.append(term_id)

    def add_spanish_term_id(self, term_id: UUID) -> None:
        if term_id not in self.spanish_term_ids:
            self.spanish_term_ids.append(term_id)

    def add_example_id(self, example_id: UUID) -> None:
        if example_id not in self.example_ids:
            self.example_ids.append(example_id)


@dataclass(slots=True)
class Example:
    language: str  # "en" or "es"
    text: str
    meaning_id: UUID
    example_id: UUID = field(default_factory=uuid4, init=False)
