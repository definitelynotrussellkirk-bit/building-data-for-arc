"""Proposed task-local chevron parameters; reference labels come only from Racket."""
from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve()
for ancestor in HERE.parents:
    # In a copied runtime, its selected execution layout outranks library mirrors.
    candidates = ((ancestor, ancestor/'shared/runtime')
                  if (ancestor/'RUNTIME_MANIFEST.json').is_file()
                  else (ancestor/'shared/runtime', ancestor))
    local = next((p for p in candidates
                  if (p/'reviewer_support.py').is_file()), None)
    if local is not None:
        sys.path.insert(0, str(local))
        break
else:
    raise ImportError('No local reviewer_support in this source tree')

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import strip_line_comments, strip_rule_wrapper
from reviewer_support import canonical_pairs, canonical_path, find_root, load_selected_generator, normalize_grid

ROOT = find_root(HERE)
TASK_ID = '3977ec54e4a0'
CANONICAL_SHA256 = 'b4c2540796af088ba41f486413b1be85ff6f8a9db373d30e6105bdc4529c7f25'
PAINT_SITE = '           8 v)))))'
COLOR_COMMENT_SITE = ';; with cyan(8).'
EDGE_COMMENT_SITE = ';; cell within the solid triangle'
EDGE_SITES = (
    '(<= (abs (- c ac)) (- r ar))',
    '(<= (abs (- c ac)) (- ar r))',
    '(<= (abs (- r ar)) (- c ac))',
    '(<= (abs (- r ar)) (- ac c))',
)
COMPETITORS = (
    'omit_down', 'omit_up', 'omit_right', 'omit_left', 'cap_depth_two',
    'symmetric_only', 'first_component_only', 'complete_arms_only',
)


@dataclass(frozen=True)
class Setting:
    fill_color: int = 8
    fill_edges: bool = True

    def __post_init__(self):
        if type(self.fill_color) is not int or self.fill_color not in (2, 4, 6, 8):
            raise ValueError('fill_color must be an integer in (2,4,6,8)')
        if type(self.fill_edges) is not bool:
            raise ValueError('fill_edges must be a boolean')

    @property
    def key(self):
        return f'color-{self.fill_color}-edges-{str(self.fill_edges).lower()}'


DEFAULT = Setting()
SETTINGS = tuple(Setting(c, e) for c in (2, 4, 6, 8) for e in (False, True))


def digest(value):
    if not isinstance(value, bytes):
        value = value.encode() if isinstance(value, str) else json.dumps(
            value, sort_keys=True, separators=(',', ':')).encode()
    return hashlib.sha256(value).hexdigest()


def selected_generator():
    """Hash and load the current selected source using the public helper."""
    return load_selected_generator(TASK_ID, root=ROOT)


@lru_cache(maxsize=1)
def canonical_rule():
    sources = set()
    with canonical_path(ROOT).open(encoding='utf-8') as handle:
        for line in handle:
            if TASK_ID in line:
                row = json.loads(line)
                if row.get('task_id') == TASK_ID:
                    sources.add(row['program_solution'])
    if len(sources) != 1:
        raise ValueError('canonical authority is missing or ambiguous')
    source = sources.pop()
    if digest(source) != CANONICAL_SHA256:
        raise ValueError('canonical source changed; re-review the prototype')
    return source


def materialize_rule(setting=DEFAULT, *, source=None):
    if not isinstance(setting, Setting):
        raise ValueError('expected a validated Setting')
    source = canonical_rule() if source is None else source
    if not isinstance(source, str) or digest(source) != CANONICAL_SHA256:
        raise ValueError('canonical source changed; guarded replacement refused')
    for site in (PAINT_SITE, COLOR_COMMENT_SITE, EDGE_COMMENT_SITE, *EDGE_SITES):
        if source.count(site) != 1:
            raise ValueError('canonical replacement site is not unique')
    if setting == DEFAULT:
        return source
    if setting.fill_color != 8:
        source = source.replace(PAINT_SITE, f'           {setting.fill_color} v)))))')
        source = source.replace(COLOR_COMMENT_SITE, f';; with color {setting.fill_color}.')
    if not setting.fill_edges:
        for site in EDGE_SITES:
            source = source.replace(site, site.replace('(<= ', '(< ', 1))
        source = source.replace(EDGE_COMMENT_SITE,
                                ';; strict diagonal interior; axial depth inclusive')
    return source


