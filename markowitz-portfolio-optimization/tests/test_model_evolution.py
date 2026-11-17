"""Synthetic METADATA only: no returns, models, market data, or extra experiments."""
import copy
import hashlib
import json
import socket
import subprocess
import sys

import pytest

from scripts import check_model_evolution as policy


def read(path):
    return json.loads(path.read_text())


@pytest.fixture
def metadata(tmp_path):
    artifact = tmp_path/'invented.txt'
    artifact.write_text('SYNTHETIC METADATA FIXTURE — not market data or permission\n')
    registry = read(policy.REGISTRY)
    registry['preserved_artifacts'] = {'invented.txt': hashlib.sha256(artifact.read_bytes()).hexdigest()}
    registry['holdouts'].append(dict(id='006-confirmation-fixture-v1', start='2000-10-01', end='2000-12-31',
        purpose='challenger_confirmation', state='reserved', owner_authorization_ref='SYNTHETIC FIXTURE ONLY'))
    record = read(policy.TEMPLATE)
    def fill(value):
        if isinstance(value, dict): return {k:fill(v) for k,v in value.items()}
        if isinstance(value, list): return [fill(v) for v in value]
        return 'SYNTHETIC FIXTURE ONLY — no authorization' if isinstance(value,str) and value.startswith('REQUIRED:') else value
    record = fill(record)
    record.update(candidate_id='006-challenger-fixture-v1', kind='candidate', stage='preregistered',
        registered_at='2001-01-03T00:00:00Z', earliest_evaluation_at='2001-01-04T00:00:00Z', preregistration_commit='a'*40)
    record['comparison']['criteria_status'] = 'frozen'
    record['reproducibility'].update(code_commit='b'*40,config_sha256='c'*64,environment_lock_sha256='d'*64)
    record['training_information'].update(decision_at='2000-07-01T00:00:00Z',
        latest_observation_at='2000-06-30T20:00:00Z',latest_publication_at='2000-06-30T21:00:00Z',
        latest_revision_available_at='2000-06-30T21:00:00Z',snapshot_retrieved_at='2001-01-01T00:00:00Z',
        point_in_time_evidence='SYNTHETIC PIT evidence only',snapshot_sha256='e'*64,manifest_sha256='f'*64,
        adjustment_vintage='SYNTHETIC publisher/vintage fixture')
    for item in record['eligibility'].values():
        if isinstance(item,dict): item.update(status='approved',evidence='SYNTHETIC entitlement fixture only')
    record['eligibility'].update(source_policy_approval_ref='SYNTHETIC policy fixture only',independent_verification_ref='SYNTHETIC check fixture only')
    record['periods'].update(training=dict(start='2000-01-01',end='2000-06-30'), calibration=dict(start='2000-05-01',end='2000-06-30'),
        validation=dict(start='2000-07-02',end='2000-09-30'),
        confirmation=dict(holdout_id='006-confirmation-fixture-v1',start='2000-10-01',end='2000-12-31'))
    record['owner_preregistration_signoff'].update(reviewer='Synthetic test actor',at='2001-01-02T00:00:00Z',evidence='SYNTHETIC ONLY')
    return record,registry,tmp_path


def test_production_checkpoint_is_unapproved_and_history_intact(monkeypatch):
    def forbidden(*args, **kwargs): raise AssertionError('No network or analytical module loading')
    monkeypatch.setattr(socket, 'create_connection', forbidden)
    registry = policy.validate_registry(read(policy.REGISTRY))
    assert registry['decisions'] == [] and registry['consumption_events'] == []
    assert registry['holdouts'][0]['state'] == 'reserved'
    record = read(policy.TEMPLATE)
    before = copy.deepcopy(record),copy.deepcopy(registry)
    assert policy.validate_record(record,registry) == ['Proposal only: not preregistered, not cleared for evaluation']
    assert before == (record,registry)


def test_complete_invented_preregistration_is_deterministic_and_not_authorization(metadata):
    record,registry,root = metadata
    policy.validate_registry(registry,root)
    before = copy.deepcopy((record,registry))
    assert policy.validate_record(record,registry,root) == []
    assert policy.validate_record(copy.deepcopy(record),copy.deepcopy(registry),root) == []
    assert (record,registry) == before


@pytest.mark.parametrize('field', ['hypothesis','comparison','training_information','eligibility','owner_preregistration_signoff'])
def test_required_fields(metadata,field):
    record,registry,root = metadata
    del record[field]
    with pytest.raises(ValueError,match='Missing fields'): policy.validate_record(record,registry,root)


