"""First-class, unapproved public-evaluation family creation.

Preflight is source-bound authoring evidence. Only owner registration, review,
unchanged native qualification and fresh acceptance establish coverage.
"""
from __future__ import annotations
import argparse
import ast
import copy
import hashlib
import importlib.util
import inspect
import itertools
import json
from pathlib import Path
import re
import sys

PUBLIC_WORK_SCHEMA = 'arcpuzzles-public-eval-creation-v1'
PUBLIC_WORK_POLICY = {'schema': PUBLIC_WORK_SCHEMA, 'roles': ['public_eval_creation', 'public_eval_creation'],
    'priority': 'uncovered_public_evaluation_first', 'peer_work': 'none',
    'completion': 'both_native_owner_accepted', 'demonstration_range': [2, 6],
    'training_queries': 4, 'query_visibility': 'sequential_without_total_count_hint',
    'missing_reference': 'must_author_general_racket_rule'}
PUBLIC_LEGACY_WORK_POLICY = PUBLIC_WORK_POLICY
PUBLIC_WORK_POLICY = {**PUBLIC_LEGACY_WORK_POLICY,
    'priority': 'uniform_all_public_until_half_covered_then_uncovered_first'}
SOURCE = 'shared/data/raw/arc-agi_evaluation_challenges.json'
SOLUTIONS = 'shared/data/raw/arc-agi_evaluation_solutions.json'
PREFLIGHT = 'arcpuzzles-public-eval-authoring-preflight-v1'


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                         separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def generator_id(public_task_id):
    if type(public_task_id) is not str or not re.fullmatch('[0-9a-f]{8}', public_task_id):
        raise ValueError('Invalid public evaluation task ID')
    return 'public_eval_' + public_task_id


def reference_id(public_task_id):
    """Canonical authority uses the frozen runner's hexadecimal/underscore charset."""
    generator_id(public_task_id)
    return 'ee_' + public_task_id


def validate_reference_id(generator_path, public_task_id):
    expected = reference_id(public_task_id)
    declarations = []
    for statement in ast.parse(Path(generator_path).read_bytes()).body:
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            targets = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
            if any(isinstance(target, ast.Name) and target.id == 'RULE_TASK_ID' for target in targets):
                declarations.append(statement.value)
    if (len(declarations) != 1 or not isinstance(declarations[0], ast.Constant)
            or declarations[0].value != expected):
        raise ValueError(f"Public generator requires literal RULE_TASK_ID = {expected!r}")
    return expected


def authoring_contract(root, task_id):
    """Check the existing native source/resource contract before Racket work."""
    from .parametric_manifest import _contract
    root = Path(root)
    return _contract(root, root / 'generators' / task_id)[0]


def creation_queue(root, *, fast=False, verification=None):
    """Retain every public parent; manifest policy determines the coverage phase."""
    from .parametric_priority import _challenge
    root = Path(root)
    path = root / SOURCE
    if not path.is_file():
        return []
    parents = json.loads(path.read_text())
    # Owner coverage helper may supply a stricter current-source verifier.
    coverage = set()
    try:
        from .review_public_admission import verified_coverage
    except ImportError:
        pass
    else:
        if fast:
            from .review_public_coverage_cache import fast_coverage
            covered, receipt = fast_coverage(root)
            coverage = set(covered)
        else:
            coverage = set(verified_coverage(root))
            receipt = {'mode': 'full', 'basis': 'unchanged_full_verification'}
        if verification is not None:
            verification.update(receipt)
    solution_path = root / SOLUTIONS
    solutions = json.loads(solution_path.read_text()) if solution_path.is_file() else {}
    missing = set(parents) - coverage
    pool = set(parents)
    return [{'public_task_id': pid, 'task_id': generator_id(pid),
             'source_path': SOURCE, 'challenge_sha256': digest(_challenge(parents[pid])),
             'source_record_sha256': digest(parents[pid]),
             'test_outputs_sha256': digest(solutions[pid]) if pid in solutions else None,
             'needs_creation': pid in missing}
            for pid in sorted(pool)]



def allocation_policy(queue):
    count = len(queue)
    covered = sum(row.get('needs_creation') is False for row in queue)
    cutoff = (count + 1) // 2
    return {'source_count': count, 'verified_covered_count': covered,
            'coverage_cutoff': cutoff,
            'allocation_phase': 'uniform_all_public' if covered < cutoff else 'uncovered_first'}


