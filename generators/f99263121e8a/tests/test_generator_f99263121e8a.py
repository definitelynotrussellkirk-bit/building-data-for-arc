"""Task-local regression tests; run explicitly (repo pytest does not collect these)."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path
import sys
import pytest

HOME = Path(__file__).resolve().parents[1]
ROOT = HOME.parents[1]
sys.path.insert(0, str(ROOT / 'shared/runtime'))
spec = importlib.util.spec_from_file_location('subject_f99263121e8a', HOME / 'generator.py')
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def components(grid):
    """Independent 4-connected same-color reference for observable assertions."""
    seen, out = set(), []
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color == 0 or (r, c) in seen:
                continue
            pending, cells = [(r, c)], set()
            seen.add((r, c))
            while pending:
                p = pending.pop()
                cells.add(p)
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = p[0]+dr, p[1]+dc
                    if (0 <= q[0] < len(grid) and 0 <= q[1] < len(row)
                            and q not in seen and grid[q[0]][q[1]] == color):
                        seen.add(q)
                        pending.append(q)
            out.append((color, cells))
    return out


def bbox(cells):
    return min(r for r,c in cells), min(c for r,c in cells), max(r for r,c in cells), max(c for r,c in cells)


@pytest.mark.parametrize('band', ['easy', 'medium', 'hard'])
@pytest.mark.parametrize('n', [2, 3, 6])
def test_component_override_is_exact(band, n):
    for seed in range(8):
        grid = gen.generate(seed, 0, difficulty=band, n_components=n)
        assert len(components(grid)) == n
        assert gen.self_check(grid, difficulty=band) == []


@pytest.mark.parametrize('name', ['typo', 'palette_kind', 'palette_size', 'n_distinct_colors', 'position_bias', 'density'])
def test_unknown_or_removed_inert_overrides_fail_loudly(name):
    with pytest.raises(ValueError, match='override|unsupported|unknown'):
        gen.generate(0, 0, **{name: 'unused'})


@pytest.mark.parametrize('kwargs', [
    {'n_components': 1}, {'n_components': 7}, {'n_components': True},
    {'grid_h': 7}, {'grid_h': 31}, {'grid_w': 8}, {'grid_w': 31},
    {'grid_h': 12.5}, {'grid_w': '10'}, {'texture': 'typo'},
])
def test_invalid_overrides_fail_loudly(kwargs):
    with pytest.raises(ValueError):
        gen.generate(1, 0, **kwargs)


@pytest.mark.parametrize('texture', ['no_components', 'single_component'])
def test_negative_fixtures_remain_outside_ordinary_domain(texture):
    assert texture not in gen.AXES['texture']['valid'].split('|')
    assert gen.self_check(gen.generate(1, 0, texture=texture))


@pytest.mark.parametrize('texture', ['canonical','scattered','crop_overlap','shared_color','wide_narrow','equal_leftmosts','diagonal_contact'])
def test_geometry_modes_are_real_exact_and_bounded(texture):
    for seed in range(10):
        g = gen.generate(seed, 0, texture=texture, n_components=3, grid_h=12, grid_w=13)
        cs = components(g)
        boxes = [bbox(cells) for _, cells in cs]
        assert (len(g), len(g[0]), len(cs)) == (12, 13, 3)
        assert gen.self_check(g) == []
        assert sum(b[2]-b[0]+1 for b in boxes) + len(cs)-1 <= 30
        if texture == 'crop_overlap':
            assert any(g[r][c] not in (0, color)
                       for color,cells in cs for r in range(bbox(cells)[0], bbox(cells)[2]+1)
                       for c in range(bbox(cells)[1],bbox(cells)[3]+1))
        if texture in ('shared_color', 'diagonal_contact'):
            assert len({color for color,cells in cs}) < len(cs)
        if texture == 'equal_leftmosts':
            assert len({b[1] for b in boxes}) < len(boxes)
        if texture == 'wide_narrow':
            widths = [b[3]-b[1]+1 for b in boxes]
            assert max(widths)-min(widths) >= 2


@pytest.mark.parametrize('bad', [[], [[]], [[0,1],[0]], [[-1]], [[10]], [[True]], [[1.5]], [['1']], '01'])
def test_selfcheck_rejects_malformed_grids_without_crashing(bad):
    assert gen.self_check(bad)


def test_selfcheck_rejects_output_above_arc_bounds():
    g = [[1,0,2] for _ in range(16)]
    assert gen.self_check(g)  # would stack to 33 rows


def test_canonical_labels_and_crop_neighbor_semantics():
    task = next(json.loads(s) for s in (ROOT / 'shared/data/canonical/puzzles.jsonl').open()
                if json.loads(s).get('task_id') == gen.TASK_ID)
    for pair in task['train'] + task['test']:
        assert gen.self_check(pair['input']) == []
        assert gen.rule_mirror(pair['input']) == pair['output']
        assert gen.strict_canonical_like(pair['input']) is True


def test_centering_is_not_left_alignment():
    g = [[0]*10 for _ in range(10)]
    g[1][1:6] = [2]*5
    for r in (4,5,6):
        g[r][2] = 3
    assert gen.rule_mirror(g) == [[2]*5, [0]*5, [0,0,3,0,0], [0,0,3,0,0], [0,0,3,0,0]]


def test_default_census_reproducibility_and_semantic_support():
    for band in ('easy','medium','hard'):
        witnesses = {name: 0 for name in gen.SEMANTIC_WITNESSES}
        strict_count = 0
        for seed in range(120):
            a = gen.generate(seed, seed % 7, difficulty=band)
            assert a == gen.generate(seed, seed % 7, difficulty=band)
            assert gen.self_check(a) == []
            strict_count += gen.strict_canonical_like(a)
            for name, pred in gen.SEMANTIC_WITNESSES.items():
                witnesses[name] += bool(pred(a))
        assert strict_count >= 20
        assert all(witnesses.values()), witnesses


def test_every_five_demo_sliding_window_refutes_named_query_rivals():
    # Regression for independently sampled examples leaving a query-changing
    # competitor alive. Any start offset must work, not just index zero.
    for band in ('easy', 'medium', 'hard'):
        for seed in range(8):
            grids = [gen.generate(seed, i, difficulty=band) for i in range(11)]
            for start in range(6):
                demos = [{'input':g, 'output':gen.rule_mirror(g)} for g in grids[start:start+5]]
                assert gen.lesson_identifiable(demos, {'input':grids[start+5]}) == []


def test_review_probe_wraps_rules_from_canonical_repository_layout():
    # The canonical tree calls this directory shared/tools; the inherited
    # Racket normalizer imports it as scripts in portable execution trees.
    import subprocess
    code = (
        "import importlib.util; "
        f"s=importlib.util.spec_from_file_location('probe', {str(Path(__file__).resolve().parents[1] / 'workspace/review_probe.py')!r}); "
        "m=importlib.util.module_from_spec(s); s.loader.exec_module(m); "
        "assert 'lambda' in m.wrap_rule('(rule! (lambda (g) g))')"
    )
    result = subprocess.run([sys.executable, '-c', code], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr

EXTENDED_RIVALS = {
    'sort_by_top', 'sort_by_color', 'sort_by_area', 'reverse_left_order',
    'ceil_center', 'gapless_stack', 'two_row_gap', 'left_then_bottom',
}


def test_extended_rival_library_is_declared():
    assert EXTENDED_RIVALS <= set(gen.SEMANTIC_RIVALS)


def test_order_conflict_profile_is_canonical_like_and_decisive():
    order_rivals = {'sort_by_top', 'sort_by_color', 'sort_by_area', 'reverse_left_order'}
    for seed in range(12):
        grid = gen.generate(seed, 0, texture='order_conflict',
                            n_components=3, grid_h=10, grid_w=10)
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid)
        intended = gen.rule_mirror(grid)
        for name in order_rivals:
            assert gen.SEMANTIC_RIVALS[name](grid) != intended, (seed, name)


def test_crop_overlap_also_teaches_equal_left_tie_order():
    for seed in range(12):
        grid = gen.generate(seed, 0, texture='crop_overlap',
                            n_components=3, grid_h=12, grid_w=13)
        boxes = [bbox(cells) for _, cells in components(grid)]
        assert len({box[1] for box in boxes}) < len(boxes)
        intended = gen.rule_mirror(grid)
        for name in ('mask_each_component', 'merge_touching_colors', 'left_then_bottom'):
            assert gen.SEMANTIC_RIVALS[name](grid) != intended, (seed, name)


def test_wide_narrow_teaches_floor_not_ceil_centering():
    for seed in range(12):
        grid = gen.generate(seed, 0, texture='wide_narrow',
                            n_components=3, grid_h=12, grid_w=13)
        intended = gen.rule_mirror(grid)
        assert gen.SEMANTIC_RIVALS['sort_by_right_edge'](grid) != intended
        assert gen.SEMANTIC_RIVALS['left_align'](grid) != intended
        assert gen.SEMANTIC_RIVALS['ceil_center'](grid) != intended


def test_gap_rivals_have_the_advertised_separator_counts():
    grid = [[0] * 8 for _ in range(8)]
    grid[1][1:5] = [2] * 4
    for row in (4, 5, 6):
        grid[row][6] = 3
    intended = gen.rule_mirror(grid)
    assert len(intended) == 5
    assert len(gen.SEMANTIC_RIVALS['gapless_stack'](grid)) == 4
    assert len(gen.SEMANTIC_RIVALS['two_row_gap'](grid)) == 6
    assert intended[2] == [0, 3, 0, 0]
    assert gen.SEMANTIC_RIVALS['ceil_center'](grid)[2] == [0, 0, 3, 0]


def test_rival_search_cli_finds_no_surviving_extended_rival(tmp_path):
    import subprocess
    tool = HOME / 'workspace/rival_search.py'
    report = tmp_path / 'rivals.json'
    result = subprocess.run(
        [sys.executable, str(tool), '--seeds', '8', '--out', str(report)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(report.read_text())
    assert payload['passed'] is True
    assert payload['surviving_windows'] == []
    assert set(payload['rivals']) >= EXTENDED_RIVALS


def test_rival_search_compound_mode_checks_cross_axis_shortcuts(tmp_path):
    import subprocess
    tool = HOME / 'workspace/rival_search.py'
    report = tmp_path / 'compound-rivals.json'
    result = subprocess.run(
        [sys.executable, str(tool), '--seeds', '2', '--compound', '--out', str(report)],
        cwd=ROOT, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stderr + result.stdout
    payload = json.loads(report.read_text())
    compound = payload['compound_search']
    assert compound['candidate_count'] == 503
    assert compound['surviving_windows'] == []
    assert compound['candidates_fitting_any_complete_window'] == 0
