"""Proposed, unapproved bounded shear prototype; Racket supplies every label."""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile

TASK_ID = 'ad4e576b99c4'
SETTINGS = (2, 3, 4)
RULE_PIN = '6de9bdaa4c45'
CANONICAL_PROGRAM_SHA256 = '61fb42dce4c08b6efbe1a7711718153f16848699effa351b2006c0ebbb7f5e21'
MAX_RETRIES_PER_INPUT = 64


def _integer(value, name, lo, hi=None):
    if type(value) is not int or value < lo or (hi is not None and value > hi):
        bound = f'{lo}..{hi}' if hi is not None else f'>={lo}'
        raise ValueError(f'{name} must be an exact integer {bound}; got {value!r}')
    return value


def validate_parameter(value):
    _integer(value, 'shear_start_rows', 2, 4)
    return value


def _request(seed, shear_start_rows, n_demo, n_query, input_seed, timeout_ms):
    _integer(seed, 'seed', 0)
    validate_parameter(shear_start_rows)
    _integer(n_demo, 'n_demo', 1, 8)
    _integer(n_query, 'n_query', 1, 32)
    if input_seed is not None:
        _integer(input_seed, 'input_seed', 0)
    _integer(timeout_ms, 'timeout_ms', 1, 60000)


def _helpers():
    # Bootstrap only the nearest normal repository runtime, never cwd or an
    # environment-selected alternate source. Actual selection remains bound to
    # reviewer_support.find_root(__file__). Staging imports need no repository.
    for ancestor in Path(__file__).resolve().parents:
        runtime = ancestor / 'shared/runtime'
        if (runtime / 'reviewer_support.py').is_file():
            if str(runtime) not in sys.path:
                sys.path.insert(0, str(runtime))
            break
    import reviewer_support
    return reviewer_support


def _context():
    support = _helpers()
    root = support.find_root(__file__)
    generator, source, digest = support.load_selected_generator(TASK_ID, root=root)
    if generator.RULE_HASH != RULE_PIN:
        raise ValueError('selected generator canonical rule pin changed')
    with support.canonical_path(root).open(encoding='utf-8') as handle:
        matches = [row for line in handle if line.strip()
                   for row in [json.loads(line)] if row.get('task_id') == TASK_ID]
    if len(matches) != 1:
        raise ValueError('expected one canonical parent record')
    program = matches[0]['program_solution']
    if _sha(program.encode()) != CANONICAL_PROGRAM_SHA256:
        raise ValueError('canonical parent program changed; narrow variants require review')
    return dict(root=root, generator=generator, source=source,
                generator_sha256=digest, canonical_program=program)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def _variant(program, setting):
    validate_parameter(setting)
    old_final = '(- r1 r0 2)'
    old_row = '(- r r0 2)'
    if program.count(old_final) != 2 or program.count(old_row) != 1:
        raise ValueError('canonical substitution anchors are not unique as expected')
    if setting == 3:
        return program
    return program.replace(old_final, f'(- r1 r0 {setting-1})').replace(
        old_row, f'(- r r0 {setting-1})')


def program_for(shear_start_rows):
    validate_parameter(shear_start_rows)
    return _variant(_context()['canonical_program'], shear_start_rows)


