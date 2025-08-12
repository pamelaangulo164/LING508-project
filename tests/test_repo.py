from db.mysql_repository import MysqlRepository
from models import EnglishTerm, Meaning, SpanishTerm, Example, PartOfSpeech, Gender

import pytest

@pytest.fixture(scope="module")
def repo():
    r = MysqlRepository()
    r.bootstrap_if_needed()
    return r

def test_select_seed_lesion(repo: MysqlRepository):
    et = repo.load_english_term("lesion")
    assert et and et.term == "lesion"

def test_insert_and_roundtrip_graph(repo: MysqlRepository):
    repo.delete_entry_by_english_lemma("bruise")  # cleanup before

    en = EnglishTerm(term="bruise", pos=PartOfSpeech.NOUN)
    m  = Meaning(description="Injury causing discoloration of the skin", english_term=en)
    es = SpanishTerm(term="moretón", gender=Gender.MASCULINE, meaning=m)
    ex1 = Example(language="en", text="He had a bruise on his arm.", meaning=m)
    ex2 = Example(language="es", text="Tenía un moretón en el brazo.", meaning=m)

    repo.insert_english_term(en)
    repo.insert_meaning(m)
    repo.link_meaning_english(m.meaning_id, en.term_id)
    repo.insert_spanish_term(es)
    repo.link_meaning_spanish(m.meaning_id, es.term_id)
    repo.insert_example(ex1); repo.insert_example(ex2)

    back = repo.load_english_term("bruise")
    assert back and back.term == "bruise"
    assert any(st.term == "moretón" for mm in back.meanings for st in mm.spanish_terms)