@pytest.mark.parametrize('change', ['bad_id','old_champion','wrong_version','template','proposed_criteria','placeholder','no_signoff','no_commit','empty_metrics'])
def test_preregistration_requirements(metadata,change):
    r,g,root = metadata
    if change=='bad_id': r['candidate_id']='unversioned'
    elif change=='old_champion': r['champion_id']='tuned-006-v1'
    elif change=='wrong_version': r['record_version']=0
    elif change=='template': r['kind']='template'
    elif change=='proposed_criteria': r['comparison']['criteria_status']='proposed'
    elif change=='placeholder': r['hypothesis']='REQUIRED: incomplete'
    elif change=='no_signoff': r['owner_preregistration_signoff']['evidence']=None
    elif change=='no_commit': r['preregistration_commit']=None
    else: r['comparison']['metrics']=[]
    with pytest.raises(ValueError): policy.validate_record(r,g,root)


@pytest.mark.parametrize('key', ['latest_observation_at','latest_publication_at','latest_revision_available_at'])
def test_unavailable_at_decision_is_leakage(metadata,key):
    r,g,root = metadata
    r['training_information'][key]='2000-07-01T00:00:01Z'
    with pytest.raises(ValueError,match='Temporal leakage'): policy.validate_record(r,g,root)


@pytest.mark.parametrize('change', ['naive','late_prereg','retrieved_later','no_pit','calibration','training','confirmation_overlap'])
def test_time_contract_and_separate_clocks(metadata,change):
    r,g,root = metadata
    if change=='naive': r['training_information']['decision_at']='2000-07-01T00:00:00'
    elif change=='late_prereg': r['earliest_evaluation_at']=r['registered_at']
    elif change=='retrieved_later': r['training_information']['snapshot_retrieved_at']='2002-01-01T00:00:00Z'
    elif change=='no_pit': r['training_information']['point_in_time_evidence']=None
    elif change=='calibration': r['periods']['calibration']['end']='2000-07-02'
    elif change=='training': r['periods']['training']['end']='2000-07-01'
    else: r['periods']['confirmation']['start']='2000-09-30'
    with pytest.raises(ValueError): policy.validate_record(r,g,root)


@pytest.mark.parametrize('gate', ['automation','analysis','retention','independent_comparison','public_derived_outputs','raw_redistribution'])
def test_rights_unknown_denied_or_unevidenced_are_blocked(metadata,gate):
    r,g,root = metadata
    r['eligibility'].update(publication_planned=True,raw_distribution_planned=True)
    for status,evidence in [('unknown',None),('denied','SYNTHETIC evidence'),('approved',None)]:
        r['eligibility'][gate].update(status=status,evidence=evidence)
        with pytest.raises(ValueError,match='Data-rights gate'): policy.validate_record(r,g,root)


def test_independent_checks_and_runtime_policy_are_not_replaced(metadata):
    r,g,root = metadata
    for key in ('independent_verification_ref','source_policy_approval_ref'):
        bad=copy.deepcopy(r);bad['eligibility'][key]=None
        with pytest.raises(ValueError,match='Existing source-policy'): policy.validate_record(bad,g,root)


def event(holdout='006-confirmation-fixture-v1'):
    return dict(holdout_id=holdout,candidate_id='006-challenger-earlier-v1',actor='Synthetic test actor',accessed_at='2001-01-01T00:00:00Z',
        purpose='Synthetic partial result peek',evidence_ref='SYNTHETIC test actor/evidence only')


def test_consumed_relabelled_and_overlapping_holdouts_fail(metadata):
    r,g,root = metadata
    g['consumption_events'].append(event())
    with pytest.raises(ValueError,match='Consumption log/state mismatch'): policy.validate_registry(g,root)
    g['holdouts'][1]['state']='consumed'
    policy.validate_registry(g,root)
    with pytest.raises(ValueError,match='Consumed/ineligible'): policy.validate_record(r,g,root)
    # An unused name over already used observations is still contaminated.
    g['holdouts'].append(dict(g['holdouts'][1],id='006-confirmation-renamed-v1',state='reserved'))
    r['periods']['confirmation']['holdout_id']='006-confirmation-renamed-v1'
    with pytest.raises(ValueError,match='overlaps'): policy.validate_record(r,g,root)