def _check_grid(grid, *, shape=None):
    if (type(grid) is not list or not grid or type(grid[0]) is not list
            or not grid[0] or len(grid) > 30 or len(grid[0]) > 30):
        raise ValueError('Racket returned an invalid grid')
    width = len(grid[0])
    if any(type(row) is not list or len(row) != width or
           any(type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError('grid cells must be exact integer ARC colors')
    if shape is not None and (len(grid), width) != shape:
        raise ValueError('Racket output shape changed')


def _run_on_bridge(bridge, grids, program):
    from puzzle_generators.rule_wrap import wrap_rule
    bridge.eval_text(f'(define __parametric_rule {wrap_rule(program)})')
    outputs = []
    for grid in grids:
        _check_grid(grid)
        bridge.define_grid('__parametric_input', grid)
        output = bridge.eval_text('(__parametric_rule __parametric_input)')
        _check_grid(output, shape=(len(grid), len(grid[0])))
        outputs.append(output)
    return outputs


def racket_outputs(grids, program, timeout_ms=4000):
    """Execute real protected Racket; failures propagate without a Python fallback.

    This packet exposes RacketBridge (the persistent session implementation),
    rather than a class named RacketSession.
    """
    _integer(timeout_ms, 'timeout_ms', 1, 60000)
    c = _context()
    from arc_repl.racket_bridge import RacketBridge
    prelude = c['root'] / 'shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt'
    with RacketBridge(prelude_path=str(prelude), timeout=timeout_ms / 1000) as bridge:
        return _run_on_bridge(bridge, grids, program)


def _sample_inputs(c, seed, n_demo, n_query):
    gen = c['generator']
    grids, seen = [], set()
    for slot in range(n_demo + n_query):
        is_demo = slot < n_demo
        role_index = slot if is_demo else slot - n_demo
        side = ('left', 'right')[role_index % 2]
        height = (7, 9)[role_index % 2] if is_demo else (4, 10, 6, 8)[role_index % 4]
        profile = 1 if slot == 0 else slot % 3
        for attempt in range(MAX_RETRIES_PER_INPUT):
            index = 3 * (slot * MAX_RETRIES_PER_INPUT + attempt) + profile
            grid = gen.generate(seed, index, side=side, patch_height=height)
            issues = gen.self_check(grid)
            if issues:
                raise ValueError(f'production sampler rejected its input: {issues}')
            observed = gen.observe_overrides(grid)
            if observed['side'] != side or observed['patch_height'] != height:
                continue
            if slot == 0 and not gen._noncanonical_mask(grid):
                continue
            key = json.dumps(grid, separators=(',', ':'))
            if key in seen:
                continue
            seen.add(key)
            grids.append(grid)
            break
        else:
            raise RuntimeError(f'input retry budget exhausted at slot {slot}: '
                               f'{MAX_RETRIES_PER_INPUT} attempts; side={side}, height={height}')
    return grids


def _rival(grid, setting, *, comb=False, same_side=False, border_delta=0, no_shear=False):
    """Supplementary finite rivals, never the source of accepted labels."""
    fives = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 5]
    r0, c0 = min(r for r, _ in fives), min(c for _, c in fives)
    r1, c1 = max(r for r, _ in fives), max(c for _, c in fives)
    h, w = len(grid), len(grid[0])
    br = min(r for r, row in enumerate(grid) if 6 in row)
    ph, pw = r1-r0+1, c1-c0+1
    move_right = c0 == 0
    if same_side:
        move_right = not move_right
    final_shift = 0 if no_shear else max(0, ph-setting)
    foot = w-pw-final_shift if move_right else final_shift
    out = [[1 if r < br else 6 for _ in range(w)] for r in range(h)]
    for c in range(w):
        if ((move_right and c < foot+pw-1+border_delta) or
                (not move_right and c > foot-border_delta)):
            out[br][c] = 9
    for dr in range(ph):
        shift = 0 if no_shear else max(0, dr-(setting-1))
        start = w-pw-shift if move_right else shift
        for dc in range(pw):
            value = 5 if dr < 2 or dc % 2 == 0 else 1
            out[r0+dr][start+dc] = value if comb else grid[r0+dr][c0+dc]
    return out


def _predictions(grids, c, timeout_ms):
    from arc_repl.racket_bridge import RacketBridge
    prelude = c['root'] / 'shared/runtime/arc_repl/racket_prelude/arc-prelude.rkt'
    predictions = {}
    # Every legal setting is executed by Racket. Only declared wrong-rule
    # competitors use the supplementary Python renderer.
    with RacketBridge(prelude_path=str(prelude), timeout=timeout_ms / 1000) as bridge:
        for setting in SETTINGS:
            predictions[f'shear_start_rows={setting}'] = _run_on_bridge(
                bridge, grids, _variant(c['canonical_program'], setting))
    for setting in SETTINGS:
        for name, kwargs in [('fixed_public_comb', dict(comb=True)),
                             ('same_side', dict(same_side=True)),
                             ('border_off_by_one', dict(border_delta=1))]:
            predictions[f'{name}:{setting}'] = [_rival(g, setting, **kwargs) for g in grids]
    predictions['identity'] = deepcopy(grids)
    predictions['no_shear'] = [_rival(g, 3, no_shear=True) for g in grids]
    return predictions


def _certificate(demos, query_inputs, predictions):
    # No query output or hidden setting is accepted by this function. Fit is
    # determined solely by demonstrations; query inputs test surviving agreement.
    n = len(demos)
    survivors = sorted(name for name, outputs in predictions.items()
                       if outputs[:n] == [pair['output'] for pair in demos])
    if not survivors:
        raise ValueError('no finite candidate fits demonstrations')
    anchor = predictions[survivors[0]][n:]
    disagreements = [[name for name in survivors if predictions[name][n+i] != anchor[i]]
                     for i in range(len(query_inputs))]
    if any(disagreements):
        raise ValueError(f'demonstrations leave query-changing survivors: {disagreements}')
    return dict(scope='explicit finite candidate family only',
                fit_uses='demonstration input/output pairs only',
                query_check_uses='query inputs and surviving candidate predictions only',
                candidates=sorted(predictions), survivors=survivors,
                eliminated=sorted(set(predictions)-set(survivors)),
                per_query_disagreements=disagreements)


def certify(demos, query_inputs, timeout_ms=4000):
    _integer(timeout_ms, 'timeout_ms', 1, 60000)
    _integer(len(demos), 'n_demo', 1, 8)
    _integer(len(query_inputs), 'n_query', 1, 32)
    for pair in demos:
        if type(pair) is not dict or 'input' not in pair or 'output' not in pair:
            raise ValueError('certificate demonstrations require input and output grids')
        _check_grid(pair['input'])
        _check_grid(pair['output'], shape=(len(pair['input']), len(pair['input'][0])))
    c = _context()
    grids = [pair['input'] for pair in demos] + list(query_inputs)
    for grid in grids:
        _check_grid(grid)
        issues = c['generator'].self_check(grid)
        if issues:
            raise ValueError(f'unlawful certificate input: {issues}')
    predictions = _predictions(grids, c, timeout_ms)
    return _certificate(demos, query_inputs, predictions)


def make_episode(seed, *, shear_start_rows=3, n_demo=2, n_query=4,
                 input_seed=None, timeout_ms=4000):
    _request(seed, shear_start_rows, n_demo, n_query, input_seed, timeout_ms)
    effective_input_seed = seed if input_seed is None else input_seed
    c = _context()
    grids = _sample_inputs(c, effective_input_seed, n_demo, n_query)
    predictions = _predictions(grids, c, timeout_ms)
    labels = predictions[f'shear_start_rows={shear_start_rows}']
    pairs = [dict(input=grid, output=output) for grid, output in zip(grids, labels)]
    train, test = pairs[:n_demo], pairs[n_demo:]
    certificate = _certificate(train, grids[n_demo:], predictions)
    program = _variant(c['canonical_program'], shear_start_rows)
    support = _helpers()
    episode = dict(schema_version=1, status='proposed/unapproved', training_admitted=False,
        task_id=TASK_ID, seed=seed, input_seed=effective_input_seed,
        parameters=dict(shear_start_rows=shear_start_rows), n_demo=n_demo, n_query=n_query,
        timeout_ms=timeout_ms, train=train, test=test, program=program,
        program_sha256=_sha(program.encode()),
        programs={str(s): dict(text=_variant(c['canonical_program'], s),
            sha256=_sha(_variant(c['canonical_program'], s).encode())) for s in SETTINGS},
        canonical_parent=dict(task_id=TASK_ID, original_arc_training_id='9f41bd9c',
            review_id='review-e622a7eb1a6fbedc', canonical_rule_pin=RULE_PIN,
            canonical_program_sha256=CANONICAL_PROGRAM_SHA256),
        generator_source=str(c['source'].relative_to(c['root'])),
        generator_sha256=c['generator_sha256'], prototype_sha256=_sha(Path(__file__).read_bytes()),
        certificate=certificate,
        sampler=dict(max_retries_per_input=MAX_RETRIES_PER_INPUT,
                     input_policy='production domain; lawful inputs independent of setting'))
    episode['public_id'] = support.public_challenge_id(episode)
    return episode


def _verify_episode(episode):
    if type(episode) is not dict:
        raise ValueError('episode must be a generated episode dictionary')
    try:
        parameters = episode['parameters']
        if type(parameters) is not dict or set(parameters) != {'shear_start_rows'}:
            raise ValueError('invalid parameter mapping')
        args = dict(shear_start_rows=parameters['shear_start_rows'], n_demo=episode['n_demo'],
                    n_query=episode['n_query'], input_seed=episode['input_seed'],
                    timeout_ms=episode['timeout_ms'])
        # Regeneration verifies lawful deterministic inputs, exact counts,
        # actual-Racket labels, complete demo-only certificate, and provenance.
        # A caller's verified flag/certificate/hash can never authorize output.
        fresh = make_episode(episode['seed'], **args)
        if _json_bytes(episode) != _json_bytes(fresh):
            raise ValueError('episode tampered or stale: regeneration mismatch')
        return fresh
    except (KeyError, TypeError) as error:
        raise ValueError('incomplete episode') from error


def _json_bytes(value):
    return (json.dumps(value, sort_keys=True, indent=2) + '\n').encode()


def write_batch(episodes, output_dir):
    """Reverify complete episodes, then atomically expose a new public/private batch."""
    destination = Path(output_dir)
    if destination.exists() or destination.is_symlink():
        raise ValueError('output directory must be new')
    items = list(episodes)
    if not items:
        raise ValueError('batch must contain episodes')
    support = _helpers()
    plan = [(support.public_challenge_id(e), support.public_challenge_bytes(e), e) for e in items]
    if len({key for key, _, _ in plan}) != len(plan):
        raise ValueError('duplicate visible public payload')
    verified = []
    for key, payload, episode in sorted(plan, key=lambda row: row[0]):
        fresh = _verify_episode(episode)
        if fresh['public_id'] != key or support.public_challenge_bytes(fresh) != payload:
            raise ValueError('public projection changed during verification')
        verified.append((key, payload, fresh))
    destination.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f'.{destination.name}.staging-', dir=destination.parent))
    try:
        (stage/'public').mkdir()
        (stage/'private/episodes').mkdir(parents=True)
        ids, setting_map = [], {}
        for key, payload, fresh in verified:
            (stage/'public'/f'{key}.json').write_bytes(payload)
            (stage/'private/episodes'/f'{key}.json').write_bytes(_json_bytes(fresh))
            ids.append(key)
            setting_map[key] = fresh['parameters']['shear_start_rows']
        (stage/'private/manifest.json').write_bytes(_json_bytes(dict(
            status='proposed/unapproved', training_admitted=False,
            public_ids=ids, setting_map=setting_map, task_id=TASK_ID,
            prototype_sha256=_sha(Path(__file__).read_bytes()))))
        if destination.exists() or destination.is_symlink():
            raise ValueError('output directory must be new')
        os.rename(stage, destination)
    except BaseException:
        shutil.rmtree(stage, ignore_errors=True)
        raise
    return ids


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', required=True, type=int)
    parser.add_argument('--settings', nargs='+', type=int, choices=SETTINGS, default=list(SETTINGS))
    parser.add_argument('--demos', type=int, default=2)
    parser.add_argument('--queries', type=int, default=4)
    parser.add_argument('--out', required=True, type=Path)
    args = parser.parse_args(argv)
    if len(args.settings) != len(set(args.settings)):
        parser.error('--settings must be distinct')
    episodes = [make_episode(args.seed, shear_start_rows=s, n_demo=args.demos,
                             n_query=args.queries, input_seed=args.seed) for s in args.settings]
    ids = write_batch(episodes, args.out)
    print(json.dumps(dict(output_dir=str(args.out), public_ids=ids, training_admitted=False), sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
