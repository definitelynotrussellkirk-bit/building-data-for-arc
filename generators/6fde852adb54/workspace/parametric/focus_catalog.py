#!/usr/bin/env python3
"""Proposed d8e07eb2-inspired catalog rule; not a canonical generator variant.

All exported labels are executed by the protected Racket bridge. Python is only
an independent sampler/checker. See README.md for the observed public anomaly
and the explicit complete-line assumption.
"""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
from pathlib import Path
import random
import sys

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
RUNTIME = REPO / 'shared/runtime'
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))
from reviewer_support import public_challenge_bytes, public_challenge_id
from arc_repl.racket_bridge import RacketBridge

ALIGNMENTS = ('row_or_column', 'row_only', 'column_only')
MODELS = ALIGNMENTS + ('shape_only', 'color_only', 'header_positions', 'any_complete_count')
DEFAULT = 'row_or_column'
FOCUS_SHA256 = '6dece13d6599eea896cbb0ebece1f8098a602b601f2030026d3674cc08b4155c'
COLORS = (0, 1, 2, 4, 5, 6, 7, 9)
DIMENSIONS = ((3, 3), (3, 4), (3, 5), (4, 4), (4, 5))
SCENARIOS = ('row', 'column', 'mixed', 'partial')


class SamplingExhausted(ValueError):
    pass


class InsufficientDemonstrations(ValueError):
    pass


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=False)


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def grid_digest(grid):
    return sha256(compact(grid).encode())


def exact_int(name, value, lower, upper):
    if type(value) is not int or not lower <= value <= upper:
        raise ValueError(f'{name} must be an exact integer in {lower}..{upper}')
    return value


def validate_model(model):
    if type(model) is not str or model not in MODELS:
        raise ValueError('unknown rule model')


def parse_grid(grid):
    if (type(grid) is not list or not grid or type(grid[0]) is not list
            or not grid[0] or len(grid) > 30 or len(grid[0]) > 30):
        raise ValueError('grid must be a nonempty list within ARC dimensions')
    h, w = len(grid), len(grid[0])
    if any(type(row) is not list or len(row) != w or any(
        type(v) is not int or not 0 <= v <= 9 for v in row) for row in grid):
        raise ValueError('grid must be rectangular with exact integer colors 0..9')
    bars = [r for r, row in enumerate(grid) if all(v == 6 for v in row)]
    if bars != [5, h - 3] or (h - 10) % 5 or (w - 2) % 5:
        raise ValueError('expected two separator bars and 5-cell catalog tiles')
    nr, nc = (h - 10) // 5, (w - 2) // 5
    if (nr, nc) not in DIMENSIONS:
        raise ValueError('unsupported catalog dimensions')
    allowed = {(r, c) for r in bars for c in range(w)}

    def glyph(r, c):
        points = [(r+dr, c+dc) for dr in range(3) for dc in range(3)]
        allowed.update(points)
        key = tuple(grid[y][x] for y, x in points)
        ink = set(key) - {8}
        if 3 in ink or len(ink) > 1:
            raise ValueError('glyphs must be monochrome, excluding reserved highlight 3')
        return key

    tiles = [(r, c, glyph(8 + 5*r, 2 + 5*c)) for r in range(nr) for c in range(nc)]
    if any(all(v == 8 for v in key) for _, _, key in tiles):
        raise ValueError('catalog tiles must contain glyphs')
    if len({key for _, _, key in tiles}) != nr * nc:
        raise ValueError('exact colored catalog glyphs must be unique')
    headers = [(c, glyph(1, 2 + 5*c)) for c in range(nc)]
    headers = [(slot, key) for slot, key in headers if any(v != 8 for v in key)]
    keys = {key for _, _, key in tiles}
    if not headers or len({key for _, key in headers}) != len(headers):
        raise ValueError('header must contain distinct nonempty glyphs')
    if any(key not in keys for _, key in headers):
        raise ValueError('every header glyph must exactly match a catalog item')
    if any(grid[r][c] != 8 for r in range(h) for c in range(w) if (r,c) not in allowed):
        raise ValueError('padding and input footer must be background 8')
    return {'rows': nr, 'cols': nc, 'bars': bars, 'headers': headers, 'tiles': tiles}


def shape(key):
    return tuple(v != 8 for v in key)


