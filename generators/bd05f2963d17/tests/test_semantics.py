"""Independent rule and declared-rival regressions for bd05f2963d17.

The retained reference fixtures are handmade validator-only evidence, not
claims that the sampler emitted those grids. Generated-support assertions use
fresh default draws below. No solve files or generator parsing helpers are used.
"""
from __future__ import annotations

from importlib import util
import json
from pathlib import Path
import sys

import pytest


# A library and a copied runtime expose the same public helper in different
# places. Bind discovery to this file, never the caller's working directory.
try:
    from reviewer_support import canonical_pairs, find_root, normalize_grid
except ModuleNotFoundError as error:
    if error.name != "reviewer_support":
        raise
    for ancestor in Path(__file__).resolve().parents:
        helper_home = ancestor / "shared/runtime"
        if (helper_home / "reviewer_support.py").is_file():
            sys.path.insert(0, str(helper_home))
            break
    else:
        raise
    from reviewer_support import canonical_pairs, find_root, normalize_grid


TASK_ID = "bd05f2963d17"
ROOT = find_root(__file__)
GENERATOR_CANDIDATES = (
    ROOT / "generators" / TASK_ID / "generator.py",
    ROOT / "puzzle_generators/per_puzzle" / TASK_ID / "generator.py",
)
GENERATOR_PATH = next(path for path in GENERATOR_CANDIDATES if path.is_file())
for runtime_home in (ROOT, ROOT / "shared/runtime"):
    if (runtime_home / "puzzle_generators/base.py").is_file():
        sys.path.insert(0, str(runtime_home))
        break