def _authoring_source(relative):
    parts = relative.parts
    if any(p in {'__pycache__', '.pytest_cache', '.git'} for p in parts):
        return False
    if parts[0] in {'evidence', 'parametric'} or ('evidence' in parts and parts[0] != 'tests'):
        return False
    return relative.suffix in {'.py', '.rkt', '.json', '.md'}


def add_creation_sources(root, files, queue):
    """Add unapproved authoring homes; these are not runtime catalog records."""
    root = Path(root)
    staging = root / 'var/review/public-creation-sources'
    staging.mkdir(parents=True, exist_ok=True)
    files['repo/' + SOURCE] = root / SOURCE
    if (root / SOLUTIONS).is_file():
        files['repo/' + SOLUTIONS] = root / SOLUTIONS
    rows = {}
    for item in queue:
        tid = item['task_id']; home = f'generators/{tid}/'
        existing = root / home
        for name in list(files):
            if name.startswith('repo/' + home) and not _authoring_source(Path(name.removeprefix('repo/' + home))):
                files.pop(name)
        if existing.is_dir():
            for source in existing.rglob('*'):
                if source.is_file() and not source.is_symlink() and _authoring_source(source.relative_to(existing)):
                    files['repo/' + source.relative_to(root).as_posix()] = source
        provenance = {'schema': 'arcpuzzles-public-eval-creation-target-v1', **item,
                      'approved': False, 'owner_registration_required': True}
        path = staging / tid / 'public-parent.json'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(provenance, sort_keys=True, indent=2) + '\n')
        files['repo/' + home + 'workspace/public-parent.json'] = path
        rows[tid] = {'generator': home + 'generator.py', 'generator_sha256': None,
            'rule_task_id': reference_id(item['public_task_id']), 'rule_hash': None, 'approved': False,
            'job_kind': 'public_eval_creation', 'public_creation': item}
    return rows


def select(manifest, seed):
    policy = manifest.get('public_eval_creation', {})
    pool = policy.get('ids')
    if (manifest.get('work_policy') not in (PUBLIC_WORK_POLICY, PUBLIC_LEGACY_WORK_POLICY) or not isinstance(pool, list)
            or len(pool) < 2 or pool != sorted(set(pool))
            or any(manifest['generators'].get(t, {}).get('job_kind') != 'public_eval_creation' for t in pool)):
        raise ValueError('Invalid public evaluation creation policy')
    missing = [t for t in pool if manifest['generators'][t]['public_creation'].get('needs_creation', True)]
    phase = policy.get('allocation_phase', 'uncovered_first')
    if 'allocation_phase' in policy:
        expected = allocation_policy([manifest['generators'][tid]['public_creation'] for tid in pool])
        if any(policy.get(key) != value for key, value in expected.items()):
            raise ValueError('Public allocation phase or cutoff differs from frozen coverage')
    remaining = (missing if phase == 'uncovered_first' and len(missing) >= 2 else pool).copy(); chosen = []
    for slot in range(2):
        attempt = 0; limit = 2**256 - (2**256 % len(remaining))
        while True:
            value = int.from_bytes(hashlib.sha256(seed + f':public-create:{slot}:{attempt}'.encode()).digest(), 'big')
            if value < limit:
                break
            attempt += 1
        tid = missing[0] if phase == 'uncovered_first' and slot == 0 and len(missing) == 1 else remaining[value % len(remaining)]
        remaining.remove(tid)
        chosen.append({'task_id': tid, 'generator': manifest['generators'][tid]})
    return chosen