def execute_rule(bridge, program, grid):
    """Execute this pinned syntax through the shared reference bridge.

    The canonical form already uses full Racket bindings (no shorthand/dicts).
    Shared exported helpers remove comments and rule!; lexical h/w reproduce
    the documented grid-lambda convention without importing private scripts.
    """
    grid = normalize_grid(grid)
    literal = '(' + ' '.join('('+' '.join(map(str, row))+')' for row in grid) + ')'
    body = strip_rule_wrapper(strip_line_comments(program))
    expression = f"(let* ((g '{literal}) (h (rows g)) (w (cols g))) ({body} g))"
    return normalize_grid(bridge.eval_text(expression))


def _coordinates(orientation, apex, r, c):
    dr, dc = r-apex[0], c-apex[1]
    return ((dr, dc), (-dr, dc), (dc, dr), (-dc, dr))[orientation]


def _inside(orientation, apex, depth, r, c, fill_edges):
    axial, transverse = _coordinates(orientation, apex, r, c)
    return 0 <= axial <= depth and (
        abs(transverse) <= axial if fill_edges else abs(transverse) < axial)


def _attested_triangles(grid):
    """Independent relation/projection implementation of canonical detection."""
    remaining = {(r,c) for r,row in enumerate(grid) for c,v in enumerate(row) if v == 3}
    groups = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        pending, group = [start], {start}
        while pending:
            ar, ac = pending.pop()
            neighbors = set()
            for r, c in remaining:
                dr, dc = abs(r-ar), abs(c-ac)
                if max(dr,dc) <= 2 and (dr == dc or dr == 0 or dc == 0):
                    neighbors.add((r,c))
            remaining -= neighbors
            group |= neighbors
            pending.extend(sorted(neighbors))
        groups.append(group)
    result = set()
    for group in groups:
        for apex in group:
            for orientation in range(4):
                projected = [_coordinates(orientation,apex,r,c) for r,c in group]
                left = {a for a,t in projected if a > 0 and t == -a}
                right = {a for a,t in projected if a > 0 and t == a}
                for depth in left | right:
                    if any(a <= depth for a in left) and any(a <= depth for a in right):
                        result.add((orientation,apex,depth))
    return sorted(result)


def predict(grid, setting=DEFAULT):
    """Independent diagnostic prediction; never used as an example label."""
    if not isinstance(setting, Setting):
        raise ValueError('expected a validated Setting')
    grid = normalize_grid(grid)
    triangles = _attested_triangles(grid)
    return [[setting.fill_color if v != 3 and any(
        _inside(o,a,d,r,c,setting.fill_edges) for o,a,d in triangles)
        else v for c,v in enumerate(row)] for r,row in enumerate(grid)]


def choose_setting(seed):
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    index = int(digest(f'{TASK_ID}:parametric-v1:{seed}')[:16], 16) % len(SETTINGS)
    return SETTINGS[index]


class EpisodeBuildError(ValueError):
    def __init__(self, message, evidence):
        super().__init__(message)
        self.evidence = deepcopy(evidence)


def _rival_prediction(grid, setting, name, generator):
    """Preserve each selected competitor's object selection; vary paint only."""
    chevrons, errors = generator._decode_grid(grid)
    if errors:
        raise ValueError('; '.join(errors))
    active = []
    for index, chevron in enumerate(sorted(chevrons)):
        if name in COMPETITORS[:4] and chevron.orientation == COMPETITORS.index(name):
            continue
        if name == 'symmetric_only' and chevron.asymmetric:
            continue
        if name == 'first_component_only' and index != 0:
            continue
        if name == 'complete_arms_only' and not (all(chevron.left_mask) and all(chevron.right_mask)):
            continue
        depth = min(2, chevron.depth) if name == 'cap_depth_two' else chevron.depth
        active.append((chevron.orientation, chevron.apex, depth))
    return [[setting.fill_color if v != 3 and any(
        _inside(o,a,d,r,c,setting.fill_edges) for o,a,d in active)
        else v for c,v in enumerate(row)] for r,row in enumerate(grid)]


def _label_candidate(grid, setting, programs, bridge, generator):
    predictions = {s.key: execute_rule(bridge, programs[s.key], grid) for s in SETTINGS}
    for s in SETTINGS:
        if predict(grid, s) != predictions[s.key]:
            raise ValueError(f'independent diagnostic disagrees with Racket: {s.key}')
    rivals = {}
    for name in COMPETITORS:
        working = deepcopy(grid)
        declared = normalize_grid(generator.LESSON_COMPETITORS[name](working))
        if working != grid:
            raise ValueError(f'selected lesson competitor mutates its input: {name}')
        if declared != _rival_prediction(grid, DEFAULT, name, generator):
            raise ValueError(f'canonical lesson competitor adaptation mismatch: {name}')
        rivals[name] = _rival_prediction(grid, setting, name, generator)
    return {
        'input': deepcopy(grid),
        'output': deepcopy(predictions[setting.key]),
        'parameter_predictions': predictions,
        'lesson_competitor_predictions': rivals,
    }


