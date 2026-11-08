"""Optional reviewer causal-witness builder; uses existing native validation/replay."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile

from .catalog import Catalog
from . import parametric_promotion as native
from .review_parametric_admission import validate_sequential_witness
from .review_sequential_replay import replay_witness
from .runtime import run_process

FIELDS = ('step_a', 'intermediate', 'step_b', 'why_b_depends_on_a')
LIMITS = ('Finite protected label replay only. Intermediate values and causal interpretation '
          'are authored metadata, not independently proved. No owner acceptance or training admission.')


def _raw(value):
    return (json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False) + '\n').encode()


def _sha_text(text):
    return hashlib.sha256(text.encode()).hexdigest()


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _fresh(path):
    path = Path(path)
    if path.exists() or path.is_symlink():
        raise FileExistsError(f'Choose a new output path: {path}')
    return path


def _write_new(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('xb') as handle:
        handle.write(_raw(value))


def _qualified(root, path):
    path = Path(path).resolve()
    q = json.loads(path.read_bytes())
    from .review_base_preflight import SCHEMA as AUTHORING_SCHEMA, source_ready, _records_hash
    authoring = q.get('schema') == AUTHORING_SCHEMA
    if authoring:
        if (q.get('status') != 'passed' or q.get('owner_accepted') is not False
                or q.get('verification_status') != 'authoring_preflight_not_owner_qualification'):
            raise ValueError('Invalid base authoring preflight receipt')
    elif q.get('schema') != native.QUALIFICATION or q.get('status') != 'qualified':
        from .review_public_creation import PREFLIGHT
        if q.get('schema') == PREFLIGHT:
            raise ValueError('Expected native qualified receipt or base authoring receipt with --qualification; '
                             'public-evaluation creation receipts require --public-preflight')
        raise ValueError('Expected native qualified receipt or base authoring receipt with --qualification')
    execution_path = path.with_name('execution.json')
    if q.get('execution') != {'path': 'execution.json', 'sha256': _sha(execution_path)}:
        raise ValueError('Qualification execution hash/path differs')
    execution = json.loads(execution_path.read_bytes())
    contract, binding = (source_ready(root, q['task_id']) if authoring
                         else native._ready(Catalog(root), q['task_id']))
    if q.get('source_binding') != binding or q.get('contract') != contract:
        raise ValueError('Qualification does not bind current source/contract')
    if native._check_execution(execution, q['jobs'], binding, contract) != q.get('programs'):
        raise ValueError('Qualification program map differs from execution')
    if authoring:
        base = execution.get('base_review', {})
        if (base.get('status') != 'passed' or not base.get('pairs')
                or base.get('canonical_records_sha256') != _records_hash(Catalog(root), q['task_id'])):
            raise ValueError('Base preflight original evidence differs from current reference records')
    return q, execution


def _public_preflight(root, path):
    """Read exact authoring evidence; never reinterpret it as native qualification."""
    import importlib.util
    from .review_public_creation import PREFLIGHT, authoring_contract, generator_id
    from .review_public_admission import _check_binding, _parent, _regular
    from .parametric_promotion import settings_space
    from .parametric_worker import _grid, _local_imports
    from .review_programs import strict_programs
    root = Path(root).resolve(); path = Path(path).absolute()
    def evidence(member):
        if not member.is_file() or any(p.is_symlink() for p in (member, *member.parents)):
            raise ValueError('Public preflight evidence must be regular files without symlinks')
        return member.read_bytes()
    q = json.loads(evidence(path))
    if q.get('schema') != PREFLIGHT:
        from .review_base_preflight import SCHEMA as AUTHORING_SCHEMA
        if q.get('schema') in {AUTHORING_SCHEMA, native.QUALIFICATION}:
            raise ValueError(f"Receipt schema {q['schema']} requires --qualification; "
                             '--public-preflight is only for public-evaluation creation receipts')
        raise ValueError('Expected public authoring preflight, not owner qualification')
    tid = q['task_id']; item = q['public_creation']
    if (q.get('schema') != PREFLIGHT or q.get('status') != 'passed'
            or q.get('verification_status') != 'authoring_preflight_not_owner_qualification'
            or q.get('owner_accepted') is not False or tid != generator_id(item['public_task_id'])
            or item['task_id'] != tid or q.get('source_binding', {}).get('task_id') != tid):
        raise ValueError('Expected public authoring preflight, not owner qualification')
    home = root/'generators'/tid
    target = json.loads(_regular(root, f'generators/{tid}/workspace/public-parent.json').read_bytes())
    if any(target.get(k) != v for k, v in item.items()):
        raise ValueError('Public preflight parent differs from current home')
    parent = _parent(root, item)
    _check_binding(root, q['source_binding'])
    required = {p.relative_to(root).as_posix() for p in home.rglob('*')
                if p.is_file() and (p.suffix in {'.py', '.rkt'} or p.name in {'promotion.json', 'public-parent.json'})
                and '__pycache__' not in p.parts}
    required.update(p.relative_to(root).as_posix() for p in (root/'shared/runtime').rglob('*')
                    if p.is_file() and p.suffix in {'.py', '.rkt'} and '__pycache__' not in p.parts)
    required.add('shared/tools/comment_solutions.py')
    if {row['path'] for row in q['source_binding']['files']} != required:
        raise ValueError('Public preflight source closure differs from current source')
    records = {}
    for name in ('execution.json', 'original-pairs.json'):
        raw = evidence(path.with_name(name))
        if hashlib.sha256(raw).hexdigest() != q['evidence_sha256'].get(name):
            raise ValueError('Public preflight evidence hash differs: ' + name)
        records[name] = json.loads(raw)
    original = records['original-pairs.json']
    grid = lambda value: _grid([[int(c) for c in row] for row in value])
    expected = [dict(split=split, index=i, input=grid(pair['input']), output=grid(pair['output']))
                for split in ('train', 'test') for i, pair in enumerate(parent.get(split, [])) if 'output' in pair]
    if (original.get('status') != 'passed' or original.get('public_creation') != item
            or _raw(original.get('pairs')) != _raw(expected)):
        raise ValueError('Public preflight must retain every original labelled pair')
    contract = authoring_contract(root, tid)
    if q.get('contract') != contract:
        raise ValueError('Public preflight contract differs from current source')
    settings = settings_space(contract); base = home/'workspace/parametric'
    expected_jobs = [dict(settings=setting, seed=seed, demos=contract['limits']['demos'][0], queries=4)
                     for setting in settings for seed in (17, 43)]
    if _raw(q.get('jobs')) != _raw(expected_jobs):
        raise ValueError('Public preflight jobs differ from the bounded authoring run')
    with _local_imports(root/'shared/runtime', base):
        spec = importlib.util.spec_from_file_location('_public_witness_adapter', base/'adapter.py')
        adapter = importlib.util.module_from_spec(spec); sys.modules[spec.name] = adapter; spec.loader.exec_module(adapter)
        key = lambda setting: json.dumps(setting, sort_keys=True, separators=(',', ':'), ensure_ascii=False)
        programs = {key(setting): adapter.program(deepcopy(setting)) for setting in settings}
    strict_programs(root, programs.values())
    if q.get('programs') != {k: hashlib.sha256(v.encode()).hexdigest() for k, v in programs.items()}:
        raise ValueError('Public preflight program map differs from current adapter')
    if programs[key(contract['default'])] != _regular(root, f'generators/{tid}/reference.rkt').read_text():
        raise ValueError('Public preflight default differs from reference')
    execution = records['execution.json']
    for record in (execution, original):
        if record.get('racket', {}).get('backend') != 'racket' or record.get('racket', {}).get('protected') is not True:
            raise ValueError('Public preflight requires protected Racket evidence')
    episodes = execution.get('episodes', [])
    if len(episodes) != len(q.get('jobs', [])) or not episodes:
        raise ValueError('Public preflight episodes differ from jobs')
    for episode, job in zip(episodes, q['jobs']):
        if (episode.get('settings') != job['settings'] or episode.get('seed') != job['seed']
                or len(episode['train']) != job['demos'] or len(episode['test']) != 4 or job['queries'] != 4
                or episode.get('program_solution') != programs.get(key(job['settings']))):
            raise ValueError('Public preflight episode program/count differs')
        for split in ('train', 'test'):
            for pair in episode[split]:
                _grid(pair['input']); _grid(pair['output'])
        episode['program'] = episode['program_solution']
    _check_binding(root, q['source_binding'])
    return q, execution


def _receipt(root, path, public_preflight=False):
    return _public_preflight(root, path) if public_preflight else _qualified(root, path)


def _descriptions(value):
    if not isinstance(value, dict) or any(not isinstance(value.get(k), str) or not value[k].strip() for k in FIELDS):
        raise ValueError('Fill all four named dependency descriptions')
    return {key: value[key] for key in FIELDS}


def _match_case(execution, case):
    """Locate an audited case without treating its causal claims as verified."""
    keys = ('settings', 'program', 'input', 'output')
    if not isinstance(case, dict) or any(key not in case for key in keys):
        raise ValueError('Matched case requires settings, program, input and output')
    expected = _raw({key: case[key] for key in keys})
    for index, episode in enumerate(execution['episodes']):
        for split in ('train', 'test'):
            for pair_index, pair in enumerate(episode[split]):
                actual = dict(settings=episode['settings'], program=episode['program'],
                              input=pair['input'], output=pair['output'])
                if _raw(actual) == expected:
                    return dict(episode_index=index, split=split, pair_index=pair_index)
    raise ValueError('Audited settings/program/input/output has no exact qualified pair')


def write_template(root, qualification, output, *, match_case=None, settings=None, counterfactual_settings=None, public_preflight=False):
    """Write a private draft selecting an audited pair, exact settings, or first nondefault job."""
    output = _fresh(output)
    q, execution = _receipt(root, qualification, public_preflight)
    index = next((i for i, e in enumerate(execution['episodes'])
                  if e['settings'] != q['contract']['default']), 0)
    if settings is not None:
        if match_case is not None:
            raise ValueError('Choose settings or match_case, not both')
        if not isinstance(settings, dict):
            raise ValueError('settings must be a JSON object selecting one complete qualified setting')
        index = next((i for i, e in enumerate(execution['episodes'])
                      if _raw(e['settings']) == _raw(settings)), None)
        if index is None:
            raise ValueError('No exact qualified settings match; supply every parameter with its declared JSON type')
    selection = (dict(episode_index=index, split='test', pair_index=0) if match_case is None
                 else _match_case(execution, match_case))
    case = dict(**selection, counterfactual_program='', intermediate_value=None,
                ablation='wrong_intermediate')
    if match_case is not None:
        for key in ('counterfactual_program', 'intermediate_value', 'ablation'):
            if key in match_case:
                case[key] = deepcopy(match_case[key])
    selected = execution['episodes'][selection['episode_index']]
    pair = selected[selection['split']][selection['pair_index']]
    alternatives, seen = [], set()
    for episode in execution['episodes']:
        key = _raw(episode['settings'])
        if key == _raw(selected['settings']) or key in seen:
            continue
        seen.add(key)
        alternatives.append(dict(settings=deepcopy(episode['settings']),
                                 program=episode['program'], program_sha256=_sha_text(episode['program']),
                                 counterfactual_checked=False))
    selected_counterfactual = None
    if counterfactual_settings is not None:
        if not isinstance(counterfactual_settings, dict):
            raise ValueError('counterfactual settings must be one complete qualified JSON object')
        selected_counterfactual = next((row for row in alternatives
                                       if _raw(row['settings']) == _raw(counterfactual_settings)), None)
        if selected_counterfactual is None:
            raise ValueError('Counterfactual settings must select a distinct complete qualified setting')
        if case['counterfactual_program'] and case['counterfactual_program'] != selected_counterfactual['program']:
            raise ValueError('Matched case counterfactual differs from selected counterfactual settings')
        case['counterfactual_program'] = selected_counterfactual['program']
    recipe = {**{key: '' for key in FIELDS}, 'cases': [case],
              'selected_case': dict(settings=deepcopy(selected['settings']),
                                    program=selected['program'], program_sha256=_sha_text(selected['program']),
                                    input=deepcopy(pair['input']), output=deepcopy(pair['output'])),
              'receipt_alternatives': alternatives,
              'syntax_examples': {'identity': {
                  'program': '(rule! (lambda (g) g))',
                  'limits': 'Standalone identity syntax, not a causal claim or a preselected ablation. '
                            'Use only if it tests your dependency; build must still show different final output. '
                            'A bare (rule! g) leaves g unbound at top level.'}},
              'limits': 'Private authoring context. Alternatives are recorded in the source receipt on their own sampled inputs; '
                        'none is claimed to change this selected pair or prove causal dependency. '
                        'No new qualification or acceptance is claimed. Fill the recipe and use build for protected replay.'}
    if selected_counterfactual is not None:
        recipe['selected_counterfactual'] = deepcopy(selected_counterfactual)
    _write_new(output, recipe)
    return {'status': 'draft_only', 'recipe': str(output.resolve()),
            'task_id': q['task_id'], 'instructions': 'Fill descriptions, intermediate_value and standalone counterfactual_program; then build.'}


def _counterfactual(row, root):
    if 'counterfactual_program_path' not in row:
        return row.get('counterfactual_program')
    if row.get('counterfactual_program') not in (None, ''):
        raise ValueError('Choose counterfactual_program or counterfactual_program_path, not both')
    name = row['counterfactual_program_path']
    expected = row.get('counterfactual_program_sha256')
    if (not isinstance(expected, str) or len(expected) != 64
            or any(c not in '0123456789abcdef' for c in expected)):
        raise ValueError('counterfactual_program_path requires its exact counterfactual_program_sha256')
    if not isinstance(name, str) or not name or root is None:
        raise ValueError('counterfactual_program_path requires a nonempty library-relative path')
    relative = Path(name)
    if relative.is_absolute() or '..' in relative.parts:
        raise ValueError('counterfactual_program_path must stay inside the library')
    path = Path(root).resolve()
    for part in relative.parts:
        path = path / part
        if path.is_symlink():
            raise ValueError('counterfactual_program_path must not contain symlinks')
    if not path.is_file() or path.stat().st_size > 100000:
        raise ValueError('counterfactual_program_path must be a regular file of at most 100000 bytes')
    with path.open('rb') as handle:
        raw = handle.read(100001)
    if len(raw) > 100000 or hashlib.sha256(raw).hexdigest() != expected:
        raise ValueError('counterfactual program file differs from its expected SHA-256 or size limit')
    try:
        return raw.decode('utf-8')
    except UnicodeError as exc:
        raise ValueError('counterfactual program file must be UTF-8') from exc


def _cases(recipe, execution, *, root=None):
    rows = recipe.get('cases')
    if not isinstance(rows, list) or not 1 <= len(rows) <= 16:
        raise ValueError('Recipe requires 1..16 cases')
    cases = []
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError('Each case must be an object')
        index, pair_index = row.get('episode_index'), row.get('pair_index')
        if type(index) is not int or not 0 <= index < len(execution['episodes']):
            raise ValueError('episode_index must select a qualified episode')
        episode = execution['episodes'][index]
        split = row.get('split')
        if split not in ('train', 'test') or type(pair_index) is not int or not 0 <= pair_index < len(episode[split]):
            raise ValueError('split/pair_index must select a qualified pair')
        program = _counterfactual(row, root)
        if not isinstance(program, str) or not program.strip() or len(program.encode()) > 100000:
            raise ValueError('counterfactual_program must be nonempty bounded Racket text')
        if row.get('ablation') not in {'skip_a', 'wrong_intermediate', 'wrong_order'}:
            raise ValueError('ablation must be skip_a, wrong_intermediate or wrong_order')
        if row.get('intermediate_value') is None:
            raise ValueError('Supply the authored intermediate_value')
        pair = episode[split][pair_index]
        cases.append(dict(input=pair['input'], output=pair['output'], settings=episode['settings'],
                          program=episode['program'], counterfactual_program=program,
                          counterfactual_program_sha256=_sha_text(program),
                          intermediate_value=row['intermediate_value'], ablation=row['ablation'],
                          qualified_case=dict(episode_index=index, split=split, pair_index=pair_index)))
    return deepcopy(cases)


def _validate_programs(cases):
    from arc_repl import parser
    from .review_programs import validate_forms
    validate_forms([case.get(key) for case in cases
                    for key in ('program', 'counterfactual_program')], parser)


def _evaluate(request):
    """Internal subprocess: compute both labels in the protected reference runtime."""
    from .parametric_worker import _grid, _local_imports, _real_evaluator
    runtime = Path(request['root']) / 'shared/runtime'
    with _local_imports(runtime, runtime):
        _validate_programs(request['cases'])
        apply, identity, bridge = _real_evaluator(runtime)
        try:
            cases = request['cases']
            for case in cases:
                grid = _grid(case['input'])
                actual = _grid(apply(case['program'], grid))
                if actual != _grid(case['output']):
                    raise ValueError('Qualified label differs from fresh protected execution')
                alternate = _grid(apply(case['counterfactual_program'], grid))
                if alternate == actual:
                    raise ValueError('Counterfactual does not change final output')
                case['counterfactual_output'] = alternate
            return {'cases': cases, 'racket': identity, 'evaluations': 2 * len(cases)}
        finally:
            bridge.close()


def _execute(root, cases, timeout):
    if type(timeout) not in (float, int) or not math.isfinite(timeout) or not 0 < timeout <= 60:
        raise ValueError('Timeout must be finite in (0, 60] seconds per execution/replay phase')
    with tempfile.TemporaryDirectory(prefix='arcpuzzles-witness-') as directory:
        request = Path(directory) / 'request.json'
        request.write_bytes(_raw({'root': str(Path(root).resolve()), 'cases': cases}))
        result = run_process([sys.executable, '-m', 'arcpuzzles.review_witness', '_execute', str(request)],
                             Path(root), timeout=timeout,
                             extra_env={'PYTHONPATH': str(Path(__file__).resolve().parents[1]),
                                        'PYTHONNOUSERSITE': '1', 'PYTHONDONTWRITEBYTECODE': '1'})
    if result['timed_out'] or result['exit_code'] != 0:
        raise ValueError('Protected witness construction failed: ' + json.dumps({
            'timed_out': result['timed_out'], 'exit_code': result['exit_code'],
            'stdout': result['stdout'][-1800:], 'stderr': result['stderr'][-1800:]}))
    return json.loads(result['stdout'])


def _check(root, qualification, q, witness, timeout, public_preflight=False):
    from .parametric_worker import _local_imports
    descriptions = _descriptions(witness)
    payload = _raw(witness)
    validate_sequential_witness({'sequential_dependency': {**descriptions, 'witness_path': 'witness.json'}},
                                q, lambda _: payload)
    runtime = Path(root) / 'shared/runtime'
    with _local_imports(runtime, runtime):
        _validate_programs(witness['cases'])
    replay = replay_witness(root, witness, timeout=timeout)
    if _receipt(root, qualification, public_preflight)[0] != q:
        raise ValueError('Qualified source or receipt changed during witness replay')
    return {'schema': 'arcpuzzles-reviewer-witness-check-v1', 'status': 'reviewer_replayed',
            'task_id': q['task_id'], 'source_binding': q['source_binding'],
            ('public_preflight_sha256' if public_preflight else 'qualification_sha256'): _sha(qualification),
            'verification_status': ('authoring_preflight_not_owner_qualification' if public_preflight else 'reviewer_native_qualification_replay'),
            'witness_sha256': hashlib.sha256(payload).hexdigest(),
            'replay': {**replay, 'status': 'reviewer_replayed'},
            'training_admitted': False, 'owner_acceptance': 'not_performed', 'limits': LIMITS}


def build_witness(root, qualification, recipe, output, *, timeout=30, public_preflight=False):
    output = _fresh(output)
    q, execution = _receipt(root, qualification, public_preflight)
    descriptions = _descriptions(recipe)
    constructed = _execute(root, _cases(recipe, execution, root=root), timeout)
    witness = {'schema': 'arcpuzzles-sequential-dependency-witness-v1',
               'source_binding': q['source_binding'], **descriptions,
               'racket': {'backend': 'racket', 'protected': True},
               'cases': constructed['cases'], 'limits': LIMITS}
    result = _check(root, qualification, q, witness, timeout, public_preflight)
    result['construction'] = {'racket': constructed['racket'], 'evaluations': constructed['evaluations']}
    output.mkdir(parents=True, exist_ok=False)
    _write_new(output / 'witness.json', witness)
    result['witness_path'] = str((output / 'witness.json').resolve())
    _write_new(output / 'replay.json', result)
    return result


def check_witness(root, qualification, witness_path, output, *, timeout=30, public_preflight=False):
    output = _fresh(output)
    q, _ = _receipt(root, qualification, public_preflight)
    witness_path = Path(witness_path)
    before = witness_path.read_bytes()
    result = _check(root, qualification, q, json.loads(before), timeout, public_preflight)
    if witness_path.read_bytes() != before:
        raise ValueError('Witness changed during replay')
    result.update(witness_path=str(witness_path.resolve()), witness_sha256=hashlib.sha256(before).hexdigest())
    _write_new(output, result)
    return result


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv and argv[0] == '_execute':
        try:
            print(json.dumps(_evaluate(json.loads(Path(argv[1]).read_bytes())), allow_nan=False))
            return 0
        except Exception as exc:
            print(json.dumps({'error': type(exc).__name__, 'message': str(exc)}))
            return 1
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--library', type=Path, default=Path.cwd())
    actions = parser.add_subparsers(dest='action', required=True)
    for name in ('template', 'build', 'check'):
        command = actions.add_parser(name)
        source = command.add_mutually_exclusive_group(required=True)
        source.add_argument('--qualification', type=Path, help='Native qualification or review_base_preflight receipt (including unapproved bases)')
        source.add_argument('--public-preflight', type=Path, help='Only public-evaluation creation preflight receipts; not review_base_preflight')
        if name == 'build':
            command.add_argument('--out', '--out-dir', dest='out', type=Path, required=True,
                                 metavar='DIR', help='new directory for witness.json and replay.json')
        else:
            kind = 'recipe' if name == 'template' else 'replay'
            command.add_argument('--out', type=Path, required=True, metavar='FILE',
                                 help=f'new {kind} JSON file')
        if name == 'template':
            command.add_argument('--counterfactual-settings', type=json.loads,
                                 help='Distinct complete qualified setting for the draft alternate program; build still must prove disagreement')
            selector = command.add_mutually_exclusive_group()
            selector.add_argument('--settings', type=json.loads, help='Exact complete setting as a JSON object; selects its first qualified query')
            selector.add_argument('--match-case', type=Path,
                                 help='audited JSON case with exact settings/program/input/output; still a draft')
        if name != 'template': command.add_argument('--timeout', type=float, default=30)
        if name == 'build': command.add_argument('--recipe', type=Path, required=True)
        if name == 'check': command.add_argument('--witness', type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        public = args.public_preflight is not None
        receipt = args.public_preflight if public else args.qualification
        if args.action == 'template':
            result = write_template(args.library, receipt, args.out, public_preflight=public,
                                    match_case=json.loads(args.match_case.read_bytes()) if args.match_case else None,
                                    settings=args.settings, counterfactual_settings=args.counterfactual_settings)
        elif args.action == 'build':
            result = build_witness(args.library, receipt, json.loads(args.recipe.read_bytes()), args.out, timeout=args.timeout, public_preflight=public)
        else:
            result = check_witness(args.library, receipt, args.witness, args.out, timeout=args.timeout, public_preflight=public)
        print(json.dumps({key: result[key] for key in ('status', 'task_id', 'recipe', 'witness_path', 'training_admitted', 'limits') if key in result}, indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f'review_witness: {exc}', file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
