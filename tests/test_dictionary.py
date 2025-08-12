from uuid import UUID
from models import (
    EnglishTerm, SpanishTerm, Meaning, Example, PartOfSpeech, Gender
)

def test_basic_english_term():
    lesion = EnglishTerm(term="lesion", pos=PartOfSpeech.NOUN)
    assert lesion.term == "lesion"
    assert lesion.pos is PartOfSpeech.NOUN
    assert isinstance(lesion.term_id, UUID)
    assert lesion.meanings == []

def test_meaning():
    lesion = EnglishTerm(term="lesion", pos=PartOfSpeech.NOUN)
    m1 = Meaning(description="Injury, trauma (e.g. bruise, fracture)", english_term=lesion)
    lesion.add_meaning(m1)
    assert lesion.meanings[0].description.startswith("Injury")

def test_spanish_term_link():
    lesion = EnglishTerm(term="lesion", pos=PartOfSpeech.NOUN)
    m1 = Meaning(description="Pathological change; abnormal tissue", english_term=lesion)
    es_lesion = SpanishTerm(term="lesión", gender=Gender.FEMININE, meaning=m1)
    assert es_lesion.gender is Gender.FEMININE
    assert es_lesion in m1.spanish_terms
    assert es_lesion.meaning is m1

def test_examples_attach():
    lesion = EnglishTerm(term="lesion", pos=PartOfSpeech.NOUN)
    m1 = Meaning(description="Pathological change; abnormal tissue", english_term=lesion)
    ex_en = Example(language="en", text="The MRI showed a suspicious brain lesion.", meaning=m1)
    ex_es = Example(language="es", text="La resonancia mostró una lesión sospechosa en el cerebro.", meaning=m1)
    m1.add_example(ex_en)
    m1.add_example(ex_es)
    assert {e.language for e in m1.examples} == {"en", "es"}
