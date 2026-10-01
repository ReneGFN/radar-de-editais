"""Critério local de promoção de versões; não altera banco nem garante precisão futura."""


def assess_release(rows,*,target=.90,min_new_questions=100,min_new_editais=10,min_regression_questions=30):
    if not 0<target<=1 or min_new_questions<1 or min_new_editais<1 or min_regression_questions<1:
        raise ValueError('Critério de qualidade inválido')
    seen=set();reasons=[]
    for row in rows:
        if not isinstance(row,dict) or not isinstance(row.get('case_id'),str) or not row['case_id'] or row['case_id'] in seen:
            raise ValueError('Caso ausente ou duplicado')
        seen.add(row['case_id'])
        if row.get('cohort') not in ('regression','new') or row.get('kind') not in ('answerable','out_of_scope'):
            raise ValueError('Grupo de avaliação inválido')
        if row.get('review_status') not in ('pending','assistant_reviewed','human_reviewed'):
            raise ValueError('Revisão inválida')
        if row.get('answer_state') not in ('answered','refused','insufficient_evidence','rejected','not_run'):
            raise ValueError('Estado inválido')
        if not isinstance(row.get('pncp_id'),str) or not row['pncp_id']:
            raise ValueError('Edital ausente')
        hashes=row.get('source_hashes')
        if not isinstance(hashes,list) or not hashes or any(not isinstance(h,str) or len(h)!=64 or any(c not in '0123456789abcdef' for c in h) for h in hashes):
            raise ValueError('Hashes de origem ausentes ou inválidos')
        for key in ('natural_question','source_approved'):
            if type(row.get(key)) is not bool:raise ValueError('Indicador inválido')
        for key in ('correct','complete','supported','refusal_safe'):
            if row.get(key) is not None and type(row[key]) is not bool:
                raise ValueError('Pontuação inválida')
    if any(r['review_status']!='human_reviewed' or not r['source_approved'] for r in rows):
        reasons.append('references_or_human_reviews_pending')
    result={}
    for cohort,minimum in [('regression',min_regression_questions),('new',min_new_questions)]:
        group=[r for r in rows if r['cohort']==cohort]
        facts=[r for r in group if r['kind']=='answerable']
        success=sum(r['review_status']=='human_reviewed' and r['answer_state']=='answered' and
                    all(r.get(key) is True for key in ('correct','complete','supported')) for r in facts)
        answered=sum(r['answer_state']=='answered' for r in facts)
        reviewed=all(r['review_status']=='human_reviewed' for r in facts)
        rate=success/len(facts) if facts and reviewed else None
        result[cohort]={'answerable_cases':len(facts),'human_reviewed':sum(r['review_status']=='human_reviewed' for r in facts),
            'correct_complete_supported':success if reviewed else None,
            'end_to_end_success':rate,'answer_coverage':answered/len(facts) if facts else None,
            'precision_among_answers':success/answered if answered and reviewed else None,
            'distinct_editais':len({r['pncp_id'] for r in facts})}
        if len(facts)<minimum:reasons.append(cohort+'_sample_too_small')
        if rate is None or rate<target:reasons.append(cohort+'_below_target_or_unscored')
        if cohort=='new':
            if result[cohort]['distinct_editais']<min_new_editais:reasons.append('new_editais_too_few')
            if any(not r['natural_question'] for r in facts):reasons.append('new_questions_have_location_hints')
    old_ids={r['pncp_id'] for r in rows if r['cohort']=='regression'}
    new_ids={r['pncp_id'] for r in rows if r['cohort']=='new'}
    if old_ids & new_ids:reasons.append('edital_overlap_between_groups')
    old_hashes={h for r in rows if r['cohort']=='regression' for h in r['source_hashes']}
    new_hashes={h for r in rows if r['cohort']=='new' for h in r['source_hashes']}
    if old_hashes & new_hashes:reasons.append('pdf_overlap_between_groups')
    refusals=[r for r in rows if r['kind']=='out_of_scope']
    if not refusals:reasons.append('refusal_cases_missing')
    if any(r['review_status']!='human_reviewed' or r.get('refusal_safe') is not True for r in refusals):
        reasons.append('refusal_review_pending_or_unsafe')
    return {'decision':'eligible_for_manual_promotion' if not reasons else 'blocked',
        'target':target,'groups':result,'reasons':reasons,
        'guarantee':'none; benchmark result does not guarantee future accuracy',
        'promotion_performed':False}