def _predictions(pair):
    return {**{'parameter:'+name: value for name,value in pair['parameter_predictions'].items()},
            **{'lesson:'+name: value for name,value in pair['lesson_competitor_predictions'].items()}}


def _survivors(demonstrations):
    if not demonstrations:
        raise ValueError('demonstration evidence is empty')
    names = _predictions(demonstrations[0])
    return [name for name in names if all(
        _predictions(pair)[name] == pair['output'] for pair in demonstrations)]


def _score_rivals(demonstrations, queries, setting):
    rows = []
    for name in _predictions(demonstrations[0]):
        refutations = [i for i,pair in enumerate(demonstrations)
                       if _predictions(pair)[name] != pair['output']]
        differences = [i for i,pair in enumerate(queries)
                       if _predictions(pair)[name] != pair['output']]
        rows.append({
            'name': name,
            'chosen_program': name == 'parameter:'+setting.key,
            'execution': 'Racket' if name.startswith('parameter:') else 'checked selected Python competitor adaptation',
            'status': ('refuted_by_demonstrations' if refutations else
                       'ambiguous' if differences else 'survived_all'),
            'refuting_demonstration_indices': refutations,
            'query_disagreement_indices': differences,
        })
    return rows


def build_episode(seed, train=3, test=4, setting=None, max_attempts=128, bridge=None):
    """Choose demonstrations before queries; return a finite-rival verified episode.

    A passing demo window refutes every declared nonchosen rival. Queries are
    drawn only afterwards. This stronger demo-only criterion may exhaust the
    bounded input stream; it never relaxes the gate or the requested counts.
    """
    if type(seed) is not int:
        raise ValueError('seed must be an integer')
    if type(train) is not int or not 3 <= train <= 32:
        raise ValueError('train must be an integer in 3..32')
    if type(test) is not int or not 1 <= test <= 32:
        raise ValueError('test must be an integer in 1..32')
    if type(max_attempts) is not int or not 1 <= max_attempts <= 4096:
        raise ValueError('max_attempts must be an integer in 1..4096')
    setting = choose_setting(seed) if setting is None else setting
    if not isinstance(setting, Setting):
        raise ValueError('expected a validated Setting')
    if bridge is None:
        with RacketBridge() as owned:
            return build_episode(seed, train, test, setting, max_attempts, owned)
    generator, source_path, source_hash = selected_generator()
    declared = generator.LESSON_COMPETITORS
    if not isinstance(declared, dict) or set(declared) != set(COMPETITORS) or not all(callable(v) for v in declared.values()):
        raise ValueError('selected lesson competitor inventory changed; re-review adaptations')
    programs = {s.key: materialize_rule(s) for s in SETTINGS}
    sampling = {'attempts': 0, 'max_attempts': max_attempts, 'requested_start': 0,
                'next_index': 0, 'rejections': [], 'demo_windows': [], 'accepted_pairs': []}
    draws, seen, demonstrations, queries = [], set(), None, []
    for sample_index in range(max_attempts):
        sampling['attempts'] += 1
        sampling['next_index'] = sample_index+1
        try:
            grid = normalize_grid(generator.generate(seed, sample_index, difficulty='medium'))
            errors = generator.self_check(grid)
            if errors:
                raise ValueError('; '.join(errors))
        except ValueError as exc:
            sampling['rejections'].append({'sample_index': sample_index, 'reason': str(exc)})
            continue
        input_hash = digest(grid)
        if input_hash in seen:
            sampling['rejections'].append({'sample_index': sample_index, 'reason': 'duplicate input', 'input_sha256': input_hash})
            continue
        seen.add(input_hash)
        pair = _label_candidate(grid, setting, programs, bridge, generator)
        pair['sample_index'] = sample_index
        if demonstrations is None:
            draws.append(pair)
            if len(draws) < train:
                continue
            window = draws[-train:]
            survivors = _survivors(window)
            passed = survivors == ['parameter:'+setting.key]
            sampling['demo_windows'].append({
                'sample_indices': [p['sample_index'] for p in window],
                'surviving_rivals': survivors, 'passed': passed,
            })
            if passed:
                demonstrations = window
        else:
            queries.append(pair)
            if len(queries) == test:
                break
    if demonstrations is None or len(queries) != test:
        raise EpisodeBuildError('finite-rival episode construction exhausted its sampling bound', {
            'status': 'FAIL', 'parameters': asdict(setting), 'seed': seed,
            'reason': 'demonstrations not identified' if demonstrations is None else 'query count not reached',
            'requested_train': train, 'requested_test': test,
            'actual_train': 0 if demonstrations is None else len(demonstrations),
            'actual_test': len(queries), 'generator_sha256': source_hash, 'sampling': sampling,
        })
    if digest(source_path.read_bytes()) != source_hash:
        raise ValueError('selected generator changed while building the episode')
    rivals = _score_rivals(demonstrations, queries, setting)
    if any(row['status'] == 'ambiguous' for row in rivals):
        raise EpisodeBuildError('query ambiguity after final assembly', {
            'status': 'FAIL', 'sampling': sampling, 'finite_rivals': rivals})
    for split, pairs in (('train',demonstrations), ('test',queries)):
        for position, pair in enumerate(pairs):
            sampling['accepted_pairs'].append({
                'split': split, 'pair_index': position,
                'sample_index': pair['sample_index'],
                'input_sha256': digest(pair['input']), 'output_sha256': digest(pair['output']),
            })
    query_checks = [{
        'query_index': i, 'identified': True,
        'surviving_rivals': _survivors(demonstrations),
        'disagreeing_survivors': [row['name'] for row in rivals
            if not row['refuting_demonstration_indices'] and i in row['query_disagreement_indices']],
    } for i in range(test)]
    private = {
        'schema': 'chevron-parametric-private-v1', 'task_id': TASK_ID,
        'seed': seed, 'difficulty': 'medium', 'parameters': asdict(setting),
        'program': programs[setting.key], 'program_sha256': digest(programs[setting.key]),
        'pairs': deepcopy(demonstrations+queries), 'train_count': train, 'test_count': test,
    }
    report = {
        'schema': 'chevron-parametric-episode-report-v1', 'status': 'PASS',
        'prototype_status': 'proposed; not canonical approval',
        'generator_source': str(source_path.relative_to(ROOT)), 'generator_sha256': source_hash,
        'canonical_program_sha256': CANONICAL_SHA256,
        'program_sha256': private['program_sha256'],
        'sampling': sampling, 'finite_rivals': rivals, 'query_checks': query_checks,
        'diagnostic_mirror_agrees_all_settings': True,
        'selected_competitor_parity_checked': list(COMPETITORS),
        'demo_selection_used_query_answers': False,
        'limits': 'Ordered demonstrations; finite declared rivals only. No arbitrary-query-rotation or universal-identifiability claim.',
    }
    public = {
        'train': [{'input':deepcopy(p['input']), 'output':deepcopy(p['output'])} for p in demonstrations],
        'test': [{'input':deepcopy(p['input'])} for p in queries],
    }
    return {'public':public, 'private':private, 'report':report}