def ink(key):
    return next(v for v in key if v != 8)


def lookup_positions(info, model=DEFAULT):
    validate_model(model)
    positions = []
    for slot, header in info['headers']:
        if model == 'header_positions':
            positions.append((0, slot))
            continue
        project = shape if model == 'shape_only' else ink if model == 'color_only' else lambda x: x
        r, c, _ = next(tile for tile in info['tiles'] if project(tile[2]) == project(header))
        positions.append((r, c))
    return positions


def python_apply(grid, model=DEFAULT):
    info = parse_grid(grid)
    positions = set(lookup_positions(info, model))
    row_ok = len(positions) == info['cols'] and len({r for r,c in positions}) == 1
    col_ok = len(positions) == info['rows'] and len({c for r,c in positions}) == 1
    success = row_ok if model == 'row_only' else col_ok if model == 'column_only' else row_ok or col_ok
    if model == 'any_complete_count':
        success = len(positions) in (info['rows'], info['cols'])
    result = copy.deepcopy(grid)
    for r, c in positions:
        for y in range(7+5*r, 12+5*r):
            for x in range(1+5*c, 6+5*c):
                if grid[y][x] == 8:
                    result[y][x] = 3
    if success:
        for y in range(info['bars'][0]):
            for x in range(len(grid[0])):
                if grid[y][x] == 8:
                    result[y][x] = 3
    for y in range(info['bars'][1]+1, len(grid)):
        result[y] = [3 if success else 2] * len(grid[0])
    return result


RACKET_BODY = r'''(lambda (g)
  (define h (rows g))
  (define w (cols g))
  (define bars (filter (lambda (r) (andmap (lambda (v) (= v 6)) (list-ref g r))) (range 0 h)))
  (define top (first bars))
  (define bottom (second bars))
  (define nr (quotient (- bottom top 2) 5))
  (define nc (quotient (- w 2) 5))
  (define (glyph y x)
    (for*/list ([dy (in-range 3)] [dx (in-range 3)]) (cell-at g (+ y dy) (+ x dx))))
  (define (mask key) (map (lambda (v) (not (= v 8))) key))
  (define (ink key) (first (filter (lambda (v) (not (= v 8))) key)))
  (define tiles (for*/list ([r (in-range nr)] [c (in-range nc)])
    (list r c (glyph (+ top 3 (* 5 r)) (+ 2 (* 5 c))))))
  (define headers (filter (lambda (item) (ormap (lambda (v) (not (= v 8))) (second item)))
    (for/list ([slot (in-range nc)]) (list slot (glyph (- top 4) (+ 2 (* 5 slot)))))))
  (define positions (remove-duplicates
    (for/list ([header (in-list headers)])
      $LOOKUP$) equal?))
  (define row-ok (and (= (length positions) nc)
    (= (length (remove-duplicates (map first positions))) 1)))
  (define col-ok (and (= (length positions) nr)
    (= (length (remove-duplicates (map second positions))) 1)))
  (define success $SUCCESS$)
  (for/list ([r (in-range h)])
    (for/list ([c (in-range w)])
      (define v (cell-at g r c))
      (cond
        [(> r bottom) (if success 3 2)]
        [(and success (< r top) (= v 8)) 3]
        [(and (= v 8) (>= r (+ top 2)) (< r bottom) (>= c 1) (< c (- w 1))
              (member (list (quotient (- r top 2) 5) (quotient (- c 1) 5)) positions)) 3]
        [else v]))))'''


def materialize_program(model=DEFAULT):
    validate_model(model)
    if model == 'header_positions':
        lookup = '(list 0 (first header))'
    else:
        predicate = '(equal? (third tile) (second header))'
        if model == 'shape_only':
            predicate = '(equal? (mask (third tile)) (mask (second header)))'
        if model == 'color_only':
            predicate = '(= (ink (third tile)) (ink (second header)))'
        lookup = '(let ([found (first (filter (lambda (tile) ' + predicate + ') tiles))]) (list (first found) (second found)))'
    success = {'row_only': 'row-ok', 'column_only': 'col-ok',
               'any_complete_count': '(or (= (length positions) nr) (= (length positions) nc))'}.get(model, '(or row-ok col-ok)')
    body = RACKET_BODY.replace('$LOOKUP$', lookup).replace('$SUCCESS$', success)
    return '(rule!\n' + body + '\n)\n'


