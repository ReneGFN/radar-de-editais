import pytest
from radar.sector import classify_sector
from radar.ingestion import matches_sector


@pytest.mark.parametrize('text',['Monitores portáteis de glicemia e lancetas','Monitores de sinais vitais de triagem e seladora'])
def test_medical_monitor_is_not_computer_display(text):
    assert classify_sector(text)=='out_of_scope'
    assert not matches_sector(text)


def test_ambiguous_monitor_requires_review():
    assert classify_sector('Aquisição de monitores')=='review_required'
    assert not matches_sector('Aquisição de monitores')


def test_medical_buyer_does_not_exclude_real_computers():
    assert classify_sector('Aquisição de notebooks para unidade hospitalar')=='mixed_requires_item_review'
    assert matches_sector('Aquisição de notebooks para unidade hospitalar')


def test_known_it_category_and_display():
    assert matches_sector('Equipamentos de informática')
    assert matches_sector('Aquisição de monitores LCD de vídeo')
    assert not matches_sector('Papelaria e suprimentos de informática')


def test_generic_it_materials_still_remain_candidates():
    assert matches_sector('Aquisição de materiais de informática para unidade pública')