def duties(contract):
    targets = '\n'.join(f"- `{r['task_id']}` from official public parent `{r['generator']['public_creation']['public_task_id']}`; challenge SHA-256 `{r['generator']['public_creation']['challenge_sha256']}`."
                        for r in contract['repair_targets'])
    return f'''# Create two accepted public-evaluation parametric families

Assignment `{contract['assignment_id']}`. ALL 120 supplied public-evaluation parents
are the first priority. Until 60 distinct parents have accepted families, ALL
120 remain equally likely, with two draws without replacement. At 60 accepted
parents the next published packet switches to uncovered-first selection. A target
may already be covered: improve complementary settings or sampler branches;
the owner preserves its current acceptance until source reconciliation. No ordinary repair, inspiration-only substitute, peer audit or extra
solve fulfills this assignment. Finish and self-review each full build.

{targets}

1. Read each exact parent in `repo/{SOURCE}` and its immutable
   `repo/generators/TASK/workspace/public-parent.json`. If no valid general Racket
   rule exists, YOU MUST CREATE ONE in `reference.rkt`. A missing rule
   is the work, not a reason to substitute another task. Infer a general rule,
   never a lookup of supplied grids or answers. Execute every supplied labelled
   example AND all provided test gold in author-private `repo/{SOLUTIONS}`.
   Preserve existing valid reference bytes. Only genuinely unlabelled queries
   remain unverified. Never put gold labels in model-visible challenges.
2. Create `generator.py` with literal `RULE_TASK_ID = 'ee_PUBLIC_TASK_ID'`
   (replace PUBLIC_TASK_ID with the eight-hex parent ID), current `notes.md`,
   focused tests, and a full native
   `workspace/parametric/adapter.py` plus `promotion.json`. The default program
   must exactly equal `reference.rkt`. Keep a byte-identical `canonical.rkt`
   inside `workspace/parametric/` and have the adapter read that copy: native
   resources must all stay inside that folder. Preserve the original reasoning;
   add meaningful episode-fixed parameters, fresh generated examples and a real
   input-dependent A -> intermediate -> B dependency. Read PARAMETRIC-RULES.md
   and the native adapter contract in repo/docs/parametric-promotion.md.
3. Support the family's smallest teachable demonstration count within 2–6 and
   ALWAYS four distinct novel queries. Randomize presentation independently of
   query ordinal; reveal one query at a time without a total-count hint. Keep
   settings, programs, answers and future queries private. Demonstrations must
   defeat plausible wrong rules; adversarially self-review sampler boundaries,
   causal counterfactuals, label execution and private/public exports. Retain
   compact evidence, meaningful rivals, exact seeds and concrete limits.
4. Run `python3 setup_racket.py`, then for EACH TASK:
   `python3 run_with_racket.py python3 -m arcpuzzles.review_public_creation preflight TASK --root . --out ../checks/TASK/preflight`.
   This protected-Racket authoring preflight requires no approved base and grants
   NO owner qualification or acceptance. All programs must parse as one complete
   rule! or lambda expression before execution. Use the shared review_witness CLI
   with --public-preflight ../checks/TASK/preflight/preflight.json for causal
   template/build/check commands (see PARAMETRIC-RULES.md). Fix failures. Keep a source-bound
   sequential witness and self-adversarial/public-export evidence under checks/TASK/.
   Reuse `python3 ../preview_public.py export --public-preflight ../checks/TASK/preflight/preflight.json --out ../checks/TASK/preview`
   from repo/, then `python3 ../preview_public.py verify --bundle ../checks/TASK/preview`.
   The shared `check_first_turn.py` also accepts this bundle. Do not write a
   task-local exporter or privacy checker to duplicate these tools. Training uses
   the native adapter; spend task-local effort on meaningful sampler variation,
   teaching examples, plausible wrong rules and causal counterfactuals.
5. For each RESULTS.json repair_targets row, declare outcome, summary,
   changed_components, evidence_paths, remaining_failures, and parametric_work:
   status ready/blocked, summary, prototype_path, promotion_path, inventory_path,
   preflight_path (`checks/TASK/preflight/preflight.json`), and sequential_dependency
   (step_a, intermediate, step_b, why_b_depends_on_a, witness_path). Use repo-rooted
   source paths; preflight writes the task-local inventory. Include preflight,
   execution.json, original-pairs.json, causal and adversarial/export evidence in
   evidence_paths. Complete means BOTH reviewer-ready; owner acceptance is pending.
6. Package one compact delta with REVIEW.md and FEEDBACK_TO_CODEX.md using
   `python3 package_return.py --out review_response_{contract['assignment_id']}.zip`.
   The owner registers exact source/provenance, accepts its source review, then
   runs unchanged native qualification and fresh acceptance separately for BOTH.
   Only actual current native accepted source with official-pair execution and
   verified parent linkage counts toward 120/120. One acceptance is partial.

Overlapping public-parent work is useful: preserve a faithful existing canonical
default and retain complementary settings or sampler branches for owner union.
A source collision requires explicit owner reconciliation, never silent overwrite
or discarding a useful branch. No global reservation prevents this work.
This ZIP freezes its phase and coverage count; owner refresh changes the phase
only at the manifest's half-source cutoff (60 of the real 120 parents).
Separate copies may overlap. Resuming preserves this draw.
'''