def diagnostic_probe(bridge):
    """A deliberately designed hidden-edge ambiguity, separate from production."""
    generator, _, source_hash = selected_generator()
    grids = []
    for orientation in range(4):
        grid = [[(r+c) % 2 for c in range(12)] for r in range(12)]
        points = [(0,0), (1,-1), (2,-2), (3,-3), (1,1), (2,2), (3,3)]
        if orientation == 3:
            points.remove((2,-2))
        for dr,dc in points:
            dr,dc = ((dr,dc),(-dr,dc),(dc,dr),(dc,-dr))[orientation]
            grid[5+dr][5+dc] = 3
        if generator.self_check(grid):
            raise ValueError('diagnostic witness is outside the selected grammar')
        grids.append(grid)
    programs = [materialize_rule(Setting(8,edges)) for edges in (True,False)]
    labels = [[execute_rule(bridge,program,grid) for grid in grids] for program in programs]
    matches = [a == b for a,b in zip(*labels)]
    differences = [{'row':r, 'column':c, 'inclusive':labels[0][3][r][c],
                    'strict':labels[1][3][r][c]}
                   for r in range(12) for c in range(12) if labels[0][3][r][c] != labels[1][3][r][c]]
    return {
        'kind':'diagnostic_probe', 'origin':'deliberately designed; not a natural solve failure',
        'status':'ambiguous' if all(matches[:3]) and not matches[3] else 'unexpected',
        'generator_sha256':source_hash, 'borrowed_query_answers':False,
        'demonstration_matches':matches[:3], 'query_matches':matches[3:],
        'parameters':[asdict(Setting(8,edges)) for edges in (True,False)],
        'program_sha256':[digest(p) for p in programs],
        'public':{'train':[{'input':g,'output':y} for g,y in zip(grids[:3],labels[0][:3])],
                  'test':[{'input':grids[3]}]},
        'private_labels':{'inclusive':labels[0], 'strict':labels[1]},
        'query_differences':differences,
        'interpretation':'Correct labels alone do not establish query identifiability; score final assembled episodes from demonstrations against parameter rivals.',
    }


