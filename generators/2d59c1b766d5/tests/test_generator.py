"""Focused regressions for the two-frame gate-and-wall flood task.

The tests deliberately use an independent frame parser and component counter so
that generator metadata cannot make its own contract pass.  Canonical labels
and the optional Racket parity check come through public review/runtime APIs.
"""
from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path

import pytest
from arcpuzzles import Catalog
from reviewer_support import canonical_pairs, find_root

TASK_ID = "2d59c1b766d5"
TASK_DIR = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("gate_frames_under_test", TASK_DIR / "generator.py")
gen = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
_spec.loader.exec_module(gen)

DIR4 = ((-1, 0), (1, 0), (0, -1), (0, 1))
DIR8 = DIR4 + ((-1, -1), (-1, 1), (1, -1), (1, 1))


def _accepts(value):
    return value is True or value == []


def _components(cells, directions):
    remaining = set(cells)
    result = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = [start]
        comp = {start}
        for r, c in queue:
            for dr, dc in directions:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    comp.add(nxt)
                    queue.append(nxt)
        result.append(comp)
    return result


def _frames(grid):
    eights = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 8}
    frames = []
    for comp in _components(eights, DIR4):
        rs = [r for r, _ in comp]
        cs = [c for _, c in comp]
        r0, r1, c0, c1 = min(rs), max(rs), min(cs), max(cs)
        border = {
            (r, c)
            for r in range(r0, r1 + 1)
            for c in range(c0, c1 + 1)
            if r in (r0, r1) or c in (c0, c1)
        }
        assert comp == border
        frames.append((r0, c0, r1, c1))
    return sorted(frames)


def _profile(grid):
    labels = []
    for r0, c0, r1, c1 in _frames(grid):
        free = {
            (r, c)
            for r in range(r0 + 1, r1)
            for c in range(c0 + 1, c1)
            if grid[r][c] != 5
        }
        n4 = len(_components(free, DIR4))
        n8 = len(_components(free, DIR8))
        labels.append("open" if n4 == 1 else "diagonal" if n8 == 1 else "sealed")
    assert len(set(labels)) == 1
    return labels[0]


def _independent_observation(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "profile": _profile(grid)}


@pytest.fixture(scope="module")
def canonical():
    return canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True)


