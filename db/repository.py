from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional, Iterable         
from uuid import UUID
from models import EnglishTerm, Meaning, SpanishTerm, Example

class Repository(ABC):
    @abstractmethod
    def load_english_term(self, lemma: str) -> Optional[EnglishTerm]: ...

    @abstractmethod
    def insert_english_term(self, term: EnglishTerm) -> None: ...
    @abstractmethod
    def insert_meaning(self, meaning: Meaning) -> None: ...
    @abstractmethod
    def insert_spanish_term(self, term: SpanishTerm) -> None: ...
    @abstractmethod
    def insert_example(self, example: Example) -> None: ...

    @abstractmethod
    def link_meaning_english(self, meaning_id: UUID, english_term_id: UUID) -> None: ...
    @abstractmethod
    def link_meaning_spanish(self, meaning_id: UUID, spanish_term_id: UUID) -> None: ...

 
    @abstractmethod
    def persist_entry_graph(
        self,
        english: EnglishTerm,
        meaning: Meaning,
        spanish: SpanishTerm,
        examples: Iterable[Example],
    ) -> None: ...


    @abstractmethod
    def delete_entry_by_english_lemma(self, lemma: str) -> None: ...