def _write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, indent=2)+'\n', encoding='utf-8')


def _source_manifest():
    _, generator_path, _ = selected_generator()
    files = [HERE, generator_path, HERE.parents[1]/'../tests/test_parametric_chevrons.py',
             HERE.with_name('README.md'), HERE.with_name('DESIGN.md')]
    files = [path.resolve() for path in files if path.is_file()]
    runtime = Path(sys.modules['reviewer_support'].__file__).resolve().parent
    files.extend(runtime/name for name in ('reviewer_support.py', 'puzzle_generators/rule_wrap.py',
                                         'arc_repl/racket_bridge.py',
                                         'arc_repl/racket_prelude/arc-prelude.rkt',
                                         'arc_repl/racket_prelude/bank-helpers.rkt',
                                         'arc_repl/racket_prelude/heightmap.rkt',
                                         'arc_repl/racket_prelude/layers.rkt')
                 if (runtime/name).is_file())
    return [{'path':str(path.relative_to(ROOT)), 'sha256':digest(path.read_bytes())}
            for path in files]


def _canonical_checks(bridge):
    program = materialize_rule(DEFAULT)
    rows = []
    for pair in canonical_pairs(TASK_ID, root=ROOT, labeled_only=True):
        output = execute_rule(bridge, program, pair['input'])
        if output != pair['output']:
            raise ValueError('default Racket output differs from a canonical label')
        rows.append({'variant':pair['variant'], 'split':pair['split'], 'pair_index':pair['pair_index'],
                     'input_sha256':digest(pair['input']), 'output_sha256':digest(output), 'equal':True})
    return {'status':'PASS', 'exact_canonical_program_bytes':program == canonical_rule(),
            'canonical_program_sha256':CANONICAL_SHA256, 'labeled_pairs_checked':len(rows),
            'unique_inputs':len({row['input_sha256'] for row in rows}), 'pairs':rows}


