"""Read-only, standard-library preregistration checklist. No data, fitting or authority.

Proposal templates may be structurally valid while every evaluation gate is blocked.
A complete preregistration is metadata consistency only, never a data-use grant.
"""
import argparse
from datetime import date, datetime
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
POLICY = '006-evolution-v1'
REGISTRY = ROOT/'research/model-evolution/registry-v1.json'
TEMPLATE = ROOT/'research/model-evolution/decision-template.json'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def text(value):
    return isinstance(value, str) and bool(value.strip()) and not value.startswith('REQUIRED:')


def timestamp(value):
    require(isinstance(value, str), 'Timezone-aware timestamp required')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(result.tzinfo is not None and result.utcoffset() is not None, 'Timezone-aware timestamp required')
    return result


def interval(value):
    require(isinstance(value, dict) and set(value) >= {'start', 'end'}, 'Closed period required')
    start, end = date.fromisoformat(value['start']), date.fromisoformat(value['end'])
    require(start <= end, 'Reversed period')
    return start, end


def file_hash(root, relative):
    path = (root/relative).resolve()
    require(path.is_relative_to(root.resolve()) and path.is_file(), 'Evidence path must be a local file inside project')
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sealed_files(entries, root):
    for path, expected in entries.items():
        require(re.fullmatch(r'[0-9a-f]{64}', expected) is not None, 'Invalid artifact SHA-256')
        require(file_hash(root, path) == expected, f'Immutable artifact changed: {path}')


def validate_registry(registry, root=ROOT, _seen=frozenset()):
    require(registry['schema_version'] == POLICY and registry['champion_id'] == '006-v1', 'Frozen policy/champion ID')
    require(type(registry['checkpoint_version']) is int and registry['checkpoint_version'] >= 1, 'Registry version required')
    require(bool(registry['preserved_artifacts']), 'Historical fingerprints required')
    sealed_files(registry['preserved_artifacts'], root)
    previous = registry['previous_registry']
    if previous is not None:
        sealed_files({previous['path']: previous['sha256']}, root)
        previous_path = (root/previous['path']).resolve()
        require(previous_path not in _seen, 'Cyclic registry history')
        old = json.loads(previous_path.read_text())
        validate_registry(old, root, _seen | {previous_path})
        require(registry['checkpoint_version'] == old['checkpoint_version']+1, 'Registry versions must advance by one')
        require(all(registry['preserved_artifacts'].get(k) == v for k,v in old['preserved_artifacts'].items()), 'Do not rewrite historical fingerprints')
        for key in ('decisions', 'consumption_events'):
            require(registry[key][:len(old[key])] == old[key], f'{key} must be append-only')
        for holdout in old['holdouts']:
            current = [h for h in registry['holdouts'] if h['id'] == holdout['id']]
            require(len(current) == 1 and all(current[0][k] == holdout[k] for k in ('start','end','purpose')), 'Do not relabel or move a previous reservation')
            require(holdout['state'] != 'consumed' or current[0]['state'] == 'consumed', 'Consumed holdout cannot become reserved')
    else:
        require(registry['checkpoint_version'] == 1, 'Later registries must cite an immutable predecessor')
    decisions = registry['decisions']
    require(len({d['id'] for d in decisions}) == len(decisions), 'Decision IDs must be unique')
    sealed_files({d['path']: d['sha256'] for d in decisions}, root)
    for d in decisions:
        require(json.loads((root/d['path']).read_text())['candidate_id'] == d['id'], 'Decision identity mismatch')
    holdouts = registry['holdouts']
    require(len({h['id'] for h in holdouts}) == len(holdouts), 'Holdout IDs must be unique')
    reserved = [h for h in holdouts if h['id'] == '006-v1-reserved']
    require(len(reserved) == 1 and reserved[0]['start'] == '2025-01-01' and reserved[0]['end'] is None and reserved[0]['purpose'] == 'original_006_v1_only', 'Original open-ended holdout is protected')
    for h in holdouts:
        date.fromisoformat(h['start'])
        if h['end'] is not None:
            interval(h)
        require(h['state'] in ('reserved','consumed'), 'Unknown holdout state')
        events = [e for e in registry['consumption_events'] if e['holdout_id'] == h['id']]
        require((h['state'] == 'consumed') == bool(events), 'Consumption log/state mismatch; never relabel untouched')
    for index, h in enumerate(holdouts):
        start = date.fromisoformat(h['start']); end = date.fromisoformat(h['end']) if h['end'] else date.max
        for other in holdouts[index+1:]:
            a = date.fromisoformat(other['start']); b = date.fromisoformat(other['end']) if other['end'] else date.max
            require(end < a or b < start, 'Overlapping holdout reservations')
    for event in registry['consumption_events']:
        require(any(h['id'] == event['holdout_id'] for h in holdouts), 'Unknown consumed holdout')
        timestamp(event['accessed_at'])
        require(all(text(event[k]) for k in ('candidate_id','actor','purpose','evidence_ref')), 'Consumption attribution required')
    return registry