def components(grid):
    """Independent four-neighbor flood fill of the green cells."""
    unseen = {(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 3}
    found = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        cells, frontier = {start}, [start]
        while frontier:
            r, c = frontier.pop()
            for neighbor in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if neighbor in unseen:
                    unseen.remove(neighbor)
                    cells.add(neighbor)
                    frontier.append(neighbor)
        found.append(cells)
    return found


def bbox(cells):
    return (min(r for r, _ in cells), min(c for _, c in cells),
            max(r for r, _ in cells), max(c for _, c in cells))


def size_key(cells):
    r0, c0, _, _ = bbox(cells)
    return len(cells), r0, c0


def bbox_key(cells):
    r0, c0, r1, c1 = bbox(cells)
    return (r1 - r0 + 1) * (c1 - c0 + 1), r0, c0


def selected(grid):
    return sorted(components(grid), key=size_key)[1]


def paint_scaled(grid, cells, *, fixed_shape=None, first_cell_anchor=False):
    r0, c0, _, _ = bbox(cells)
    offsets = {(r - r0, c - c0) for r, c in cells}
    if fixed_shape is not None:
        offsets = fixed_shape
    if first_cell_anchor:
        r0, c0 = min(cells)
    output = [[0] * len(grid[0]) for _ in grid]
    for r, c in offsets:
        for dr in range(2):
            for dc in range(2):
                rr, cc = r0 + 2 * r + dr, c0 + 2 * c + dc
                # The reference painter clips. Lawful generated inputs are
                # separately required to fit the selected object's whole box.
                if 0 <= rr < len(grid) and 0 <= cc < len(grid[0]):
                    output[rr][cc] = 8
    return output


def reference_output(grid):
    return paint_scaled(grid, selected(grid))


def selection_rival(grid, selector):
    return paint_scaled(grid, selector(components(grid)))


# This maps implemented independent competitors to stable IDs. The declarations
# below are read dynamically from the generator; adding a declared ID without an
# executable competitor fails visibly rather than silently shrinking coverage.
RIVAL_IMPLEMENTATIONS = {
    "second_largest": lambda g: selection_rival(g, lambda os: sorted(os, key=size_key)[-2]),
    "lower_median": lambda g: selection_rival(g, lambda os: sorted(os, key=size_key)[(len(os) - 1) // 2]),
    "upper_median": lambda g: selection_rival(g, lambda os: sorted(os, key=size_key)[len(os) // 2]),
    "fixed_size_4": lambda g: selection_rival(g, lambda os: next(
        (o for o in sorted(os, key=size_key) if len(o) == 4), min(os, key=size_key))),
    "bottommost": lambda g: selection_rival(g, lambda os: max(os, key=lambda o: bbox(o)[:2])),
    "bbox_second": lambda g: selection_rival(g, lambda os: sorted(os, key=bbox_key)[1]),
    "fixed_S_stamp": lambda g: paint_scaled(g, selected(g), fixed_shape={(0, 0), (0, 1), (1, 1), (1, 2)}),
    "first_cell_anchor": lambda g: paint_scaled(g, selected(g), first_cell_anchor=True),
}


def declared_rivals(generator, attribute):
    declared = getattr(generator, attribute, None)
    assert declared, f"Generator must declare a nonempty {attribute}"
    names = tuple(declared)
    assert len(set(names)) == len(names), f"Duplicate IDs in {attribute}: {names}"
    unknown = set(names) - RIVAL_IMPLEMENTATIONS.keys()
    assert not unknown, f"Implement independent competitors for declared IDs: {sorted(unknown)}"
    return {name: RIVAL_IMPLEMENTATIONS[name] for name in names}


@pytest.fixture(scope="module")
def generator():
    spec = util.spec_from_file_location("bd05f2963d17_semantics_under_test", GENERATOR_PATH)
    module = util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def canonical():
    return canonical_pairs(TASK_ID, root=ROOT)


@pytest.fixture(scope="module")
def retained_witnesses():
    candidates = (
        ROOT / "generators" / TASK_ID / "counterexamples/semantic_rivals.json",
        GENERATOR_PATH.parent / "counterexamples/semantic_rivals.json",
    )
    path = next(path for path in candidates if path.is_file())
    record = json.loads(path.read_text())
    assert record["origin"] == "handmade"
    assert record["support_scope"] == "validator_only"
    assert record["reference"]["rule_hash_matches_catalog"] is True
    return [{**case, "input": normalize_grid(case["input"]),
             "output": normalize_grid(case["output"])} for case in record["cases"]]


@pytest.fixture(scope="module")
def default_draws(generator):
    # 4 bands x 4 seeds x 16 indices = 256 draws, shared by all support tests.
    # Every schedule phase and overlapping four-pair window is represented.
    draws = []
    for band in (None, "easy", "medium", "hard"):
        for seed in (0, 1, 17, 104729):
            for index in range(16):
                case = {"band": band, "seed": seed, "index": index}
                try:
                    case["input"] = generator.generate(seed, index, difficulty=band)
                except Exception as error:
                    case["generation_error"] = repr(error)
                draws.append(case)
    return draws


def checked_input(case):
    assert "generation_error" not in case, case
    grid = case["input"]
    assert normalize_grid(grid) == grid, case
    return grid


def test_independent_oracle_matches_all_canonical_pairs(canonical):
    assert canonical
    for case in canonical:
        assert reference_output(case["input"]) == case["output"], (
            case["variant"], case["split"], case["pair_index"])


def test_every_declared_canonical_shortcut_fits_every_canonical_pair(generator, canonical):
    rivals = declared_rivals(generator, "CANONICAL_SHORTCUTS")
    for case in canonical:
        for name, predict in rivals.items():
            assert predict(case["input"]) == case["output"], (
                name, case["variant"], case["split"], case["pair_index"])


def test_exact_retained_racket_outputs(retained_witnesses):
    for case in retained_witnesses:
        assert reference_output(case["input"]) == case["output"], case["name"]


def test_lawful_handmade_witnesses_are_validator_accepted(generator, retained_witnesses):
    for case in retained_witnesses:
        assert generator.self_check(case["input"]) == [], case["name"]


def test_default_draws_preserve_the_rule_domain(generator, default_draws):
    for case in default_draws:
        grid = checked_input(case)
        objects = components(grid)
        assert 3 <= len(objects) <= 5, case
        assert len({len(o) for o in objects}) == len(objects), case
        assert set(v for row in grid for v in row) <= {0, 3}, case
        target = selected(grid)
        r0, c0, r1, c1 = bbox(target)
        assert r0 + 2 * (r1 - r0 + 1) <= len(grid), case
        assert c0 + 2 * (c1 - c0 + 1) <= len(grid[0]), case
        output = reference_output(grid)
        assert sum(v == 8 for row in output for v in row) == 4 * len(target), case
        assert generator.self_check(grid) == [], case


@pytest.mark.parametrize("band", (None, "easy", "medium", "hard"))
def test_odd_default_draws_defeat_all_declared_lesson_rivals(generator, default_draws, band):
    rivals = declared_rivals(generator, "LESSON_COMPETITORS")
    cases = [case for case in default_draws if case["band"] == band and case["index"] % 2]
    assert cases
    for case in cases:
        grid = checked_input(case)
        expected = reference_output(grid)
        assert len(components(grid)) == 5, case
        for name, predict in rivals.items():
            assert predict(grid) != expected, (name, case)


def test_every_four_pair_window_teaches_declared_rivals_after_any_one_query_holdout(generator, default_draws):
    assert getattr(generator, "EXAMPLES_NEEDED", None) == 3
    assert getattr(generator, "LESSON_SCHEDULE_PERIOD", None) == 4
    rivals = declared_rivals(generator, "LESSON_COMPETITORS")
    for band in (None, "easy", "medium", "hard"):
        for seed in (0, 1, 17, 104729):
            cases = [case for case in default_draws if case["band"] == band and case["seed"] == seed]
            failures = []
            for case in cases:
                grid = checked_input(case)
                expected = reference_output(grid)
                failures.append({name for name, predict in rivals.items() if predict(grid) != expected})
            for start in range(len(cases) - 3):
                window = failures[start:start + 4]
                for query in range(4):
                    for name in rivals:
                        assert any(name in failed for index, failed in enumerate(window) if index != query), (
                            "rival survives all three demonstrations", name, band, seed, start, query)


@pytest.mark.parametrize("band", (None, "easy", "medium", "hard"))
def test_even_general_draws_include_five_components_with_nonfive_target(default_draws, band):
    targets = []
    for case in default_draws:
        if case["band"] != band or case["index"] % 2:
            continue
        grid = checked_input(case)
        if len(components(grid)) == 5:
            targets.append(len(selected(grid)))
    assert targets, f"No five-component general draw in bounded support probe for band={band!r}"
    assert any(size != 5 for size in targets), (band, targets)


@pytest.mark.parametrize("count", (3, 4))
def test_explicit_lower_component_counts_do_not_inherit_default_teaching_claim(generator, count):
    # These eight override draws are checked for their own lawful contract only;
    # median separation is intentionally not demanded from an explicit 3/4 draw.
    for band in (None, "easy", "medium", "hard"):
        grid = generator.generate(17, 1, difficulty=band, n_components=count)
        assert len(components(grid)) == count, (band, count)
        assert generator.self_check(grid) == [], (band, count)


def test_production_success_does_not_bless_witness_query_rotation(generator, canonical, retained_witnesses):
    """Intentional teaching negative: holding out the only witness loses the rule."""
    strong = next(case for case in retained_witnesses if case["name"] == "strong_size5_cross")
    train = [case for case in canonical if case["split"] == "train"]
    assert len(train) >= 3
    lesson = [train[0], strong, train[1], train[2]]
    # The original production query is harmless because its demos include the witness.
    assert generator.lesson_identifiable(lesson[:3], lesson[3]) == []
    # A permitted query rotation can remove that sole witness from the demos.
    rivals = declared_rivals(generator, "LESSON_COMPETITORS")
    ambiguous = {name for name, predict in rivals.items()
                 if all(predict(pair["input"]) == pair["output"] for pair in train[:3])
                 and predict(strong["input"]) != strong["output"]}
    assert ambiguous
    reasons = generator.lesson_identifiable(train[:3], strong)
    assert len(reasons) == len(ambiguous)
    assert all(any(reason.startswith(name + " ") for reason in reasons)
               for name in ambiguous)


@pytest.mark.parametrize("index", (0, 1), ids=("general", "teaching"))
def test_forced_compact_fallback_preserves_exact_controls(generator, monkeypatch, index):
    """Exercise the real fallback output when the random placement budget expires."""
    monkeypatch.setattr(generator, "_try_placement", lambda *args, **kwargs: None)
    rivals = declared_rivals(generator, "LESSON_COMPETITORS")
    for band in (None, "easy", "medium", "hard"):
        for count in (3, 4, 5):
            for height, width in ((10, 11), (16, 17)):
                grid = generator.generate(17, index, difficulty=band,
                                          grid_h=height, grid_w=width, n_components=count)
                assert (len(grid), len(grid[0])) == (height, width)
                assert len(components(grid)) == count
                assert generator.self_check(grid) == []
                expected = reference_output(grid)
                assert sum(value == 8 for row in expected for value in row) == 4 * len(selected(grid))
                if index == 1 and count == 5:
                    assert all(predict(grid) != expected for predict in rivals.values())
