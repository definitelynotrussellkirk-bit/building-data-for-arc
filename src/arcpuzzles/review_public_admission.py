"""Owner registration and native acceptance of direct public-evaluation builds.

Authoring preflight never grants approval. Original examples, the ordinary
relocated generator, causal cases and the unchanged native engine are exercised
before a source-bound parent link leaves the creation queue.
"""
from __future__ import annotations

import copy
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sys
import tempfile
import zipfile

from .catalog import Catalog, local_path, sha256
from .review_public_creation import PUBLIC_WORK_SCHEMA, SOURCE, SOLUTIONS, digest, generator_id, reference_id, validate_reference_id

REGISTRY = 'REVIEW/public-eval-families-current.json'


def _write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    pending = path.with_suffix(path.suffix + '.tmp')
    pending.write_text(json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n')
    pending.replace(path)


def _regular(root, relative):
    if type(relative) is not str or '\\' in relative or '..' in PurePosixPath(relative).parts:
        raise ValueError('Invalid source path')
    path = local_path(root, relative)
    if (not path.is_file() or path.is_symlink()
            or any(p.is_symlink() for p in path.parents if p.is_relative_to(root))):
        raise ValueError('Missing regular same-checkout source: ' + relative)
    return path


def _parent(root, item):
    from .parametric_priority import _challenge
    pid = item['public_task_id']
    if item['task_id'] != generator_id(pid) or item['source_path'] != SOURCE:
        raise ValueError('Public parent identity differs from task home')
    raw = json.loads(_regular(root, SOURCE).read_text())[pid]
    gold_path = root / SOLUTIONS
    gold = json.loads(_regular(root, SOLUTIONS).read_text()).get(pid) if gold_path.exists() else None
    if (digest(raw) != item['source_record_sha256']
            or digest(_challenge(raw)) != item['challenge_sha256']
            or (digest(gold) if gold is not None else None) != item['test_outputs_sha256']):
        raise ValueError('Official public challenge/gold identity changed')
    result = copy.deepcopy(raw)
    if gold is not None:
        if len(gold) != len(result.get('test', [])):
            raise ValueError('Official public test count mismatch')
        for pair, output in zip(result['test'], gold):
            if 'output' in pair and pair['output'] != output:
                raise ValueError('Conflicting official gold')
            pair['output'] = output
    return result


def _check_binding(root, binding):
    if type(binding) is not dict:
        raise ValueError('Missing source binding')
    files = binding.get('files')
    if type(files) is not list or not files:
        raise ValueError('Missing source binding')
    seen = set()
    for row in files:
        if row['path'] in seen:
            raise ValueError('Duplicate source binding path')
        seen.add(row['path'])
        if sha256(_regular(root, row['path'])) != row['sha256']:
            raise ValueError('Integrated source differs from preflight: ' + row['path'])


def _reviewer_binding(root, tid, pid, binding):
    """Accept original bytes first; recover only a proven metadata-only retry."""
    try:
        _check_binding(root, binding)
        return binding
    except ValueError:
        from .review_public_compatibility import rebind_source_binding
        repaired = rebind_source_binding(root, tid, pid, binding)
        _check_binding(root, repaired)
        return repaired


def _verified_originals(root, evidence, item, parent, reference_sha256):
    """Verify retained owner execution receipts, not a stand-alone success flag."""
    from .review_public_creation import PREFLIGHT
    path = _regular(root, evidence['owner_preflight'])
    if sha256(path) != evidence['owner_preflight_sha256']:
        return False
    receipt = json.loads(path.read_text())
    if (receipt.get('schema') != PREFLIGHT or receipt.get('status') != 'passed'
            or receipt.get('public_creation') != item or receipt.get('task_id') != item['task_id']
            or receipt.get('owner_accepted') is not False
            or receipt.get('verification_status') != 'authoring_preflight_not_owner_qualification'):
        return False
    default = json.dumps(receipt['contract']['default'], sort_keys=True, separators=(',', ':'), ensure_ascii=False)
    if receipt['programs'].get(default) != reference_sha256:
        return False
    for name in ('original-pairs.json', 'execution.json'):
        member = _regular(root, (path.parent / name).relative_to(root).as_posix())
        if sha256(member) != receipt['evidence_sha256'][name]:
            return False
    original = json.loads((path.parent / 'original-pairs.json').read_text())
    grid = lambda value: [[int(cell) for cell in row] for row in value]
    expected = [{'split': split, 'index': index, 'input': grid(pair['input']), 'output': grid(pair['output'])}
                for split in ('train', 'test') for index, pair in enumerate(parent.get(split, [])) if 'output' in pair]
    return (bool(expected) and original.get('status') == 'passed'
            and original.get('public_creation') == item and original.get('pairs') == expected
            and original.get('racket', {}).get('backend') == 'racket'
            and original.get('racket', {}).get('protected') is True)


def verified_coverage(root, *, _candidate_ids=None):
    """Count only exact current accepted families with owner-executed originals."""
    from . import parametric_promotion as native
    root = Path(root).resolve()
    path = root / REGISTRY
    if not path.is_file():
        return []
    try:
        registry = json.loads(_regular(root, REGISTRY).read_text())
    except (ValueError, OSError):
        return []
    if (type(registry) is not dict or registry.get('schema') != 'arcpuzzles-public-eval-coverage-v1'
            or type(registry.get('parents')) is not dict):
        return []
    catalog = Catalog(root)
    covered = []
    for pid, entry in registry.get('parents', {}).items():
        if _candidate_ids is not None and pid not in _candidate_ids:
            continue
        try:
            item = entry['public_creation']; tid = item['task_id']
            if pid != item['public_task_id'] or entry.get('status') != 'accepted':
                continue
            parent = _parent(root, item)
            proof = entry['owner_evidence']
            evidence_path = _regular(root, proof['path'])
            if sha256(evidence_path) != proof['sha256']:
                continue
            evidence = json.loads(evidence_path.read_text())
            if (evidence.get('status') != 'accepted' or evidence.get('objective_met') is not True
                    or evidence.get('public_creation') != item
                    or evidence.get('originals_owner_executed') is not True
                    or evidence.get('task_id') != tid
                    or evidence.get('acceptance_sha256') != entry['acceptance_sha256']
                    or evidence.get('reference_sha256') != entry['reference_sha256']
                    or not _verified_originals(root, evidence, item, parent, entry['reference_sha256'])):
                continue
            current = native.status(catalog, tid)
            if (current.get('status') == 'accepted'
                    and current.get('acceptance_sha256') == entry['acceptance_sha256']
                    and sha256(_regular(root, f'generators/{tid}/reference.rkt')) == entry['reference_sha256']):
                covered.append(pid)
        except (ValueError, KeyError, OSError, TypeError, AttributeError):
            continue
    return sorted(covered)


def _register(catalog, item, parent, program):
    """Validate all proposed source/catalog mappings before transactional writes."""
    from .review import _lock
    from .review_approval import generator_metadata
    root = catalog.root; tid = item['task_id']; home = f'generators/{tid}'
    authority = validate_reference_id(_regular(root, home + '/generator.py'), item['public_task_id'])
    with _lock(root / 'REVIEW'):
        fresh = Catalog(root)
        records = [dict(row) for row in fresh._records.values()]
        old = next((r for r in records if r['id'] == tid), None)
        if old and old.get('semantic_veto'):
            raise ValueError('Active semantic veto requires explicit disposition')
        if old:
            prior = old.get('public_creation', {})
            keys = ('public_task_id', 'task_id', 'source_path', 'challenge_sha256',
                    'source_record_sha256', 'test_outputs_sha256')
            if any(prior.get(key) != item.get(key) for key in keys):
                raise ValueError('Existing catalog parent identity differs')
        all_variants = fresh._variants()
        variants = all_variants.get(authority, [])
        legacy = all_variants.get(tid, [])
        migrate = old is not None and old.get('rule_task_id') == tid
        provenance_keys = ('public_task_id', 'task_id', 'source_path', 'challenge_sha256',
                           'source_record_sha256', 'test_outputs_sha256')
        def own_original(row):
            return (row.get('source') == 'evaluation' and row.get('source_task_id') == item['public_task_id']
                    and row.get('program_solution') == program
                    and all(row.get('public_creation', {}).get(k) == item.get(k) for k in provenance_keys)
                    and all(row.get(split) == parent.get(split) for split in ('train', 'test')))
        if any(r['id'] != tid and r.get('rule_task_id', r['id']) == authority for r in records):
            raise ValueError('Public reference authority already belongs to another catalog row')
        if migrate:
            if (old.get('generator') != home + '/generator.py'
                    or old.get('runtime_generator') != f'puzzle_generators/per_puzzle/{tid}/generator.py'
                    or old.get('family') != 'official:evaluation' or old.get('split') != 'evaluation'
                    or old.get('parent_ids') != [item['public_task_id']]
                    or old.get('train_safety') != 'unverified' or old.get('mix_weight') != 0
                    or old.get('review_status') != 'owner_registration_pending'
                    or old.get('reviewed_generator_sha256') or old.get('reviewed_rule_hash')
                    or fresh.describe(tid).get('approved')
                    or (root/home/'parametric/accepted.json').exists()
                    or not legacy or variants or not all(own_original(v) for v in legacy)):
                raise ValueError('Only exact never-approved public owner placeholders may migrate reference identity')
        elif legacy or old is not None and old.get('rule_task_id') != authority:
            raise ValueError('Existing public reference authority requires explicit reconciliation')
        if variants and not all(own_original(v) for v in variants):
            raise ValueError('Existing canonical reference/provenance differs; requires explicit owner reconciliation')
        metadata = generator_metadata(_regular(root, home + '/generator.py'))
        canonical = root / 'shared/data/canonical/puzzles.jsonl'
        mappings_path = root / 'catalog/runtime_files.json'
        catalog_path = root / 'catalog/puzzles.jsonl'
        mappings = json.loads(mappings_path.read_text())
        mappings = [m for m in mappings if not m['path'].startswith(home + '/parametric/')]
        target = f'puzzle_generators/per_puzzle/{tid}/generator.py'
        # Preserve adjacent sampler/rule resources in the relocated base layout.
        # Evidence and tests remain private retained assets, not runtime imports.
        expected = []
        for source in sorted((root / home).rglob('*')):
            relative = source.relative_to(root / home)
            if relative.parts[0] == 'parametric':
                continue  # Owner acceptance receipts are not generator runtime dependencies.
            if any(p in {'evidence', 'examples', 'tests', 'counterexamples', '__pycache__'} for p in relative.parts):
                continue
            if source.is_file() and source.suffix in {'.py', '.rkt', '.json'}:
                name = source.relative_to(root).as_posix()
                _regular(root, name)
                expected.append({'path': name, 'target': f'puzzle_generators/per_puzzle/{tid}/' + relative.as_posix()})
        targets = set()
        for mapping in mappings:
            if mapping['target'] in targets:
                raise ValueError('Duplicate runtime target before registration')
            targets.add(mapping['target'])
        for wanted in expected:
            if any(m['target'] == wanted['target'] and m != wanted for m in mappings):
                raise ValueError('Conflicting runtime generator mapping')
            if wanted not in mappings:
                mappings.append(wanted)
        changes = {}
        provenance = {
            'content_hash': digest({'public_task_id': item['public_task_id'],
                                    'source_record_sha256': item['source_record_sha256'],
                                    'test_outputs_sha256': item['test_outputs_sha256'],
                                    'program_solution': program}),
            'parent_hash': item['public_task_id'],
            'solution_language': 'racket', 'needs_conversion': False,
        }
        if migrate:
            lines = []
            for line in canonical.read_bytes().splitlines(keepends=True):
                row = json.loads(line)
                if row.get('task_id') == tid:
                    row['task_id'] = authority
                    for key, value in provenance.items():
                        if row.get(key) in (None, '', '?'):
                            row[key] = value
                    line = (json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n').encode()
                lines.append(line)
            changes[canonical] = b''.join(lines)
            migrated = {**old, 'rule_task_id': authority}
            lines = []
            for line in catalog_path.read_bytes().splitlines(keepends=True):
                if json.loads(line).get('id') == tid:
                    line = (json.dumps(migrated, ensure_ascii=False, allow_nan=False) + '\n').encode()
                lines.append(line)
            changes[catalog_path] = b''.join(lines)
        elif not variants:
            record = {'task_id': authority, 'source': 'evaluation', 'source_task_id': item['public_task_id'],
                      'title': '', 'difficulty': '', 'skills': [], 'written_solution': '',
                      **parent, 'program_solution': program, 'public_creation': item, **provenance}
            changes[canonical] = canonical.read_bytes().rstrip(b'\n') + b'\n' + (json.dumps(record, ensure_ascii=False, allow_nan=False) + '\n').encode()
        else:
            lines = []
            for line in canonical.read_bytes().splitlines(keepends=True):
                row = json.loads(line)
                if row.get('task_id') == authority:
                    before = dict(row)
                    for key, value in provenance.items():
                        if row.get(key) in (None, '', '?'):
                            row[key] = value
                    if row != before:
                        line = (json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n').encode()
                lines.append(line)
            if b''.join(lines) != canonical.read_bytes():
                changes[canonical] = b''.join(lines)
        changes[mappings_path] = (json.dumps(mappings, sort_keys=True, indent=2, allow_nan=False) + '\n').encode()
        if old is None:
            row = {'id': tid, 'kind': 'per_puzzle', 'summary': '', 'version': '1.0.0', **metadata,
                   'sources': ['evaluation', 'public_eval:' + item['public_task_id']],
                   'skills': [], 'difficulties': [], 'primitives': [], 'aliases': [item['public_task_id']],
                   'canonical_rows': 1, 'generator': home + '/generator.py', 'runtime_generator': target,
                   'rule_task_id': authority, 'family': 'official:evaluation', 'split': 'evaluation',
                   'parent_ids': [item['public_task_id']], 'public_creation': item,
                   'train_safety': 'unverified', 'mix_weight': 0, 'semantic_veto': False,
                   'veto_reason': '', 'review_status': 'owner_registration_pending', 'notes_count': 1}
            changes[catalog_path] = catalog_path.read_bytes().rstrip(b'\n') + b'\n' + (json.dumps(row, ensure_ascii=False, allow_nan=False) + '\n').encode()
        originals = {path: path.read_bytes() for path in changes}
        written = []
        try:
            for path, raw in changes.items():
                pending = path.with_suffix(path.suffix + '.public.tmp')
                pending.write_bytes(raw)
                os.replace(pending, path)
                written.append(path)
        except Exception:
            for path in written:
                path.write_bytes(originals[path])
            raise
        finally:
            for path in changes:
                path.with_suffix(path.suffix + '.public.tmp').unlink(missing_ok=True)
    return Catalog(root)


def _approve(catalog, tid):
    from .review import _lock
    root = catalog.root
    with _lock(root / 'REVIEW'):
        fresh = Catalog(root); selected = fresh.describe(tid)
        if selected.get('semantic_veto'):
            raise ValueError('Active semantic veto')
        rows = [dict(r) for r in fresh._records.values()]
        for row in rows:
            if row['id'] == tid:
                row.update(train_safety='reviewed_safe', mix_weight=1.0,
                           reviewed_generator_sha256=selected['generator_sha256'],
                           reviewed_rule_hash=selected['rule_hash'],
                           review_status='owner_public_originals_and_relocated_base_executed')
        path = root / 'catalog/puzzles.jsonl'; pending = path.with_suffix('.tmp')
        pending.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows)); pending.replace(path)
    return Catalog(root)


# Preserve the owner helper's existing import/API for callers and tests.
from .review_programs import strict_programs as _strict_programs


def accept_public_creation(catalog, contract, progress, read):
    """Shared owner path for return intake and an explicitly reviewed local build."""
    from . import parametric_promotion as native
    from .parametric_manifest import build_manifest
    from .review_parametric_admission import validate_sequential_witness, qualification_demo_count
    from .review_public_creation import validate_preflight
    from .review_sequential_replay import replay_witness
    from .review_public_compatibility import repair_reference_id, rebind_source_binding
    from .runtime import run_process
    root = catalog.root; tid = contract['task_id']; item = contract['generator']['public_creation']
    if tid != item['task_id']:
        raise ValueError('Assigned public identity mismatch')
    parent = _parent(root, item)
    descriptor = json.loads(_regular(root, f'generators/{tid}/workspace/public-eval-creation.json').read_text())
    if descriptor != {'schema': PUBLIC_WORK_SCHEMA, **item, 'reference_program': 'reference.rkt',
                      'promotion_manifest': 'workspace/parametric/promotion.json'}:
        raise ValueError('Public creation descriptor differs from assignment')
    reported = json.loads(read(progress['preflight_path']))
    inventory = {'repo/' + r['path'] for r in reported.get('source_binding', {}).get('files', [])}
    reported = validate_preflight(contract, progress, read, inventory)
    # Old issued packets lacked the safe authority literal. Only a retained,
    # reversible metadata edit may explain that one source-hash transition.
    checked_binding = _reviewer_binding(root, tid, item['public_task_id'], reported['source_binding'])
    _check_binding(root, checked_binding)
    causal = validate_sequential_witness(progress, reported, read)
    witness = json.loads(read(progress['sequential_dependency']['witness_path']))
    program = _regular(root, f'generators/{tid}/reference.rkt').read_text()
    _strict_programs(root, [program, *[case[key] for case in witness['cases']
                                     for key in ('program', 'counterfactual_program')]])
    home = root / f'generators/{tid}'
    base = home / 'evidence/public-owner'
    base.mkdir(parents=True, exist_ok=True)
    # Distinct permanent evidence folder: native manifest must not bind transient scratch.
    folder = base / digest({'binding': reported['source_binding'], 'programs': reported['programs']})
    if folder.exists():
        folder = Path(tempfile.mkdtemp(prefix=folder.name[:12] + '-', dir=base))
    else:
        folder.mkdir()
    out = folder / 'preflight'
    reference_repair = repair_reference_id(root, tid, item['public_task_id'])
    expected_binding = rebind_source_binding(root, tid, item['public_task_id'],
                                             reported['source_binding'], reference_repair)
    process = run_process([sys.executable, '-m', 'arcpuzzles.review_public_creation', 'preflight', tid,
                           '--root', str(root), '--out', str(out)], root, timeout=180,
                          extra_env={'PYTHONPATH': str(Path(__file__).resolve().parents[1]),
                                     'PYTHONNOUSERSITE': '1', 'PYTHONDONTWRITEBYTECODE': '1'})
    _write(folder / 'preflight-process.json', process)
    if process['timed_out'] or process['exit_code'] != 0:
        raise ValueError('Owner public preflight failed: ' + process['stderr'][-1600:] + process['stdout'][-1000:])
    fresh = json.loads((out / 'preflight.json').read_text())
    if (fresh['source_binding'] != expected_binding or fresh['programs'] != reported['programs']
            or fresh['contract'] != reported['contract']):
        raise ValueError('Owner execution differs from reported source/programs')
    executed = json.loads((out / 'execution.json').read_text())
    _strict_programs(root, [episode['program_solution'] for episode in executed['episodes']])
    live = _register(catalog, item, parent, program)
    demos = qualification_demo_count(fresh['contract'])
    episodes = live.generate(tid, seed=29, n_train=demos, n_test=4, allow_unapproved=True)
    _write(folder / 'relocated-base.json', {'status': 'passed', 'episodes': episodes,
                                         'scope': 'Normal base generator from copied runtime with protected canonical labels'})
    _check_binding(root, fresh['source_binding'])
    causal['owner_execution'] = replay_witness(root, witness)
    _write(folder / 'causal-replay.json', causal)
    live = _approve(live, tid)
    manifest = home / 'workspace/parametric/evidence/manifest.json'
    build_manifest(live, tid, evidence=folder.relative_to(root).as_posix(),
                   reported_checks='Owner executed original labelled pairs, fresh authoring preflight, relocated base and causal witness; native qualification follows.',
                   include=[f'generators/{tid}/tests'] if (home / 'tests').is_dir() else [],
                   replace_sha256=sha256(manifest) if manifest.exists() else None)
    native_contract, binding = native._ready(Catalog(root), tid)
    witness = {**witness, 'source_binding': binding}
    _write(folder / 'native-bound-witness.json', witness)
    if native._ready(Catalog(root), tid)[1] != binding:
        raise ValueError('Native source binding changed while retaining causal evidence')
    # Binding changes only by registration: every intended program is checked again below.
    scratch = root / 'var/review/public-native-admission'; scratch.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=tid + '-', dir=scratch) as directory:
        qualified = native.qualify(Catalog(root), tid, Path(directory) / 'qualification', demos=demos)
        if qualified['source_binding'] != binding:
            raise ValueError('Native source binding changed during qualification')
        if qualified['programs'] != fresh['programs']:
            raise ValueError('Native program map differs from original-pair-checked family')
        accepted = native.accept(Catalog(root), tid, qualified['receipt'],
                                 reason='Direct public task: owner original-pair/base/causal execution and fresh native acceptance')
    current = native.status(Catalog(root), tid)
    if accepted.get('status') != 'accepted' or current.get('status') != 'accepted':
        raise ValueError('Native public family acceptance did not remain current')
    return {'status': 'accepted', 'objective_met': True, 'task_id': tid, 'public_creation': item,
            'originals_owner_executed': True, 'acceptance_sha256': current['acceptance_sha256'],
            'reference_sha256': hashlib.sha256(program.encode()).hexdigest(),
            'source_binding': binding, 'sequential_dependency': causal,
            'owner_reference_compatibility': reference_repair,
            'owner_preflight': (out / 'preflight.json').relative_to(root).as_posix(),
            'owner_preflight_sha256': sha256(out / 'preflight.json'),
            'training_admitted': False, 'verification_status': 'owner_native_admission'}