class RacketOracle:
    def __init__(self):
        self.bridge = RacketBridge(timeout=15.0)
        self.cache = {}
        self.records = []
        self.evaluations = 0

    def apply(self, model, grid):
        validate_model(model)
        parse_grid(grid)
        key = (model, grid_digest(grid))
        if key not in self.cache:
            program = materialize_program(model)
            body = program.strip()[len('(rule!'):-1].strip()
            literal = '(' + ' '.join('(' + ' '.join(map(str, row)) + ')' for row in grid) + ')'
            output = self.bridge.eval_text('(' + body + " '" + literal + ')')
            expected = python_apply(grid, model)
            if output != expected:
                raise AssertionError('Python/Racket disagreement: ' + model + ' input=' + key[1])
            self.cache[key] = output
            self.evaluations += 1
            self.records.append({'model': model, 'input_sha256': key[1],
                'output_sha256': grid_digest(output), 'program_sha256': sha256(program.encode())})
        return copy.deepcopy(self.cache[key])

    @property
    def runtime_identity(self):
        return self.bridge.runtime_identity

    def close(self):
        self.bridge.close()


def _connected_masks():
    result = []
    for mask in range(1, 512):
        points = {(i//3, i%3) for i in range(9) if mask & (1 << i)}
        if not 3 <= len(points) <= 7 or len({r for r,c in points}) != 3 or len({c for r,c in points}) != 3:
            continue
        reached = {next(iter(points))}
        frontier = list(reached)
        while frontier:
            r,c = frontier.pop()
            for point in [(r-1,c),(r+1,c),(r,c-1),(r,c+1)]:
                if point in points and point not in reached:
                    reached.add(point)
                    frontier.append(point)
        if reached == points:
            result.append(mask)
    return tuple(result)


MASKS = _connected_masks()


def sample_scene(rng, scenario):
    if scenario not in SCENARIOS:
        raise ValueError('unknown sampling scenario')
    nr, nc = rng.choice(DIMENSIONS)
    all_positions = [(r,c) for r in range(nr) for c in range(nc)]
    if scenario == 'row':
        row = rng.randrange(nr)
        positions = [(row,c) for c in range(nc)]
    elif scenario == 'column':
        col = rng.randrange(nc)
        positions = [(r,col) for r in range(nr)]
    elif scenario == 'partial':
        row = rng.randrange(nr)
        columns = rng.sample(range(nc), nc-1)
        positions = [(row,c) for c in columns]
    else:
        # Start with a full row, move exactly one member to another row and
        # different column; at least two axes remain, with complete-count size.
        row = rng.randrange(nr)
        moved_col = rng.randrange(nc)
        other_row = rng.choice([r for r in range(nr) if r != row])
        other_col = rng.choice([c for c in range(nc) if c != moved_col])
        positions = [(row,c) for c in range(nc) if c != moved_col] + [(other_row,other_col)]
    target = max(positions, key=lambda p:p[0]*nc+p[1])
    target_index = target[0]*nc + target[1]
    if target_index < 2:
        # Only possible for a partial first row: swap its final selected slot
        # to column 2, preserving its partial-line status.
        positions[-1] = (positions[-1][0], 2)
        target = max(positions, key=lambda p:p[0]*nc+p[1])
        target_index = target[0]*nc + target[1]
    shadow_a, shadow_b = rng.sample(all_positions[:target_index], 2)
    mask_a, mask_b = rng.sample(MASKS, 2)
    color_a, color_b = rng.sample(COLORS, 2)
    fixed = {target:(mask_a,color_b), shadow_a:(mask_a,color_a), shadow_b:(mask_b,color_b)}
    available = [(mask,color) for mask in MASKS for color in COLORS if (mask,color) not in fixed.values()]
    chosen = iter(rng.sample(available, nr*nc-3))
    catalog = {p: fixed[p] if p in fixed else next(chosen) for p in all_positions}
    h, w = 10+5*nr, 2+5*nc
    grid = [[8]*w for _ in range(h)]
    grid[5] = [6]*w
    grid[h-3] = [6]*w

    def draw(y,x,item):
        mask,color = item
        for i in range(9):
            if mask & (1 << i):
                grid[y+i//3][x+i%3] = color

    for (r,c),item in catalog.items():
        draw(8+5*r,2+5*c,item)
    rng.shuffle(positions)
    slots = rng.sample(range(nc), len(positions))
    for slot,point in zip(slots,positions):
        draw(1,2+5*slot,catalog[point])
    info = parse_grid(grid)
    return grid, {'scenario': scenario, 'catalog_shape': [nr,nc],
                  'header_coordinates': [list(p) for p in lookup_positions(info)]}


def certify(episode, oracle):
    """Infer finite models from demonstrations ONLY; query answers are ignored."""
    eliminated = {}
    survivors = []
    for model in MODELS:
        mismatches = [i for i,pair in enumerate(episode['train'])
                      if oracle.apply(model, pair['input']) != pair['output']]
        if mismatches:
            eliminated[model] = {'demonstration_indices': mismatches}
        else:
            survivors.append(model)
    queries = []
    for index, pair in enumerate(episode['test']):
        predictions = {model: grid_digest(oracle.apply(model, pair['input'])) for model in MODELS}
        surviving_predictions = {predictions[m] for m in survivors}
        queries.append({'index': index, 'input_sha256': grid_digest(pair['input']),
                        'model_prediction_sha256': predictions,
                        'prediction_agreement': len(surviving_predictions) == 1})
    return {'scope': 'seven explicitly materialized models; not universal uniqueness',
            'uses_query_answers': False, 'surviving_models': survivors,
            'eliminated_models': eliminated, 'queries': queries}


def generate_episode(*, seed=17, alignment_mode=DEFAULT, n_train=3, n_test=4,
                     max_attempts=128, oracle=None):
    exact_int('seed', seed, 0, 2**64-1)
    exact_int('n_train', n_train, 1, 16)
    exact_int('n_test', n_test, 1, 16)
    exact_int('max_attempts', max_attempts, 1, 4096)
    if type(alignment_mode) is not str or alignment_mode not in ALIGNMENTS:
        raise ValueError('alignment_mode must be one of ' + repr(ALIGNMENTS))
    if alignment_mode == DEFAULT and n_train < 3:
        raise InsufficientDemonstrations('row_or_column needs 3 demonstrations for this teaching schedule and finite count rival')
    rng = random.Random(seed)
    schedule = [SCENARIOS[i % 4] for i in range(n_train)]
    if n_train == 1:
        schedule[0] = 'column' if alignment_mode == 'row_only' else 'row'
    schedule += [SCENARIOS[i % 4] for i in range(n_test)]
    retained, seen, attempts, rejected = [], set(), 0, {'duplicate_input':0}
    while len(retained) < len(schedule) and attempts < max_attempts:
        scenario = schedule[len(retained)]
        attempts += 1
        grid, info = sample_scene(rng, scenario)
        digest = grid_digest(grid)
        if digest in seen:
            rejected['duplicate_input'] += 1
            continue
        seen.add(digest)
        retained.append((grid,info))
    if len(retained) != len(schedule):
        raise SamplingExhausted(f'exhausted {max_attempts} attempts; retained {len(retained)}/{len(schedule)} distinct inputs')
    owned = oracle is None
    if owned:
        oracle = RacketOracle()
    try:
        pairs = [{'input':grid, 'output':oracle.apply(alignment_mode,grid)} for grid,info in retained]
        episode = {'train':pairs[:n_train], 'test':pairs[n_train:], 'seed':seed,
                   'params':{'alignment_mode':alignment_mode},
                   'status':'proposed_public_evaluation_inspired_extension',
                   'sampling':{'attempts':attempts, 'max_attempts':max_attempts,
                               'rejected':rejected, 'scenes':[info for grid,info in retained]}}
        cert = certify(episode, oracle)
        if cert['surviving_models'] != [alignment_mode]:
            raise InsufficientDemonstrations('bounded teaching schedule left models: ' + repr(cert['surviving_models']))
        episode['certificate'] = cert
        return episode
    finally:
        if owned:
            oracle.close()


def analyze_public(oracle):
    source = HERE / 'focus_challenge.json'
    body = source.read_bytes()
    if sha256(body) != FOCUS_SHA256:
        raise ValueError('public focus source hash mismatch')
    data = json.loads(body)
    train = []
    for index,pair in enumerate(data['train']):
        grid, actual = pair['input'], pair['output']
        predicted = oracle.apply(DEFAULT, grid)
        info = parse_grid(grid)
        table = {key:[r,c] for r,c,key in info['tiles']}
        output_coords = []
        for slot in range(info['cols']):
            key = tuple(8 if actual[1+dr][2+5*slot+dc] == 3 else actual[1+dr][2+5*slot+dc]
                        for dr in range(3) for dc in range(3))
            output_coords.append(table.get(key))
        input_coords = []
        by_slot = {slot:key for slot,key in info['headers']}
        for slot in range(info['cols']):
            input_coords.append(table.get(by_slot.get(slot)))
        highlighted = [[r,c] for r in range(info['rows']) for c in range(info['cols'])
                       if actual[7+5*r][1+5*c] == 3]
        differences = [[r,c,predicted[r][c],actual[r][c]] for r in range(len(grid))
                       for c in range(len(grid[0])) if predicted[r][c] != actual[r][c]]
        train.append({'index':index, 'header_input_coordinates':input_coords,
                      'header_output_coordinates':output_coords, 'highlighted_catalog':highlighted,
                      'footer':sorted(set(actual[-1])), 'differences':differences,
                      'predicted_output':predicted, 'output_sha256':grid_digest(predicted)})
    tests = []
    for index,pair in enumerate(data['test']):
        predicted = oracle.apply(DEFAULT,pair['input'])
        tests.append({'index':index, 'status':'hypothesis; hidden answer not inspected',
                      'header_coordinates':[list(p) for p in lookup_positions(parse_grid(pair['input']))],
                      'output':predicted, 'output_sha256':grid_digest(predicted)})
    return {'focus_id':'d8e07eb2', 'challenge_sha256':FOCUS_SHA256,
            'program_sha256':sha256(materialize_program().encode()),
            'exact_train_matches':[not row['differences'] for row in train],
            'complete_line_requirement':'declared inference; partial aligned headers unresolved by public examples',
            'train':train, 'test_hypotheses':tests}


def dependency_witness(episode, oracle):
    """Swap catalog objects while preserving the complete visible header."""
    original = copy.deepcopy(episode['train'][0]['input'])
    info = parse_grid(original)
    selected = set(lookup_positions(info))
    if len({r for r,c in selected}) != 1 or len(selected) != info['cols']:
        raise ValueError('dependency witness requires a full-row teaching input')
    chosen = sorted(selected)[0]
    other = next((r,c) for r in range(info['rows']) for c in range(info['cols']) if (r,c) not in selected)
    changed = copy.deepcopy(original)
    for dy in range(3):
        for dx in range(3):
            ar,ac = 8+5*chosen[0]+dy, 2+5*chosen[1]+dx
            br,bc = 8+5*other[0]+dy, 2+5*other[1]+dx
            changed[ar][ac],changed[br][bc] = original[br][bc],original[ar][ac]
    before = oracle.apply(DEFAULT,original)
    after = oracle.apply(DEFAULT,changed)
    assert original[:5] == changed[:5]
    assert set(before[-1]) == {3} and set(after[-1]) == {2}
    return {'status':'lawful contextual dependency witness',
            'intervention':'swap one selected catalog glyph with an unselected glyph in another row; header unchanged',
            'swapped_catalog_coordinates':[list(chosen),list(other)],
            'before':{'input':original, 'output':before},
            'after':{'input':changed, 'output':after},
            'program_sha256':sha256(materialize_program().encode()),
            'before_coordinates':[list(p) for p in lookup_positions(info)],
            'after_coordinates':[list(p) for p in lookup_positions(parse_grid(changed))]}


def write_export(episodes, out_dir, oracle, public_analysis=None):
    if not episodes:
        raise ValueError('export needs at least one episode')
    rows = [(public_challenge_id(ep), public_challenge_bytes(ep), ep) for ep in episodes]
    if len({payload for _,payload,_ in rows}) != len(rows):
        raise ValueError('duplicate visible public payload')
    rows.sort(key=lambda row:row[0])
    out_dir = Path(out_dir)
    if out_dir.exists():
        raise ValueError('output path must be new')
    # All validation precedes filesystem mutation; private labels must be genuine
    # matching-Racket results, regardless of caller-provided episode metadata.
    for cid,payload,ep in rows:
        mode = ep['params']['alignment_mode']
        if mode not in ALIGNMENTS:
            raise ValueError('invalid episode parameter')
        all_pairs = ep['train'] + ep['test']
        # Validate private query labels with the same exact-integer grid
        # contract as demonstration labels; Python equality accepts 1.0 == 1.
        public_challenge_bytes({'train':all_pairs, 'test':[{'input':all_pairs[0]['input']}]})
        if len({grid_digest(p['input']) for p in all_pairs}) != len(all_pairs):
            raise ValueError('duplicate input inside episode')
        if any(oracle.apply(mode,p['input']) != p['output'] for p in all_pairs):
            raise ValueError('episode labels disagree with matching Racket')
        if certify(ep,oracle)['surviving_models'] != [mode]:
            raise ValueError('episode demonstrations do not identify fixed rule')
    public_dir, private_dir = out_dir/'public', out_dir/'private'
    public_dir.mkdir(parents=True)
    private_dir.mkdir()
    programs = {}
    for model in MODELS:
        program = materialize_program(model)
        digest = sha256(program.encode())
        (private_dir/(digest+'.rkt')).write_text(program)
        programs[model] = {'sha256':digest, 'path':'private/'+digest+'.rkt'}
    for cid,payload,ep in rows:
        (public_dir/(cid+'.json')).write_bytes(payload)
        private_episode = copy.deepcopy(ep)
        private_episode['certificate'] = certify(ep, oracle)
        (private_dir/(cid+'.json')).write_text(compact(private_episode)+'\n')
    if public_analysis is not None:
        (private_dir/'public-focus-analysis.json').write_text(compact(public_analysis)+'\n')
    # Only a full-row first demonstration supports this particular intervention.
    anchor = next((ep for _,_,ep in rows if ep['sampling']['scenes'][0]['scenario'] == 'row'), None)
    if anchor is not None:
        (private_dir/'dependency-witness.json').write_text(compact(dependency_witness(anchor,oracle))+'\n')
    source_paths = {'prototype':Path(__file__), 'focus_challenge':HERE/'focus_challenge.json',
                    'public_projection':RUNTIME/'reviewer_support.py',
                    'selected_generator_context_only':REPO/'generators/6fde852adb54/generator.py'}
    manifest = {'schema':'proposed-focus-catalog-export-v1', 'focus_id':'d8e07eb2',
                'status':'proposed; not approved; no verified lineage or measured difficulty',
                'canonical_replacement':False, 'default_is_inferred_focus_rule':True,
                'public_ids':[cid for cid,payload,ep in rows], 'programs':programs,
                'source_sha256':{name:sha256(path.read_bytes()) for name,path in source_paths.items()},
                'runtime':oracle.runtime_identity, 'racket_evaluations':oracle.evaluations,
                'racket_records':oracle.records,
                'public_observation':'4/5 exact train matches; train 0 has 9 header cells inconsistent with inferred rule',
                'limits':['finite seven-model certificate only',
                          'full-line completion is an explicit inference for partial aligned headers',
                          'background 8, separator 6, highlight 3 and failure 2 remain fixed',
                          'no original canonical/default claim; no hidden evaluation answers used']}
    (out_dir/'export.json').write_text(compact(manifest)+'\n')
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, default=17)
    parser.add_argument('--settings', nargs='+', choices=ALIGNMENTS, default=list(ALIGNMENTS))
    parser.add_argument('--train', type=int, default=3)
    parser.add_argument('--test', type=int, default=4)
    parser.add_argument('--max-attempts', type=int, default=128)
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--analyze-public', action='store_true')
    args = parser.parse_args(argv)
    oracle = RacketOracle()
    try:
        episodes = [generate_episode(seed=args.seed, alignment_mode=mode, n_train=args.train,
                    n_test=args.test, max_attempts=args.max_attempts, oracle=oracle) for mode in args.settings]
        analysis = analyze_public(oracle) if args.analyze_public else None
        receipt = write_export(episodes,args.out,oracle,analysis)
        print(compact({'out':str(args.out), 'public_ids':receipt['public_ids'],
                       'racket_evaluations':receipt['racket_evaluations'],
                       'train':args.train, 'test':args.test, 'settings':len(episodes)}))
    finally:
        oracle.close()


if __name__ == '__main__':
    main()
