import pytest
import hashlib
from radar.quality import assess_release


def row(i,cohort,correct=True):
    return {'case_id':cohort+str(i),'pncp_id':cohort+str(i%10),'cohort':cohort,'kind':'answerable',
        'source_hashes':[hashlib.sha256((cohort+str(i%10)).encode()).hexdigest()],
        'natural_question':True,'source_approved':True,'review_status':'human_reviewed',
        'answer_state':'answered','correct':correct,'complete':True,'supported':True,'refusal_safe':None}


def cases():
    rows=[row(i,'regression',i<27) for i in range(30)]+[row(i,'new',i<90) for i in range(100)]
    refuse=row(999,'regression');refuse.update(kind='out_of_scope',answer_state='refused',refusal_safe=True)
    return rows+[refuse]


def test_ninety_percent_per_group_is_not_automatic_promotion():
    result=assess_release(cases())
    assert result['decision']=='eligible_for_manual_promotion' and not result['promotion_performed']
    assert result['groups']['new']['end_to_end_success']==.9


def test_old_success_cannot_hide_new_failure():
    rows=cases();rows[30]['correct']=False
    assert 'new_below_target_or_unscored' in assess_release(rows)['reasons']


def test_refusals_cannot_inflate_factual_success():
    rows=cases();rows[30].update(answer_state='insufficient_evidence',correct=True)
    result=assess_release(rows)
    assert result['groups']['new']['end_to_end_success']==.89
    assert result['decision']=='blocked'


def test_assistant_review_cannot_claim_human_approval():
    rows=cases();rows[0]['review_status']='assistant_reviewed'
    result=assess_release(rows)
    assert result['groups']['regression']['end_to_end_success'] is None
    assert 'references_or_human_reviews_pending' in result['reasons']


@pytest.mark.parametrize('mutation,reason',[
    ({'natural_question':False},'new_questions_have_location_hints'),
    ({'pncp_id':'regression0'},'edital_overlap_between_groups'),
    ({'source_approved':False},'references_or_human_reviews_pending')])
def test_leakage_and_source_checks_block_release(mutation,reason):
    rows=cases();rows[30].update(mutation)
    assert reason in assess_release(rows)['reasons']


def test_duplicate_and_string_scores_rejected():
    rows=cases();rows[1]['case_id']=rows[0]['case_id']
    with pytest.raises(ValueError):assess_release(rows)
    rows=cases();rows[0]['correct']='true'
    with pytest.raises(ValueError):assess_release(rows)


def test_same_pdf_in_different_edital_still_blocks_reserve():
    rows=cases();rows[30]['source_hashes']=rows[0]['source_hashes']
    assert 'pdf_overlap_between_groups' in assess_release(rows)['reasons']