def validate_preflight(contract, progress, read, inventory):
    tid = contract['task_id']; target = contract['generator']['public_creation']
    receipt = json.loads(read(progress['preflight_path']))
    if (receipt.get('schema') != PREFLIGHT or receipt.get('status') != 'passed'
            or receipt.get('verification_status') != 'authoring_preflight_not_owner_qualification'
            or receipt.get('task_id') != tid or receipt.get('public_creation') != target
            or receipt.get('owner_accepted') is not False):
        raise ValueError('Invalid public creation authoring preflight')
    binding = receipt.get('source_binding', {})
    if binding.get('task_id') != tid or not binding.get('files'):
        raise ValueError('Preflight lacks source binding')
    for row in binding['files']:
        if ('repo/' + row['path'] not in inventory or not re.fullmatch('[0-9a-f]{64}', row['sha256'])):
            raise ValueError('Preflight cites missing source')
    for filename in ('execution.json', 'original-pairs.json'):
        path = str(Path(progress['preflight_path']).parent / filename)
        raw = read(path)
        if hashlib.sha256(raw).hexdigest() != receipt['evidence_sha256'][filename]:
            raise ValueError('Preflight evidence hash changed')
    originals = json.loads(read(str(Path(progress['preflight_path']).parent / 'original-pairs.json')))
    if originals.get('status') != 'passed' or not originals.get('pairs'):
        raise ValueError('All original labelled pairs must pass')
    return receipt


def _base_generation(module, apply, program):
    """Exercise the ordinary worker API without catalog registration or approval."""
    from .parametric_worker import _grid
    if not callable(getattr(module, 'generate', None)):
        raise ValueError('Base generator must export callable generate')
    checks = []
    # Probe the ordinary worker default before the explicit medium setting,
    # retaining the existing two-draw budget. Both APIs must accept None.
    for index, (seed, difficulty) in enumerate(((17, None), (43, 'medium'))):
        generated = module.generate(seed=seed, sample_index=index, difficulty=difficulty)
        # Match worker._generate_episodes: metadata tuples are not input grids.
        grid = _grid(generated.get('input') if isinstance(generated, dict) else generated)
        checker = getattr(module, 'self_check', None)
        if callable(checker):
            checked = copy.deepcopy(grid)
            signature = inspect.signature(checker)
            supports_difficulty = 'difficulty' in signature.parameters or any(
                p.kind == inspect.Parameter.VAR_KEYWORD for p in signature.parameters.values())
            findings = checker(checked, **({'difficulty': difficulty} if supports_difficulty else {}))
            if findings:
                raise ValueError(f'Base generator self_check: {findings}')
            if _grid(checked) != grid:
                raise ValueError('Base generator self_check mutated its input')
        output = _grid(apply(program, copy.deepcopy(grid)))
        checks.append({'seed': seed, 'sample_index': index, 'difficulty': difficulty,
                       'input': grid, 'output': output, 'self_check_run': callable(checker)})
    return checks


