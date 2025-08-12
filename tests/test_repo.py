from uuid import UUID
import pytest
from db.mysql_repository import MysqlRepository
from models import EnglishTerm, Meaning, SpanishTerm, Example, PartOfSpeech, Gender

@pytest.fixture(scope="module")
def repo():
    r = MysqlRepository()
    r.bootstrap_if_needed()
    return r

def test_select_seed_lesion(repo: MysqlRepository):
    et = repo.load_english_term("lesion")
    assert et is not None
    assert et.term == "lesion"
    assert et.pos == PartOfSpeech.NOUN
    assert len(et.meanings) >= 1
    m = et.meanings[0]
    assert isinstance(m.description, str) and len(m.description) > 0
    assert len(m.spanish_terms) >= 1
    assert len(m.examples) >= 1

def test_insert_and_roundtrip_graph(repo: MysqlRepository):
    en = EnglishTerm(term="bruise", pos=PartOfSpeech.NOUN)
    m  = Meaning(description="Injury causing discoloration of the skin", english_term=en)
    es = SpanishTerm(term="moretón", gender=Gender.MASCULINE, meaning=m)
    ex1 = Example(language="en", text="He had a bruise on his arm.", meaning=m)
    ex2 = Example(language="es", text="Tenía un moretón en el brazo.", meaning=m)

    repo.insert_english_term(en)
    repo.insert_meaning(m)
    repo.insert_spanish_term(es)
    repo.insert_example(ex1)
    repo.insert_example(ex2)
    repo.link_meaning_english(m.meaning_id, en.term_id)
    repo.link_meaning_spanish(m.meaning_id, es.term_id)

    got = repo.load_english_term("bruise")
    assert got is not None
    assert got.term == "bruise"
    assert got.pos == en.pos
    assert len(got.meanings) == 1
    gm = got.meanings[0]
    assert any(st.term == "moretón" for st in gm.spanish_terms)
    langs = {e.language for e in gm.examples}
    assert {"en","es"} <= langs
