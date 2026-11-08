"""Focused regression tests for Offset Cloud Replay (7a15f5e5ebd9)."""
from __future__ import annotations

import copy
import importlib.util
import random
from pathlib import Path

import pytest

from puzzle_generators import base as generator_base
from reviewer_support import canonical_pairs, find_root

TASK_ID = "7a15f5e5ebd9"
ROOT = find_root(__file__)


def _generator_path() -> Path:
    here = Path(__file__).resolve()
    candidates = (
        here.parents[1] / "generator.py",
        ROOT / f"puzzle_generators/per_puzzle/{TASK_ID}/generator.py",
        ROOT / f"generators/{TASK_ID}/generator.py",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    raise FileNotFoundError(f"no generator.py for {TASK_ID}: {candidates}")


def load_generator():
    path = _generator_path()
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return load_generator()


def _pairs():
    pairs = canonical_pairs(TASK_ID, root=ROOT)
    assert len(pairs) == 5
    return pairs


def test_all_canonical_pairs_are_accepted_exact_and_linked(gen):
    signatures = []
    for pair in _pairs():
        assert gen.self_check(pair["input"]) == []
        assert gen.strict_canonical_like(pair["input"]) == []
        assert gen.rule_mirror(pair["input"]) == pair["output"]
        signatures.append(gen.canonical_profile_signature(pair["input"]))
    assert set(signatures) == gen._CANONICAL_SIGNATURES
    assert len(set(signatures)) == 5


def test_declared_canonical_shortcuts_really_fit_every_canonical_pair(gen):
    assert gen.CANONICAL_SHORTCUTS
    for name, rival in gen.CANONICAL_SHORTCUTS.items():
        for pair in _pairs():
            assert rival(pair["input"]) == pair["output"], name


def test_default_prior_reaches_every_linked_profile_in_every_band(gen):
    for band in ("easy", "medium", "hard"):
        counts = {signature: 0 for signature in gen._CANONICAL_SIGNATURES}
        strict = 0
        for seed in range(200):
            grid = gen.generate(seed, seed * 17 + 3, difficulty=band)
            assert gen.self_check(grid, difficulty=band) == []
            signature = gen.canonical_profile_signature(grid)
            if signature is not None:
                counts[signature] += 1
                strict += 1
        assert strict >= 80, (band, strict, counts)
        assert all(count > 0 for count in counts.values()), (band, counts)


def test_every_four_slot_window_is_identifiable(gen):
    period = len(gen.SCHEDULE_PROFILES)
    for start in range(period):
        demos = []
        for offset in range(gen.EXAMPLES_NEEDED):
            grid = gen.generate(104729, (start + offset) % period, difficulty="medium")
            demos.append({"input": grid, "output": gen.rule_mirror(grid)})
        query_grid = gen.generate(
            104729, (start + gen.EXAMPLES_NEEDED) % period, difficulty="medium"
        )
        query = {"input": query_grid, "output": gen.rule_mirror(query_grid)}
        assert gen.lesson_identifiable(demos, query) == [], start


def test_exact_override_observation_boundaries_and_unknown_rejection(gen):
    cases = [
        {"grid_h": 8, "grid_w": 8, "template": "canonical_down_t", "n_anchors": 1},
        {"grid_h": 18, "grid_w": 18, "template": "scatter_long_b", "n_anchors": 5},
        {"grid_h": 9, "grid_w": 17, "template": "canonical_right_hook", "n_anchors": 3},
        {"grid_h": 17, "grid_w": 9, "template": "scatter_long_a", "n_anchors": 4},
    ]
    for index, overrides in enumerate(cases):
        captured = []
        generator_base.set_ctx_observer(captured.append)
        try:
            grid = gen.generate(700 + index, 20 + index, difficulty="hard", **overrides)
        finally:
            generator_base.set_ctx_observer(None)
        assert gen.self_check(grid) == []
        assert gen.observe_overrides(grid) == overrides
        assert captured[0].recorded_draws() == overrides
        assert captured[0].overrides_used() == overrides
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(1, 1, nonexistent_axis=1)


def test_self_check_rejects_targeted_impostors(gen):
    base = gen.generate(13, 1)
    facts = gen._grid_facts(base)

    extra_nine = copy.deepcopy(base)
    for r, row in enumerate(extra_nine):
        for c, value in enumerate(row):
            if value == 0:
                extra_nine[r][c] = 9
                break
        else:
            continue
        break
    assert any("exactly one" in reason and "9" in reason for reason in gen.self_check(extra_nine))

    missing_anchors = [[0 if value == 2 else value for value in row] for row in base]
    assert any("1-5" in reason and "anchor" in reason for reason in gen.self_check(missing_anchors))

    unknown_template = copy.deepcopy(base)
    r4, c4 = facts["fours"][0]
    unknown_template[r4][c4] = 0
    assert any("declared template" in reason for reason in gen.self_check(unknown_template))

    bad_color = copy.deepcopy(base)
    for r, row in enumerate(bad_color):
        for c, value in enumerate(row):
            if value == 0:
                bad_color[r][c] = 7
                break
        else:
            continue
        break
    assert any("only colors" in reason for reason in gen.self_check(bad_color))

    too_small = [row[:7] for row in base[:7]]
    assert any("8..18" in reason for reason in gen.self_check(too_small))


def test_negative_recombination_is_lawful_but_not_canonical(gen):
    grid = gen.generate(
        23,
        17,
        grid_h=12,
        grid_w=13,
        template="canonical_down_t",
        n_anchors=5,
    )
    assert gen.self_check(grid) == []
    assert gen.strict_canonical_like(grid)
    assert gen.canonical_profile_signature(grid) is None
    output = gen.rule_mirror(grid)
    assert len(output) == 12 and len(output[0]) == 13


def test_teaching_profile_refutes_clipping_overlap_and_anchor_priority_shortcuts(gen):
    seed = 31
    sample_index = (1 - (seed ^ (seed >> 3))) % len(gen.SCHEDULE_PROFILES)
    grid = gen.generate(seed, sample_index, difficulty="medium")
    obs = gen.semantic_observables(grid)
    assert obs["clipped_offsets"] > 0
    assert obs["overlap_cells"] > 0
    assert obs["anchor_collision_cells"] > 0
    assert obs["has_anchor_above_or_left"]
    assert obs["has_long_range_offset"]
    assert obs["template_components_4"] > 1
    for name in (
        "drop_entire_clipped_copy",
        "xor_overlapping_copies",
        "yellow_overwrites_red_anchor",
        "only_below_right_destinations",
        "local_radius_2_offsets_only",
        "nearest_template_component_only",
    ):
        assert gen.rule_mirror(grid) != gen.SEMANTIC_RIVALS[name](grid), name


def test_rule_mirror_preserves_red_anchors_after_clipped_union_stamping(gen):
    seed = 37
    sample_index = (3 - (seed ^ (seed >> 3))) % len(gen.SCHEDULE_PROFILES)
    grid = gen.generate(seed, sample_index, difficulty="hard")
    before = copy.deepcopy(grid)
    facts = gen._grid_facts(grid)
    output = gen.rule_mirror(grid)
    assert grid == before
    assert any(facts["clipped_by_anchor"])
    assert facts["anchor_collision_cells"]
    assert all(output[r][c] == 2 for r, c in facts["anchors"])


def test_determinism_fresh_returns_and_global_rng_purity(gen):
    py_state = random.getstate()
    first = gen.generate(99991, 6, difficulty="hard")
    second = gen.generate(99991, 6, difficulty="hard")
    assert first == second
    assert first is not second and all(a is not b for a, b in zip(first, second))
    old = second[0][0]
    first[0][0] = 9 if old != 9 else 0
    assert second[0][0] == old
    assert random.getstate() == py_state


def test_fixed_sample_index_does_not_collapse_seed_diversity(gen):
    grids = [gen.generate(seed, 0, difficulty="medium") for seed in range(40)]
    fingerprints = {tuple(tuple(row) for row in grid) for grid in grids}
    assert len(fingerprints) >= 20


def test_boundary_clipping_witness_requires_an_output_distinguishing_copy(gen):
    # Semantic-gate regression from the final-source battery.  This scene has
    # a clipped stamp, but every surviving cell from that stamp is reproduced
    # by another anchor, so the "drop the entire clipped copy" rival agrees.
    grid = [
        [int(value) for value in row]
        for row in (
            "0000000000000/0000000000000/0000000000000/0000000400000/"
            "0000000000000/0000040000000/0000000940000/0002000000400/"
            "0020004000000/0000000004000/2000000000000/0002000000000"
        ).split("/")
    ]
    assert gen.self_check(grid) == []
    assert gen._has_clipping(grid)
    assert (
        gen.rule_mirror(grid)
        == gen.SEMANTIC_RIVALS["drop_entire_clipped_copy"](grid)
    )
    assert not gen.SEMANTIC_WITNESSES["per_cell_boundary_clipping"](grid)
