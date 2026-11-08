"""Behavioral regressions; canonical labels are authoring-only reference data."""
from collections import Counter, defaultdict
import importlib.util
from pathlib import Path
import json

import pytest
from reviewer_support import canonical_pairs, find_root

TASK = "f191c16f6179"
ROOT = find_root(__file__)
GEN_PATH = next(p for p in (
    ROOT / "generators" / TASK / "generator.py",
    ROOT / "puzzle_generators" / "per_puzzle" / TASK / "generator.py",
) if p.is_file())
spec = importlib.util.spec_from_file_location("f191c16f6179_under_test", GEN_PATH)
gen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gen)


def positions(grid):
    found = defaultdict(list)
    for r, row in enumerate(grid):
        for c, color in enumerate(row):
            if color:
                found[color].append((r, c))
    return dict(found)


def expected_bridge(grid):
    """Independent test oracle derived from the unchanged rule's four guards."""
    out = [row[:] for row in grid]
    for color, cells in positions(grid).items():
        if len(cells) != 2:
            continue
        (r0, c0), (r1, c1) = cells
        dr, dc = r1 - r0, c1 - c0
        if abs(dr) != abs(dc) or abs(dr) < 2:
            continue
        interior = [(r0 + k, c0 + k * (1 if dc > 0 else -1))
                    for k in range(1, dr)]
        if any(grid[r][c] != 0 for r, c in interior):
            continue
        for r, c in interior:
            out[r][c] = color
    return out


@pytest.mark.parametrize("pair", canonical_pairs(TASK, root=ROOT), ids=lambda p: f"{p['split']}-{p['pair_index']}")
def test_canonical_inputs_are_in_domain(pair):
    # Catches the old validator's rejection of the two unchanged query colors.
    assert gen.self_check(pair["input"]) == []
    assert expected_bridge(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", ["easy", "medium", "hard"])
@pytest.mark.parametrize("shape", [(5, 5), (5, 16), (16, 5), (16, 16)])
@pytest.mark.parametrize("pairs", [1, 3, 5])
def test_exact_controls_cross_difficulty_boundaries(band, shape, pairs):
    # Detects narrowed band-specific override ranges and silently short placement.
    for index in range(3):
        g = gen.generate(23, index, difficulty=band,
                         grid_h=shape[0], grid_w=shape[1], pairs=pairs)
        assert (len(g), len(g[0])) == shape
        assert sum(len(cells) == 2 for cells in positions(g).values()) == pairs
        assert gen.self_check(g, difficulty=band) == []
        assert gen.observe_overrides(g) == {"grid_h": shape[0], "grid_w": shape[1], "pairs": pairs}


@pytest.mark.parametrize("key,value", [("grid_h", True), ("grid_h", 8.9), ("grid_w", "8"), ("pairs", "3"), ("pairs", False)])
def test_noninteger_controls_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize("key", ["palette_kind", "palette_size", "n_distinct_colors", "position_bias", "density", "texture", "unknown_typo"])
def test_removed_or_unknown_controls_fail_loudly(key):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: "bogus"})


@pytest.mark.parametrize("key,value", [("grid_h", 4), ("grid_w", 17), ("pairs", 0), ("pairs", 6)])
def test_out_of_range_controls_are_rejected(key, value):
    with pytest.raises((TypeError, ValueError)):
        gen.generate(0, 0, **{key: value})


def test_none_controls_preserve_default_draw():
    assert gen.generate(3, 2, grid_h=None, grid_w=None, pairs=None) == gen.generate(3, 2)


@pytest.mark.parametrize("grid", [[], [[]], [[0], [0, 0]], [[True]*5 for _ in range(5)], [[0]*5 for _ in range(5)]])
def test_malformed_and_empty_semantics_are_rejected(grid):
    assert gen.self_check(grid)


def test_default_draws_are_nonidentity_deterministic_and_do_not_mutate_overrides():
    for band in ("easy", "medium", "hard"):
        for index in range(30):
            kwargs = {"difficulty": band}
            a = gen.generate(517, index, **kwargs)
            assert a == gen.generate(517, index, **kwargs)
            assert kwargs == {"difficulty": band}
            assert gen.self_check(a, difficulty=band) == []
            assert expected_bridge(a) != a


def test_guard_witnesses_have_real_counterexamples():
    # Removing a semantic branch, or confusing presence with refutation, fails.
    assert callable(getattr(gen, "strict_canonical_like", None))
    witnesses = getattr(gen, "SEMANTIC_WITNESSES", {})
    rivals = getattr(gen, "SEMANTIC_RIVALS", {})
    claims = getattr(gen, "WITNESS_RIVALS", {})
    assert len(witnesses) >= 5 and len(rivals) >= 7
    seen = Counter()
    for band in ("easy", "medium", "hard"):
        for index in range(24):
            g = gen.generate(101, index, difficulty=band)
            want = expected_bridge(g)
            assert gen.strict_canonical_like(g) in ([], True)
            for name, predicate in witnesses.items():
                if predicate(g):
                    seen[name] += 1
                    assert claims.get(name), name
                    assert any(rivals[rival](g) != want for rival in claims[name]), name
    assert set(seen) == set(witnesses)


def test_ordered_three_demo_lessons_refute_query_changing_rivals():
    competitors = getattr(gen, "LESSON_COMPETITORS", {})
    assert competitors, "Declare executable lesson competitors"
    for seed in range(12):
        for start in range(3):
            grids = [gen.generate(seed, start+i, difficulty="medium") for i in range(4)]
            labels = [expected_bridge(g) for g in grids]
            for name, rival in competitors.items():
                predictions = [rival(g) for g in grids]
                if predictions[:3] == labels[:3]:
                    assert predictions[3] == labels[3], (seed, start, name)


def test_domain_admits_reference_guard_witnesses():
    # Reproduces blocked inputs, reading-order crossings, and a third off-path cell.
    data = json.loads((GEN_PATH.parent / "counterexamples" / "guard_cases.json").read_text())
    for case in data["cases"]:
        assert gen.self_check(case["input"]) == [], case["name"]
        assert expected_bridge(case["input"]) == case["output"], case["name"]


def test_generated_inputs_against_actual_racket_labels():
    # Catches errors in the Python diagnostic oracle used by the fast tests.
    from arc_repl.executor import ArcExecutor
    from arc_repl.builtins import _unwrap
    from reviewer_support import canonical_path
    row = next(row for line in canonical_path(ROOT).open()
               if (row := json.loads(line)).get("task_id") == TASK)
    grids = [gen.generate(199, i, difficulty=band)
             for band in ("easy", "medium", "hard") for i in range(3)]
    guard_cases = json.loads((GEN_PATH.parent / "counterexamples" / "guard_cases.json").read_text())["cases"]
    grids.extend(case["input"] for case in guard_cases)
    task = {"train": [], "test": [{"input": g} for g in grids]}
    with ArcExecutor(task, use_racket=True) as executor:
        registered = executor.step(row["program_solution"])
        assert not registered.startswith("ERROR:"), registered
        for index, grid in enumerate(grids):
            applied = executor.step(f"(apply! {index})")
            assert not applied.startswith("ERROR:"), applied
            output = _unwrap(executor._results[f"_{index+1}"])
            if hasattr(output, "tolist"):
                output = output.tolist()
            assert output == expected_bridge(grid), (index, grid)