def preflight(root, tid, out):
    """Execute new unapproved source through protected Racket; never approve it."""
    from .parametric_worker import _local_imports, _real_evaluator, _grid
    from .parametric_promotion import settings_space
    from .parametric_priority import _challenge
    root = Path(root).resolve(); out = Path(out).resolve()
    if not re.fullmatch(r'public_eval_[0-9a-f]{8}', tid):
        raise ValueError('Invalid public creation task ID')
    def regular(path):
        path = Path(path)
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root):
            raise ValueError('Preflight source must be a regular same-checkout file: ' + str(path))
        if any(parent.is_symlink() for parent in path.parents if parent != root and parent.is_relative_to(root)):
            raise ValueError('Preflight source has a symlink parent')
        return path
    home = root / 'generators' / tid
    target = json.loads(regular(home / 'workspace/public-parent.json').read_text())
    item = {k: target[k] for k in ('public_task_id', 'task_id', 'source_path', 'challenge_sha256', 'source_record_sha256', 'test_outputs_sha256', 'needs_creation')}
    solutions_path = root / SOLUTIONS
    solutions = json.loads(regular(solutions_path).read_text()) if solutions_path.is_file() else {}
    outputs = solutions.get(item['public_task_id'])
    if (digest(outputs) if outputs is not None else None) != item['test_outputs_sha256']:
        raise ValueError('Official test gold identity changed')
    if item['task_id'] != tid or generator_id(item['public_task_id']) != tid or item['source_path'] != SOURCE:
        raise ValueError('Public parent identity differs from task home')
    parent = json.loads(regular(root / SOURCE).read_text())[item['public_task_id']]
    if digest(parent) != item['source_record_sha256'] or digest(_challenge(parent)) != item['challenge_sha256']:
        raise ValueError('Official source identity changed')
    parent = copy.deepcopy(parent)
    if outputs is not None:
        if len(outputs) != len(parent.get('test', [])):
            raise ValueError('Official test gold count mismatch')
        for pair, output in zip(parent['test'], outputs):
            if 'output' in pair and pair['output'] != output:
                raise ValueError('Conflicting official test gold')
            pair['output'] = output
    base = home / 'workspace/parametric'
    regular(base / 'promotion.json')
    native = authoring_contract(root, tid)
    if native.get('adapter') != f'generators/{tid}/workspace/parametric/adapter.py':
        raise ValueError('Adapter path must be in assigned home')
    settings = settings_space(native)
    bounds = native.get('limits', {}).get('demos', [])
    if type(bounds) is not list or len(bounds) != 2 or any(type(n) is not int for n in bounds) or not 2 <= bounds[0] <= bounds[1] <= 6:
        raise ValueError('Declare supported demonstrations within 2..6')
    qbounds = native.get('limits', {}).get('queries', [])
    if type(qbounds) is not list or len(qbounds) != 2 or any(type(n) is not int for n in qbounds) or not 1 <= qbounds[0] <= 4 <= qbounds[1] <= 32:
        raise ValueError('Four queries are required')
    regular(home/'generator.py'); regular(base/'adapter.py')
    validate_reference_id(home/'generator.py', item['public_task_id'])
    program = regular(home / 'reference.rkt').read_text()
    source_paths = [p for p in home.rglob('*') if p.is_file() and (p.suffix in {'.py', '.rkt'} or p.name in {'promotion.json', 'public-parent.json'}) and '__pycache__' not in p.parts]
    source_paths.append(regular(root/'shared/tools/comment_solutions.py'))
    source_paths += [p for p in (root/'shared/runtime').rglob('*') if p.is_file() and p.suffix in {'.py', '.rkt'} and '__pycache__' not in p.parts]
    for source in source_paths:
        regular(source)
    binding = {'task_id': tid, 'files': [{'path': p.relative_to(root).as_posix(), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(source_paths)]}
    with _local_imports(root / 'shared/runtime', base):
        spec = importlib.util.spec_from_file_location('_public_creation_adapter', base/'adapter.py')
        adapter = importlib.util.module_from_spec(spec); sys.modules[spec.name] = adapter; spec.loader.exec_module(adapter)
        programs = {json.dumps(s, sort_keys=True, separators=(',', ':'), ensure_ascii=False): adapter.program(copy.deepcopy(s)) for s in settings}
        key = lambda s: json.dumps(s, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        if programs[key(native['default'])] != program:
            raise ValueError('Default program must exactly equal new reference.rkt')
        from .review_programs import strict_programs
        program_syntax = strict_programs(root, [program, *programs.values()])
        apply, identity, bridge = _real_evaluator(root/'shared/runtime')
        pairs = []; checks = []; episodes = []; jobs = []; matched_streams = {}
        try:
            with _local_imports(root / 'shared/runtime', home):
                generator_spec = importlib.util.spec_from_file_location('_public_creation_base', home/'generator.py')
                generator = importlib.util.module_from_spec(generator_spec)
                sys.modules[generator_spec.name] = generator
                generator_spec.loader.exec_module(generator)
                base_generation = _base_generation(generator, apply, program)
            for split in ('train', 'test'):
                for index, pair in enumerate(parent.get(split, [])):
                    if 'output' not in pair:
                        continue
                    # Source datasets may encode rows as digit strings.
                    grid = lambda g: [[int(c) for c in row] for row in g]
                    actual = _grid(apply(program, grid(pair['input'])))
                    if actual != grid(pair['output']):
                        raise ValueError(f'Official {split}[{index}] does not match reference')
                    pairs.append({'split': split, 'index': index, 'input': grid(pair['input']), 'output': actual})
            if not pairs:
                raise ValueError('No original labelled pairs')
            for setting in settings:
                for seed in (17, 43):
                    demos = bounds[0]
                    lesson = adapter.generate(seed, copy.deepcopy(setting), demos, 4)
                    if lesson.get('program_solution') != programs[key(setting)]:
                        raise ValueError('Generated rule differs from setting')
                    if len(lesson['train']) != demos or len(lesson['test']) != 4:
                        raise ValueError('Sampler count mismatch')
                    for split in ('train', 'test'):
                        lesson[split] = [{'input': _grid(p['input']), 'output': _grid(p['output'])} for p in lesson[split]]
                    inputs = [p['input'] for sp in ('train', 'test') for p in lesson[sp]]
                    if seed in matched_streams and inputs != matched_streams[seed]:
                        raise ValueError('Parameter settings must preserve matched input streams for a fixed seed')
                    matched_streams[seed] = inputs
                    if len({digest(g) for g in inputs}) != len(inputs):
                        raise ValueError('All demo/query inputs must be distinct')
                    survivors = []
                    for rival in settings:
                        if all(_grid(apply(programs[key(rival)], _grid(p['input']))) == _grid(p['output']) for p in lesson['train']):
                            survivors.append(rival)
                    if survivors != [setting]:
                        raise ValueError('Demonstrations fail finite rival identification')
                    for p in lesson['test']:
                        if _grid(apply(programs[key(setting)], _grid(p['input']))) != _grid(p['output']):
                            raise ValueError('Generated query label mismatch')
                    jobs.append({'settings': setting, 'seed': seed, 'demos': demos, 'queries': 4})
                    checks.append({'settings': setting, 'seed': seed, 'survivors': survivors, 'queries': 4})
                    episodes.append({'reference': 'unapproved_authoring_preflight', 'settings': setting, 'seed': seed, **lesson})
        finally:
            bridge.close()
    for row in binding['files']:
        if hashlib.sha256((root/row['path']).read_bytes()).hexdigest() != row['sha256']:
            raise ValueError('Source changed during preflight')
    out.mkdir(parents=True, exist_ok=False)
    write = lambda p, v: p.write_text(json.dumps(v, sort_keys=True, indent=2, allow_nan=False)+'\n')
    original = {'status': 'passed', 'public_creation': item, 'racket': identity, 'pairs': pairs,
        'masked_queries': sum('output' not in p for p in parent.get('test', [])), 'masked_query_correctness': 'unverified_without_gold'}
    write(out/'original-pairs.json', original)
    write(out/'execution.json', {'checks': checks, 'episodes': episodes, 'base_generation': base_generation, 'program_syntax': program_syntax, 'racket': identity})
    receipt = {'schema': PREFLIGHT, 'task_id': tid, 'status': 'passed',
        'verification_status': 'authoring_preflight_not_owner_qualification', 'owner_accepted': False,
        'public_creation': item, 'source_binding': binding, 'contract': native, 'jobs': jobs,
        'programs': {k: hashlib.sha256(p.encode()).hexdigest() for k,p in programs.items()},
        'evidence_sha256': {n: hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ('execution.json', 'original-pairs.json')},
        'limits': 'Finite declared-rival sampler checks. Causal and additional adversarial/export checks required separately; no approval or training admission.'}
    write(out/'preflight.json', receipt)
    write(home/'workspace/public-eval-creation.json', {'schema': PUBLIC_WORK_SCHEMA, **item,
        'reference_program': 'reference.rkt', 'promotion_manifest': 'workspace/parametric/promotion.json'})
    # A reviewer inventory, explicitly unapproved; owner refreshes the native inventory after registration.
    (base/'evidence').mkdir(exist_ok=True)
    write(base/'evidence/manifest.json', {'schema': 'arcpuzzles-public-eval-authoring-inventory-v1', 'task_id': tid,
        'source_binding': binding, 'owner_registration_required': True})
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['preflight']); parser.add_argument('task_id')
    parser.add_argument('--root', type=Path, default=Path('.')); parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    result = preflight(args.root, args.task_id, args.out)
    print(json.dumps({'status': result['status'], 'verification_status': result['verification_status'], 'owner_accepted': False}))


if __name__ == '__main__':
    main()
