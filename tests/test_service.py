import pytest
from services.service import DictionaryService
from db.mysql_repository import MysqlRepository
from models import PartOfSpeech, Gender

@pytest.fixture(scope="module")
def svc():
    repo = MysqlRepository()
    repo.bootstrap_if_needed()
    # ensure clean slate for this lemma
    repo.delete_entry_by_english_lemma("bruise")
    return DictionaryService(repo)

def test_lookup_english_existing(svc: DictionaryService):
    data = svc.lookup_english("lesion")
    assert data and data["english_term"] == "lesion"

def test_add_entry_and_lookup_roundtrip(svc: DictionaryService):
    svc.add_entry(
        lemma="bruise",
        pos=PartOfSpeech.NOUN,
        meaning_desc="Injury causing discoloration of the skin",
        spanish_term="moretón",
        gender=Gender.MASCULINE,
        examples=[("en","He had a bruise on his arm."), ("es","Tenía un moretón en el brazo.")],
    )
    again = svc.lookup_english("bruise")
    assert again and again["english_term"] == "bruise"
    assert any(st["term"] == "moretón" for m in again["meanings"] for st in m["spanish_terms"])