def validate_record(record, registry, root=ROOT):
    """Check a record against a registry already verified by validate_registry."""
    template = json.loads(TEMPLATE.read_text())
    def structure(value, schema, path='record'):
        if isinstance(schema, dict):
            require(isinstance(value, dict) and set(value) >= set(schema), f'Missing fields: {path}')
            for key in schema:
                structure(value[key], schema[key], path+'.'+key)
        elif schema is not None:
            require(type(value) is type(schema), f'Wrong field type: {path}')
    structure(record, template)
    require(record['schema_version'] == POLICY and record['champion_id'] == '006-v1', 'Frozen policy/champion ID')
    require(re.fullmatch(r'006-challenger-[a-z0-9-]+', record['candidate_id']) is not None, 'Versioned challenger ID required')
    require(type(record['record_version']) is int and record['record_version'] >= 1, 'Positive record version required')
    require(record['kind'] in ('template','candidate') and record['stage'] in ('proposal','preregistered'), 'Unknown record kind/stage')
    sealed = [d for d in registry['decisions'] if d['id'] == record['candidate_id']]
    for entry in sealed:
        require(record == json.loads((root/entry['path']).read_text()), 'Sealed decision ID cannot be reused with changed content; issue a new candidate ID')
    if record['stage'] == 'proposal':
        return ['Proposal only: not preregistered, not cleared for evaluation']
    require(record['kind'] == 'candidate', 'Templates cannot authorize preregistration')
    for key in ('hypothesis','exact_change','expected_failure_mode','known_limitation','monitoring_proposal','decision_record_requirements'):
        require(text(record[key]), f'Complete {key} before preregistration')
    registered, earliest = timestamp(record['registered_at']), timestamp(record['earliest_evaluation_at'])
    require(registered < earliest, 'Preregister before first evaluation/outcome access')
    require(re.fullmatch(r'[0-9a-f]{40}', record['preregistration_commit'] or '') is not None, 'Preregistration commit required')
    repro = record['reproducibility']
    require(re.fullmatch(r'[0-9a-f]{40}', repro['code_commit'] or '') is not None, 'Pinned code commit required')
    for key in ('config_sha256','environment_lock_sha256'):
        require(re.fullmatch(r'[0-9a-f]{64}', repro[key] or '') is not None, f'Pinned {key} required')
    require(text(repro['entrypoint']) and text(repro['seeds_and_streams']), 'Reproduction command and RNG discipline required')
    comparison = record['comparison']
    require(comparison['criteria_status'] == 'frozen', 'Proposed thresholds are not preregistered criteria')
    require(all(text(comparison[k]) for k in ('pass_rule','fail_rule','cost_assumptions','multiple_comparisons')), 'Freeze fair comparison and decision criteria')
    require(bool(comparison['metrics']) and all(text(m) for m in comparison['metrics']), 'Frozen metrics required')
    require({'006-v1 min-vol','006-v1 local max-Sharpe','equal weight'} <= set(comparison['benchmarks']), 'Preserve original comparators')
    info = record['training_information']
    decision = timestamp(info['decision_at'])
    for key in ('latest_observation_at','latest_publication_at','latest_revision_available_at'):
        require(timestamp(info[key]) <= decision, f'Temporal leakage: {key} after decision')
    retrieved = timestamp(info['snapshot_retrieved_at'])
    require(retrieved <= registered, 'Snapshot must be pinned by preregistration')
    for key in ('latest_observation_at','latest_publication_at','latest_revision_available_at'):
        require(timestamp(info[key]) <= retrieved, f'Snapshot predates declared input availability: {key}')
    require(retrieved <= decision or text(info['point_in_time_evidence']), 'Later retrieval needs historical-vintage availability evidence')
    for key in ('snapshot_sha256','manifest_sha256'):
        require(re.fullmatch(r'[0-9a-f]{64}', info[key] or '') is not None, f'Immutable {key} required')
    require(text(info['adjustment_vintage']), 'Publisher adjustment vintage required')
    eligibility = record['eligibility']
    rights = ['automation','analysis','retention','independent_comparison']
    if eligibility['publication_planned']:
        rights.append('public_derived_outputs')
    if eligibility['raw_distribution_planned']:
        rights.append('raw_redistribution')
    for key in rights:
        require(eligibility[key]['status'] == 'approved' and text(eligibility[key]['evidence']), f'Data-rights gate: {key}')
    require(text(eligibility['source_policy_approval_ref']) and text(eligibility['independent_verification_ref']), 'Existing source-policy and independent-verification gates remain required')
    periods = record['periods']
    train, validation, confirmation = (interval(periods[k]) for k in ('training','validation','confirmation'))
    require(train[1] <= decision.date() < validation[0], 'Training/decision must precede validation')
    require(train[1] <= timestamp(info['latest_observation_at']).date(), 'Training extends beyond declared observations')
    if periods['calibration'] is not None:
        calibration = interval(periods['calibration'])
        require(train[0] <= calibration[0] and calibration[1] <= decision.date() and calibration[1] < validation[0], 'Calibration leakage')
        require(calibration[1] <= timestamp(info['latest_observation_at']).date(), 'Calibration extends beyond declared observations')
    require(validation[1] < confirmation[0], 'Fresh confirmation must follow validation')
    holdout_id = periods['confirmation']['holdout_id']
    reservations = [h for h in registry['holdouts'] if h['id'] == holdout_id]
    require(len(reservations) == 1 and holdout_id != '006-v1-reserved', 'Original holdout cannot select or confirm challengers')
    h = reservations[0]
    require(h['state'] == 'reserved' and h['purpose'] == 'challenger_confirmation', 'Consumed/ineligible confirmation period')
    require(interval(h) == confirmation and text(h['owner_authorization_ref']), 'Confirmation needs an exact separately authorized reservation')
    # Different names do not make overlapping observations fresh.
    for other in registry['holdouts']:
        if other['id'] != holdout_id:
            a = date.fromisoformat(other['start']); b = date.fromisoformat(other['end']) if other['end'] else date.max
            require(confirmation[1] < a or b < confirmation[0], 'Confirmation overlaps an existing reserve/consumed period')
    owner = record['owner_preregistration_signoff']
    require(text(owner['reviewer']) and text(owner['evidence']) and timestamp(owner['at']) <= registered, 'Owner preregistration signoff required')
    return []


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--record', type=Path, default=TEMPLATE)
    parser.add_argument('--registry', type=Path, default=REGISTRY)
    parser.add_argument('--require-preregistered', action='store_true')
    args = parser.parse_args()
    try:
        registry = validate_registry(json.loads(args.registry.read_text()))
        blocked = validate_record(json.loads(args.record.read_text()), registry)
        print('PASS: structural checklist and historical fingerprints')
        print('; '.join(blocked) if blocked else 'Structurally consistent preregistration only; human review and existing source policy still control authorization.')
        print('No model, data retrieval, performance evaluation, holdout access or adoption executed.')
        return int(bool(blocked) and args.require_preregistered)
    except (ValueError, KeyError, TypeError, OSError) as exc:
        print(f'BLOCKED: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