def record_coverage(root, result, evidence_path):
    from .review import _lock
    root = Path(root)
    if result.get('status') != 'accepted' or result.get('objective_met') is not True:
        return
    with _lock(root / 'REVIEW'):
        path = root / REGISTRY
        registry = json.loads(path.read_text()) if path.exists() else {'schema': 'arcpuzzles-public-eval-coverage-v1', 'parents': {}}
        item = result['public_creation']
        # The current admission report may later become blocked. Keep the exact
        # accepted receipt independently so that history cannot overwrite proof.
        proof = root / f"generators/{item['task_id']}/evidence/public-coverage/{digest(result)}.json"
        _write(proof, result)
        registry['parents'][item['public_task_id']] = {k: result[k] for k in
            ('status', 'public_creation', 'acceptance_sha256', 'reference_sha256')}
        registry['parents'][item['public_task_id']]['owner_evidence'] = {
            'path': proof.relative_to(root).as_posix(), 'sha256': sha256(proof)}
        _write(path, registry)


def admit_public_creation(catalog, contract, target_report, archive_path, *, withheld_paths=()):
    from .review_parametric_admission import evidence_reader
    tid = contract['task_id']
    result = {'schema': 'arcpuzzles-review-public-parametric-admission-v1', 'task_id': tid,
              'assignment_id': contract['assignment_id'], 'status': 'blocked', 'objective_met': False,
              'return_sha256': sha256(Path(archive_path)), 'training_admitted': False}
    try:
        progress = target_report.get('parametric_work', {})
        if progress.get('status') != 'ready' or withheld_paths:
            raise ValueError('Public deliverable not ready or source withheld')
        preflight = progress['preflight_path']; witness = progress['sequential_dependency']['witness_path']
        paths = [preflight, witness] + [str(PurePosixPath(preflight).parent / n) for n in ('execution.json', 'original-pairs.json')]
        with zipfile.ZipFile(archive_path) as archive:
            read = evidence_reader(archive, paths)
            result.update(accept_public_creation(catalog, contract, progress, read))
    except (ValueError, KeyError, OSError, RuntimeError, TypeError, AttributeError, SyntaxError) as exc:
        result.update(blocker=f'{type(exc).__name__}: {exc}',
                      next_action='Repair this exact public family and retry owner registration/native admission; public coverage remains unmet.')
    path = catalog.root / f'generators/{tid}/evidence/parametric-admission-current.json'
    _write(path, result)
    record_coverage(catalog.root, result, path)
    return {**result, 'evidence_path': str(path)}
