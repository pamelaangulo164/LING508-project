from typing import Iterable, Optional
from db.repository import Repository
from models import EnglishTerm, Meaning, SpanishTerm, Example, PartOfSpeech, Gender

class DictionaryService:
    def __init__(self, repo: Repository):
        self.repo = repo

    def lookup_english(self, lemma: str) -> Optional[EnglishTerm]:
        lemma = lemma.strip()
        if not lemma:
            return None
        return self.repo.load_english_term(lemma)  # <-- returns domain object

    def add_entry(
        self,
        *,
        lemma: str,
        pos: PartOfSpeech,
        meaning_desc: str,
        spanish_term: str,
        gender: Gender,
        examples: Iterable[tuple[str, str]] = (),
    ) -> EnglishTerm:
        if not lemma.strip() or not meaning_desc.strip() or not spanish_term.strip():
            raise ValueError("lemma, meaning_desc, spanish_term required")

        en = EnglishTerm(term=lemma.strip(), pos=pos)
        me = Meaning(description=meaning_desc.strip(), english_term=en)
        es = SpanishTerm(term=spanish_term.strip(), gender=gender, meaning=me)
        ex_objs = [Example(language=lng.strip(), text=txt.strip(), meaning=me)
                   for (lng, txt) in examples]

        self.repo.persist_entry_graph(en, me, es, ex_objs)
        return en  