def test_original_open_ended_reserve_cannot_be_split_for_challengers(metadata):
    r,g,root = metadata
    r['periods']['confirmation'].update(start='2025-02-01',end='2025-03-01')
    g['holdouts'][1].update(start='2025-02-01',end='2025-03-01')
    with pytest.raises(ValueError,match='overlaps'): policy.validate_record(r,g,root)
    r['periods']['confirmation']['holdout_id']='006-v1-reserved'
    with pytest.raises(ValueError,match='Original holdout'): policy.validate_record(r,g,root)


def test_fingerprints_and_predecessor_history_are_immutable(metadata):
    r,g,root = metadata
    g['holdouts'][1]['state']='consumed';g['consumption_events']=[event()]
    previous=root/'registry-previous.json';previous.write_text(json.dumps(g))
    new=copy.deepcopy(g);new.update(checkpoint_version=2,previous_registry=dict(path=previous.name,sha256=hashlib.sha256(previous.read_bytes()).hexdigest()))
    policy.validate_registry(new,root)
    lost=copy.deepcopy(new);lost['consumption_events']=[];lost['holdouts'][1]['state']='reserved'
    with pytest.raises(ValueError,match='append-only'): policy.validate_registry(lost,root)
    moved=copy.deepcopy(new);moved['holdouts'][1]['start']='2000-11-01'
    with pytest.raises(ValueError,match='relabel'): policy.validate_registry(moved,root)
    changed=copy.deepcopy(new);changed['preserved_artifacts']['invented.txt']='0'*64
    with pytest.raises(ValueError,match='Immutable artifact changed'): policy.validate_registry(changed,root)
    previous.write_text('tampered registry')
    with pytest.raises(ValueError,match='Immutable artifact changed'): policy.validate_registry(new,root)


def test_sealed_decision_cannot_be_overwritten_or_reused(metadata):
    r,g,root = metadata
    path=root/'sealed-decision.json';path.write_text(json.dumps(r))
    g['decisions']=[dict(id=r['candidate_id'],path=path.name,sha256=hashlib.sha256(path.read_bytes()).hexdigest())]
    policy.validate_registry(g,root)
    assert policy.validate_record(r,g,root) == []  # Rechecking identical sealed metadata is safe.
    altered=copy.deepcopy(r);altered['hypothesis']='Changed after preregistration'
    with pytest.raises(ValueError,match='Sealed decision ID'): policy.validate_record(altered,g,root)
    old=root/'previous-with-decision.json';old.write_text(json.dumps(g))
    removed=copy.deepcopy(g);removed.update(checkpoint_version=2,decisions=[],previous_registry=dict(path=old.name,sha256=hashlib.sha256(old.read_bytes()).hexdigest()))
    with pytest.raises(ValueError,match='decisions must be append-only'): policy.validate_registry(removed,root)
    path.write_text(json.dumps(dict(r,hypothesis='Rewritten after outcomes')))
    with pytest.raises(ValueError,match='Immutable artifact changed'): policy.validate_registry(g,root)


def test_cli_proposal_pass_is_not_preregistration_or_execution():
    script=policy.ROOT/'scripts/check_model_evolution.py'
    result=subprocess.run([sys.executable,str(script)],capture_output=True,text=True)
    assert result.returncode==0 and 'not cleared for evaluation' in result.stdout
    assert 'No model, data retrieval' in result.stdout
    blocked=subprocess.run([sys.executable,str(script),'--require-preregistered'],capture_output=True,text=True)
    assert blocked.returncode==1 and 'Proposal only' in blocked.stdout


def test_snapshot_cannot_predate_its_declared_inputs(metadata):
    r,g,root = metadata
    r['training_information']['snapshot_retrieved_at']='2000-06-30T19:00:00Z'
    with pytest.raises(ValueError,match='Snapshot predates'): policy.validate_record(r,g,root)


def test_predecessor_must_itself_be_a_valid_registry(metadata):
    r,g,root = metadata
    invalid=copy.deepcopy(g);invalid['champion_id']='rewritten-history'
    previous=root/'invalid-predecessor.json';previous.write_text(json.dumps(invalid))
    new=copy.deepcopy(g);new.update(checkpoint_version=2,previous_registry=dict(path=previous.name,sha256=hashlib.sha256(previous.read_bytes()).hexdigest()))
    with pytest.raises(ValueError,match='Frozen policy/champion'): policy.validate_registry(new,root)


def test_registry_rejects_overlap_even_before_use(metadata):
    r,g,root = metadata
    g['holdouts'].append(dict(g['holdouts'][1],id='006-confirmation-renamed-v1'))
    with pytest.raises(ValueError,match='Overlapping'): policy.validate_registry(g,root)
