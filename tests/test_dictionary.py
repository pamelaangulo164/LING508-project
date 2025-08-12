from uuid import UUID

from models import (
    EnglishTerm,
    SpanishTerm,
    Meaning,
    Example,
    PartOfSpeech,
    Gender,
)


def test_basic_english_term():
    lesion = EnglishTerm(term="lesion", pos=PartOfSpeech.NOUN)
    assert lesion.term == "lesion"
    assert lesion.pos is PartOfSpeech.NOUN
    assert isinstance(lesion.term_id, UUID)
    assert lesion.meaning_ids == []


def test_link_english_and_meaning_by_ids():
    lesion = EnglishTerm(term="lesion", pos=PartOfSpeech.NOUN)
    m1 = Meaning(description="Pathological change; abnormal tissue")

    lesion.add_meaning_id(m1.meaning_id)
    m1.add_english_term_id(lesion.term_id)

    assert m1.meaning_id in lesion.meaning_ids
    assert lesion.term_id in m1.english_term_ids


def test_spanish_term_links_to_meaning_by_ids():
    m1 = Meaning(description="Injury, trauma (e.g. bruise, fracture)")
    es_lesion = SpanishTerm(term="lesión", gender=Gender.FEMININE)

    es_lesion.add_meaning_id(m1.meaning_id)
    m1.add_spanish_term_id(es_lesion.term_id)

    assert es_lesion.gender is Gender.FEMININE
    assert m1.meaning_id in es_lesion.meaning_ids
    assert es_lesion.term_id in m1.spanish_term_ids


def test_examples_attach_by_id():
    m1 = Meaning(description="Abnormal tissue area")
    ex_en = Example(language="en", text="MRI showed a brain lesion.", meaning_id=m1.meaning_id)
    ex_es = Example(language="es", text="La resonancia mostró una lesión.", meaning_id=m1.meaning_id)

    m1.add_example_id(ex_en.example_id)
    m1.add_example_id(ex_es.example_id)

    assert ex_en.meaning_id == m1.meaning_id
    assert ex_es.meaning_id == m1.meaning_id
    assert {ex_en.example_id, ex_es.example_id}.issubset(set(m1.example_ids))