def test_rule_pin_and_all_five_canonical_pairs_are_exact(canonical):
    assert gen.RULE_HASH == "61c97755a0ea"
    assert len(canonical) == 5
    for pair in canonical:
        assert gen.self_check(pair["input"]) == []
        assert _accepts(gen.strict_canonical_like(pair["input"]))
        assert gen.rule_output(pair["input"]) == pair["output"]
        assert gen.CANONICAL_SHORTCUTS["fill_all_interior"](pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", (None, "easy", "medium", "hard"))
@pytest.mark.parametrize(
    "options",
    (
        {"grid_h": 15, "grid_w": 20, "profile": "open"},
        {"grid_h": 16, "grid_w": 21, "profile": "sealed"},
        {"grid_h": 17, "grid_w": 22, "profile": "diagonal"},
    ),
)
def test_exact_axes_are_observable_in_every_difficulty_band(band, options):
    grid = gen.generate(417, 11, difficulty=band, **options)
    assert _independent_observation(grid) == options
    assert gen.observe_overrides(grid) == options
    assert gen.self_check(grid, difficulty=band) == []
    assert _accepts(gen.strict_canonical_like(grid))
    assert gen.rule_output(grid) != grid


def test_period_three_schedule_survives_every_query_rotation():
    assert gen.EXAMPLES_NEEDED == 5
    assert tuple(gen.SCHEDULE_PROFILES) == ("open", "sealed", "diagonal")
    for start in range(6):
        grids = [gen.generate(801, start + offset) for offset in range(6)]
        assert [_profile(grid) for grid in grids] == [
            gen.schedule_profile(801, start + offset) for offset in range(6)
        ]
        for query in range(6):
            demo_profiles = {_profile(grid) for i, grid in enumerate(grids) if i != query}
            assert demo_profiles == set(gen.SCHEDULE_PROFILES)


def test_generated_witnesses_refute_canonical_fitting_shortcuts():
    open_grid = gen.generate(51, 0, profile="open")
    sealed = gen.generate(51, 1, profile="sealed")
    diagonal = gen.generate(51, 2, profile="diagonal")

    assert gen.rule_output(open_grid) == gen.SEMANTIC_RIVALS["fill_all_interior"](open_grid)
    assert gen.rule_output(sealed) != gen.SEMANTIC_RIVALS["fill_all_interior"](sealed)
    assert gen.rule_output(diagonal) != gen.SEMANTIC_RIVALS["fill_all_interior"](diagonal)
    assert gen.rule_output(diagonal) != gen.SEMANTIC_RIVALS["eight_neighbor_flood"](diagonal)
    assert gen.SEMANTIC_WITNESSES["unreachable_chamber"](sealed)
    assert gen.SEMANTIC_WITNESSES["four_neighbor_connectivity"](diagonal)


@pytest.mark.parametrize(
    "key,value,error",
    (
        ("grid_h", 14, ValueError),
        ("grid_h", 18, ValueError),
        ("grid_w", 19, ValueError),
        ("grid_w", 23, ValueError),
        ("grid_h", True, TypeError),
        ("grid_w", 20.0, TypeError),
        ("profile", "motif", ValueError),
        ("profile", 1, ValueError),
        ("unknown_axis", 1, TypeError),
    ),
)
def test_invalid_controls_are_rejected(key, value, error):
    with pytest.raises(error):
        gen.generate(0, 0, **{key: value})


@pytest.mark.parametrize(
    "seed,sample_index,error",
    (
        (True, 0, TypeError),
        (1.0, 0, TypeError),
        ("1", 0, TypeError),
        (1, True, TypeError),
        (1, 1.0, TypeError),
        (1, "1", TypeError),
        (1, -1, ValueError),
    ),
)
def test_seed_and_sample_index_are_strict_scalars(seed, sample_index, error):
    with pytest.raises(error):
        gen.generate(seed, sample_index)


def test_none_overrides_keep_default_draws():
    assert gen.generate(12, 7, grid_h=None, grid_w=None, profile=None) == gen.generate(12, 7)


@pytest.mark.parametrize(
    "grid",
    (
        None,
        [],
        [[]],
        [[0], [0, 1]],
        [[True] * 20 for _ in range(15)],
        [[0] * 20 for _ in range(15)],
        [[10] + [0] * 19 for _ in range(15)],
    ),
)
def test_malformed_inputs_are_diagnostic_not_exceptions(grid):
    result = gen.self_check(grid)
    assert isinstance(result, list) and result


def test_validator_rejects_destructive_mutations_and_rule_is_pure():
    base = gen.generate(38, 2, profile="diagonal")
    original = deepcopy(base)
    assert gen.rule_output(base) != base
    assert base == original

    mutations = []
    g = deepcopy(base); g[0][0] = 9; mutations.append(g)
    g = deepcopy(base); r0, c0, _, _ = _frames(g)[0]; g[r0][c0] = 0; mutations.append(g)
    g = deepcopy(base)
    r0, c0, r1, c1 = _frames(g)[0]
    for r in range(r0 + 1, r1):
        for c in range(c0 + 1, c1):
            if g[r][c] not in (0, 5):
                g[r][c] = 0
    mutations.append(g)
    for mutated in mutations:
        assert gen.self_check(mutated)


def test_generation_is_deterministic_and_returns_fresh_grids():
    first = gen.generate(991, 19, difficulty="hard")
    second = gen.generate(991, 19, difficulty="hard")
    assert first == second and first is not second
    first[0][0] = 7
    assert gen.generate(991, 19, difficulty="hard") == second


def test_real_racket_matches_independent_mirror_on_canonical_and_profiles(canonical):
    grids = [pair["input"] for pair in canonical]
    grids.extend(gen.generate(219, i, profile=name) for i, name in enumerate(gen.SCHEDULE_PROFILES))
    applied = Catalog().apply(TASK_ID, grids, timeout=120)
    assert applied["rule_hash_matches_catalog"]
    assert all(item["valid_output"] and item["error"] is None for item in applied["results"])
    assert [item["output"] for item in applied["results"]] == [gen.rule_output(grid) for grid in grids]


def test_retained_counterexamples_regenerate_and_refute_named_rivals():
    cases = {
        "sealed_fill_all.json": ("fill_all_interior",),
        "diagonal_joint_witness.json": ("fill_all_interior", "eight_neighbor_flood"),
    }
    for filename, rival_names in cases.items():
        payload = __import__("json").loads(
            (TASK_DIR / "counterexamples" / filename).read_text(encoding="utf-8")
        )
        regenerated = gen.generate(
            payload["seed"], payload["sample_index"], **payload["overrides"]
        )
        assert regenerated == payload["input"]
        assert gen.rule_output(regenerated) == payload["racket_output"]
        for name in rival_names:
            rival = gen.SEMANTIC_RIVALS[name](regenerated)
            assert rival == payload["rival_outputs"][name]
            assert rival != payload["racket_output"]


def test_future_agent_curriculum_probe_is_source_bound_and_rotation_complete():
    import sys

    workspace = TASK_DIR / "workspace"
    sys.path.insert(0, str(workspace))
    try:
        import probe_curriculum

        report = probe_curriculum.build_report(include_racket=False)
    finally:
        sys.path.remove(str(workspace))
    assert report["task_id"] == TASK_ID
    assert report["rule_hash"] == gen.RULE_HASH
    assert report["generator_sha256"] == probe_curriculum.file_sha256(TASK_DIR / "generator.py")
    assert report["canonical"]["pair_count"] == 5
    assert report["canonical"]["python_mirror_matches_labels"] is True
    assert set(report["canonical"]["shortcuts_fitting_all_pairs"]) == {
        "fill_all_interior",
        "eight_neighbor_flood",
    }
    assert report["schedule"]["all_query_rotations_refute_every_rival"] is True
    assert report["witnesses"]["sealed"]["refutes"] == ["fill_all_interior"]
    assert set(report["witnesses"]["diagonal"]["refutes"]) == {
        "fill_all_interior",
        "eight_neighbor_flood",
    }