def public_filename(challenge):
    """Name only visible examples, never settings, seeds or query answers."""
    demos = challenge.get("train", challenge.get("demos"))
    queries = challenge.get("test", challenge.get("query"))
    if isinstance(queries, dict): queries = [queries]
    visible = {"train": [{"input": p["input"], "output": p["output"]} for p in demos],
               "test": [{"input": p["input"]} for p in queries]}
    digest = hashlib.sha256(json.dumps(visible, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    return "challenge-" + digest + ".json"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=271828)
    parser.add_argument('--train', type=int, default=3, help='demonstrations, 3..32')
    parser.add_argument('--test', type=int, default=4, help='distinct queries, 1..32')
    parser.add_argument('--fill-color', type=int, choices=(2,4,6,8))
    parser.add_argument('--fill-edges', choices=('true','false'))
    parser.add_argument('--all-settings', action='store_true', help='eight episodes, seeds seed..seed+7')
    parser.add_argument('--max-attempts', type=int, default=128)
    parser.add_argument('--out', type=Path, required=True, help='new artifact directory')
    args = parser.parse_args(argv)
    if not 3 <= args.train <= 32 or not 1 <= args.test <= 32 or not 1 <= args.max_attempts <= 4096:
        parser.error('train is 3..32, test is 1..32, and max-attempts is 1..4096')
    if args.all_settings and (args.fill_color is not None or args.fill_edges is not None):
        parser.error('--all-settings cannot be combined with parameter overrides')
    out = args.out.resolve()
    if out.exists():
        parser.error('output destination already exists; choose a new path')
    if args.all_settings:
        chosen = list(enumerate(SETTINGS))
    else:
        base = choose_setting(args.seed)
        setting = Setting(base.fill_color if args.fill_color is None else args.fill_color,
                          base.fill_edges if args.fill_edges is None else args.fill_edges == 'true')
        chosen = [(0,setting)]
    # Validate arguments before creating any artifacts or starting the reference runtime.
    out.mkdir(parents=True)
    manifest = _source_manifest()
    try:
        with RacketBridge() as bridge:
            episodes = [build_episode(args.seed+i, args.train, args.test, setting,
                                      args.max_attempts, bridge) for i,setting in chosen]
            canonical = _canonical_checks(bridge)
            probe = diagnostic_probe(bridge)
            if probe['status'] != 'ambiguous':
                raise ValueError('designed ambiguity witness stopped distinguishing the parameter rules')
            runtime = {'binary':str(bridge.racket_binary), 'version':bridge.eval_text('(version)'),
                       'label_authority':'included RacketBridge; diagnostic Python is not a label source'}
        for row in manifest:
            if digest((ROOT/row['path']).read_bytes()) != row['sha256']:
                raise ValueError(f'source changed during evidence generation: {row["path"]}')
        records = []
        for index, episode in enumerate(episodes, 1):
            name = public_filename(episode['public'])
            _write_json(out/'public'/name, episode['public'])
            _write_json(out/'private'/name, {**episode['private'], 'report':episode['report']})
            records.append({'public_path':'public/'+name, 'private_path':'private/'+name,
                            'public_sha256':digest((out/'public'/name).read_bytes()),
                            'private_sha256':digest((out/'private'/name).read_bytes()),
                            'seed':episode['private']['seed'], 'parameters':episode['private']['parameters'],
                            'program_sha256':episode['private']['program_sha256'],
                            'sampling':episode['report']['sampling'],
                            'status':episode['report']['status']})
        program_rows = []
        for setting in SETTINGS:
            program = materialize_rule(setting)
            path = out/'private/programs'/f'{setting.key}.rkt'
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(program.encode())
            program_rows.append({'parameters':asdict(setting), 'path':str(path.relative_to(out)),
                                 'sha256':digest(program)})
        for row in manifest:
            path = ROOT/row['path']
            if path == HERE or '/generators/'+TASK_ID+'/' in '/'+row['path']:
                target = out/'private/source_snapshot'/row['path']
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(path.read_bytes())
        _write_json(out/'private/diagnostic-probe.json', probe)
        _write_json(out/'private/canonical-parity.json', canonical)
        report = {
            'schema':'chevron-parametric-evidence-v1', 'status':'PASS',
            'classification':'proposed task-local prototype; no production approval',
            'task_id':TASK_ID, 'base_seed':args.seed, 'train_count':args.train, 'test_count':args.test,
            'episode_count':len(episodes), 'source_manifest':manifest,
            'canonical_program_sha256':CANONICAL_SHA256, 'programs':program_rows,
            'episodes':records, 'canonical_parity':'private/canonical-parity.json',
            'designed_ambiguity_probe':'private/diagnostic-probe.json', 'runtime':runtime,
            'payload_command':[sys.executable,str(HERE),*(sys.argv[1:] if argv is None else argv)],
            'effective_cwd':str(Path.cwd()),
            'parameter_choice':'fixed once per episode; hash of seed unless explicitly overridden; all-settings enumerates seeds seed+i',
            'demo_gate':'all seven nonchosen Racket parameters and eight checked lesson competitor adaptations refuted before queries are drawn',
            'limits':['Finite declared rivals only; not universal identifiability.',
                      'Ordered demonstrations only; arbitrary query rotations are not certified.',
                      'Bounded deterministic nonuniform input rejection; no general success guarantee for other seeds.',
                      'Parameter alternatives execute in Racket; branch competitors remain checked Python diagnostics.',
                      'Only public/ contains model-visible challenge files. Everything in private/ is authoring evidence.'],
        }
        _write_json(out/'private/report.json', report)
        print(json.dumps({'status':'PASS', 'episodes':len(episodes),
                          'demonstrations':len(episodes)*args.train, 'queries':len(episodes)*args.test,
                          'programs':len(SETTINGS), 'canonical_labels_checked':canonical['labeled_pairs_checked'],
                          'out':str(out)}, sort_keys=True))
        return 0
    except Exception as exc:
        failure = {'status':'FAIL', 'error_type':type(exc).__name__, 'error':str(exc),
                   'source_manifest':manifest}
        if isinstance(exc, EpisodeBuildError):
            failure['episode_failure'] = exc.evidence
        _write_json(out/'private/failure.json', failure)
        print(json.dumps({'status':'FAIL','error':str(exc),'out':str(out)}, sort_keys=True), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
