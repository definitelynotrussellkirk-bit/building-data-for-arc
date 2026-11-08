"""Portable regressions and curriculum checks for generator 928c39acebe3."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import os
from pathlib import Path
import random
import sys

import pytest

# Portable bootstrap for both the library checkout and staged task-test runtime.
for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import canonical_pairs, find_root  # noqa: E402

TASK_ID = "928c39acebe3"
ROOT = find_root(__file__)
DEFAULT_GENERATOR = ROOT / "generators" / TASK_ID / "generator.py"
if not DEFAULT_GENERATOR.is_file():
    DEFAULT_GENERATOR = ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py"
GENERATOR_PATH = Path(os.environ.get("GENERATOR_UNDER_TEST", DEFAULT_GENERATOR))
SPEC = importlib.util.spec_from_file_location(f"review_{TASK_ID}", GENERATOR_PATH)
assert SPEC is not None and SPEC.loader is not None
GEN = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = GEN
SPEC.loader.exec_module(GEN)

PROBE_SPEC = importlib.util.spec_from_file_location(
    f"reference_probe_{TASK_ID}", GENERATOR_PATH.parent / "workspace" / "reference_probe.py"
)
assert PROBE_SPEC is not None and PROBE_SPEC.loader is not None
PROBE = importlib.util.module_from_spec(PROBE_SPEC)
sys.modules[PROBE_SPEC.name] = PROBE
PROBE_SPEC.loader.exec_module(PROBE)

BANDS = (None, "easy", "medium", "hard")


def _canonical_pairs():
    return canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _pair(seed: int, sample_index: int, difficulty: str | None) -> dict:
    grid = GEN.generate(seed, sample_index, difficulty=difficulty)
    return {"input": grid, "output": GEN.rule_mirror(grid)}


def _accepts(result) -> bool:
    return result is True or result == []


def test_rule_pin_and_independent_oracle_match_every_canonical_pair():
    assert GEN.RULE_HASH == "5e6d34fb1a87"
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        before = deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert _accepts(GEN.strict_canonical_like(pair["input"]))
        assert PROBE.official_output(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_single_exact_profile_axis_replaces_retired_pseudo_controls():
    assert set(GEN.AXES) == {"scene_profile"}
    assert tuple(GEN.HELPFUL_TEXTURES) == ()
    assert tuple(GEN.DEGENERATE_TEXTURES) == ()
    assert set(GEN.SCENE_PROFILES) == set(GEN.SCHEDULE_PROFILES)
    for retired in (
        "grid_h", "grid_w", "palette_kind", "palette_size", "position_bias",
        "n_distinct_colors", "density", "n_emitters", "n_mirrors",
        "n_blockers", "texture",
    ):
        with pytest.raises(ValueError, match="unknown override"):
            GEN.generate(0, 0, **{retired: 1})


@pytest.mark.parametrize("band", BANDS)
def test_every_profile_override_is_exact_observable_lawful_and_deterministic(band):
    for profile_name in GEN.SCENE_PROFILES:
        for seed in (0, 1, 17, 991):
            first = GEN.generate(seed, 7, difficulty=band, scene_profile=profile_name)
            second = GEN.generate(seed, 7, difficulty=band, scene_profile=profile_name)
            assert first == second
            assert first is not second
            assert all(left is not right for left, right in zip(first, second))
            assert GEN.observe_overrides(first) == {"scene_profile": profile_name}
            assert GEN.self_check(first, meta={"overrides": {"scene_profile": profile_name}}) == []
            assert GEN.rule_mirror(first) == PROBE.official_output(first)


def test_invalid_seed_index_difficulty_and_profile_requests_fail_loudly():
    for seed in (True, 1.5, "1"):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(seed, 0)
    for sample_index in (True, -1, 1.5, "1"):
        with pytest.raises((TypeError, ValueError)):
            GEN.generate(0, sample_index)
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(0, 0, difficulty="expert")
    with pytest.raises(ValueError, match="unknown scene_profile"):
        GEN.generate(0, 0, scene_profile="not-a-profile")
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, imaginary_axis="x")


def test_schedule_covers_all_linked_canonical_profiles_and_direction_probes_per_band():
    canonical_profiles = {
        (8, 12, (5, 4, 5)),
        (9, 13, (5, 5, 4)),
        (8, 14, (5, 4, 5, 4)),
        (9, 14, (5, 5, 4, 4)),
    }
    for band in ("easy", "medium", "hard"):
        scheduled = [GEN.schedule_profile(123, index, band) for index in range(GEN.SCHEDULE_PERIOD)]
        assert scheduled == list(GEN.DEFAULT_SCHEDULE)
        grids = [GEN.generate(123, index, difficulty=band) for index in range(GEN.SCHEDULE_PERIOD)]
        observed = {PROBE.profile(grid) for grid in grids}
        assert canonical_profiles <= observed
        probe_grids = [grid for grid in grids if "full_direction_probe" in GEN.observe_overrides(grid)["scene_profile"]]
        assert len(probe_grids) >= 2
        for grid in probe_grids:
            incoming = PROBE.incoming_pairs(grid)
            assert (4, "west") in incoming
            assert (5, "north") in incoming
        assert sum(_accepts(GEN.strict_canonical_like(grid)) for grid in grids) == 4


def test_source_bound_direction_shortcuts_fit_all_canonical_pairs_but_not_probes():
    pairs = _canonical_pairs()
    expected_names = {
        "slash_from_west_continues_straight",
        "backslash_from_north_continues_straight",
    }
    assert expected_names <= set(GEN.CANONICAL_SHORTCUTS)
    for name in expected_names:
        shortcut = GEN.CANONICAL_SHORTCUTS[name]
        assert all(shortcut(pair["input"]) == pair["output"] for pair in pairs), name
    for profile_name in ("full_direction_probe_compact", "full_direction_probe_wide"):
        grid = GEN.generate(91, 0, scene_profile=profile_name)
        truth = GEN.rule_mirror(grid)
        assert PROBE.slash_from_west_continues(grid) != truth
        assert PROBE.backslash_from_north_continues(grid) != truth
        assert GEN.CANONICAL_SHORTCUTS["slash_from_west_continues_straight"](grid) != truth
        assert GEN.CANONICAL_SHORTCUTS["backslash_from_north_continues_straight"](grid) != truth


def test_every_four_pair_schedule_window_is_identifiable_under_every_query_rotation():
    for band_index, band in enumerate(("easy", "medium", "hard")):
        for seed in range(8):
            for start in range(GEN.SCHEDULE_PERIOD):
                pairs = [_pair(7000 + band_index * 100 + seed, start + offset, band) for offset in range(4)]
                for query_index, query in enumerate(pairs):
                    demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                    assert GEN.lesson_identifiable(demos, query) == [], (
                        band, seed, start, query_index,
                    )


def test_declared_witnesses_really_refute_their_named_rivals():
    hits = {name: 0 for name in GEN.SEMANTIC_WITNESSES}
    for band in ("easy", "medium", "hard"):
        for seed in range(12):
            for index in range(GEN.SCHEDULE_PERIOD):
                grid = GEN.generate(seed, index, difficulty=band)
                truth = GEN.rule_mirror(grid)
                for witness_name, predicate in GEN.SEMANTIC_WITNESSES.items():
                    if not predicate(grid):
                        continue
                    hits[witness_name] += 1
                    assert any(
                        GEN.SEMANTIC_RIVALS[rival_name](grid) != truth
                        for rival_name in GEN.WITNESS_RIVALS[witness_name]
                    ), witness_name
    assert all(count > 0 for count in hits.values())


def test_self_check_rejects_structural_mutations_and_missed_semantics():
    grid = GEN.generate(81, 1, difficulty="medium")
    assert GEN.self_check(grid) == []

    mutations = []
    ragged = deepcopy(grid); ragged[-1].pop(); mutations.append(ragged)
    illegal = deepcopy(grid); illegal[0][0] = 9; mutations.append(illegal)
    no_source = deepcopy(grid)
    source = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2)
    no_source[source[0]][source[1]] = 0; mutations.append(no_source)
    no_blocker = deepcopy(grid)
    blocker = next((r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 6)
    no_blocker[blocker[0]][blocker[1]] = 0; mutations.append(no_blocker)
    missed_mirror = deepcopy(grid)
    details = PROBE.trace_details(grid)
    mr, mc, _color, _dr, _dc = details["hits"][0]
    missed_mirror[mr][mc] = 0; mutations.append(missed_mirror)

    for mutation in mutations:
        errors = GEN.self_check(mutation)
        assert isinstance(errors, list) and errors
        assert all(isinstance(error, str) and error for error in errors)


def test_generation_is_fresh_and_does_not_touch_process_global_rng():
    random.seed(2468)
    before = random.getstate()
    first = GEN.generate(91, 3, difficulty="hard")
    after = random.getstate()
    second = GEN.generate(91, 3, difficulty="hard")
    assert before == after
    assert first == second
    assert first is not second
    first[0][0] = 8 if first[0][0] != 8 else 7
    assert first != second


def test_axes_metadata_is_a_static_literal_for_repository_lint():
    import ast

    tree = ast.parse(GENERATOR_PATH.read_text(encoding="utf-8"))
    axes_node = next(
        node.value
        for node in tree.body
        if isinstance(node, ast.Assign)
        and any(isinstance(target, ast.Name) and target.id == "AXES" for target in node.targets)
    )
    axes = ast.literal_eval(axes_node)
    assert axes == GEN.AXES


def test_difficulty_band_changes_layout_without_changing_semantic_profile():
    for index in range(GEN.SCHEDULE_PERIOD):
        grids = {
            band: GEN.generate(31337, index, difficulty=band)
            for band in ("easy", "medium", "hard")
        }
        assert {
            GEN.observe_overrides(grid)["scene_profile"] for grid in grids.values()
        } == {GEN.schedule_profile(31337, index, "medium")}
        assert len({repr(grid) for grid in grids.values()}) >= 2


def test_retained_partial_lookup_counterexample_replays_and_refutes_combined_shortcut():
    import json

    fixture_path = GENERATOR_PATH.parent / "counterexamples" / "unseen_direction_lookup.json"
    fixture = json.loads(fixture_path.read_text(encoding="utf-8"))
    args = fixture["generator_args"]
    replay = GEN.generate(
        args["seed"],
        args["sample_index"],
        difficulty=args["difficulty"],
        **args["overrides"],
    )
    assert replay == fixture["input"]
    truth = GEN.rule_mirror(replay)
    assert truth == fixture["racket_output"]
    shortcut = GEN.CANONICAL_SHORTCUTS["unseen_directions_continue_straight"]
    assert all(shortcut(pair["input"]) == pair["output"] for pair in _canonical_pairs())
    prediction = shortcut(replay)
    assert prediction == fixture["shortcut_output"]
    assert prediction != truth
    assert PROBE.differs_at(prediction, truth) == [tuple(row) for row in fixture["differences"]]
