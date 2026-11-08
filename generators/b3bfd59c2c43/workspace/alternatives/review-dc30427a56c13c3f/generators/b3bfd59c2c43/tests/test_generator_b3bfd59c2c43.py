"""Task-local regressions for the outermost-layer recolor sampler."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
from collections import deque
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
REPO = Path(__file__).resolve().parents[3]
SOURCE = Path(os.environ.get("GENERATOR_UNDER_TEST", HOME / "generator.py"))
SPEC = importlib.util.spec_from_file_location("generator_under_test_b3bfd59c2c43", SOURCE)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)

TASK_ID = "b3bfd59c2c43"
CANONICAL_PROFILES = {"11x15": (11, 15), "12x12": (12, 12), "13x15": (13, 15)}
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def canonical_pairs():
    path = REPO / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            pairs = list(row.get("train") or [])
            test = row.get("test")
            if isinstance(test, dict):
                pairs.append(test)
            elif isinstance(test, list):
                pairs.extend(test)
            return pairs
    raise AssertionError(f"missing canonical task {TASK_ID}")


def components(grid, *, per_color=False):
    h, w = len(grid), len(grid[0])
    unseen = {
        (r, c)
        for r in range(h)
        for c in range(w)
        if grid[r][c] not in (0, 9)
    }
    found = []
    while unseen:
        start = min(unseen)
        color = grid[start[0]][start[1]]
        queue = deque([start])
        unseen.remove(start)
        comp = {start}
        while queue:
            r, c = queue.popleft()
            for dr, dc in CARDINAL:
                point = (r + dr, c + dc)
                if point not in unseen:
                    continue
                if per_color and grid[point[0]][point[1]] != color:
                    continue
                unseen.remove(point)
                comp.add(point)
                queue.append(point)
        found.append(comp)
    return found


def outermost_layer(grid):
    """Independent Python mirror of the selected Racket rule."""
    out = [list(row) for row in grid]
    h, w = len(grid), len(grid[0])
    for comp in components(grid):
        for r, c in comp:
            if any(
                not (0 <= r + dr < h and 0 <= c + dc < w)
                or (r + dr, c + dc) not in comp
                for dr, dc in CARDINAL
            ):
                out[r][c] = 8
    return out


def profile(grid):
    colors = {value for row in grid for value in row}
    return len(grid), len(grid[0]), len(colors)


def test_rule_pin_and_minimal_exact_axis_contract():
    assert GEN.GENERATOR_ID == TASK_ID
    assert GEN.TASK_ID == TASK_ID
    assert GEN.RULE_HASH == "28b8cf49f820"
    assert GEN.VERSION == "2.0.0"
    assert set(GEN.AXES) == {"canvas_profile"}
    assert GEN.AXES["canvas_profile"]["valid"] == "11x15|12x12|13x15"
    assert GEN.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


def test_canonical_inputs_are_owned_and_oracle_matches_all_outputs():
    pairs = canonical_pairs()
    assert len(pairs) == 3
    assert {profile(pair["input"]) for pair in pairs} == {
        (11, 15, 3), (12, 12, 3), (13, 15, 3)
    }
    for pair in pairs:
        assert GEN.self_check(copy.deepcopy(pair["input"])) == []
        assert outermost_layer(pair["input"]) == pair["output"]
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


@pytest.mark.parametrize("band", [None, "easy", "medium", "hard"])
@pytest.mark.parametrize("name,dims", CANONICAL_PROFILES.items())
def test_canvas_profile_is_exact_observable_override(name, dims, band):
    grid = GEN.generate(17, 5, difficulty=band, canvas_profile=name)
    assert (len(grid), len(grid[0])) == dims
    assert profile(grid) == (*dims, 3)
    assert GEN.observe_overrides(grid) == {"canvas_profile": name}
    assert GEN.self_check(grid, difficulty=band) == []


def test_unknown_invalid_overrides_and_difficulty_are_loud():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(0, 0, typo_axis="11x15")
    with pytest.raises(ValueError):
        GEN.generate(0, 0, canvas_profile="14x14")
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(0, 0, difficulty="nightmare")


def test_schedule_profiles_are_constructive_deterministic_and_witnessed():
    assert tuple(GEN.SCHEDULE_PROFILES) == ("canonical", "edge", "multicolor")
    assert GEN.EXAMPLES_NEEDED == len(GEN.SCHEDULE_PROFILES) == 3
    seen = set()
    unique = set()
    for band in ("easy", "medium", "hard"):
        for sample_index in range(96):
            expected = GEN.SCHEDULE_PROFILES[sample_index % 3]
            assert GEN.schedule_profile(7123, sample_index, difficulty=band) == expected
            grid = GEN.generate(7123, sample_index, difficulty=band)
            assert GEN.generate(7123, sample_index, difficulty=band) == grid
            assert GEN.self_check(grid, difficulty=band) == []
            assert profile(grid) in {(11, 15, 3), (12, 12, 3), (13, 15, 3)}
            assert len(components(grid)) == 2
            assert any(
                all(
                    0 <= r + dr < len(grid)
                    and 0 <= c + dc < len(grid[0])
                    and (r + dr, c + dc) in comp
                    for dr, dc in CARDINAL
                )
                for comp in components(grid)
                for r, c in comp
            )
            if expected == "edge":
                assert GEN.SEMANTIC_WITNESSES["edge_exposure"](grid)
            if expected == "multicolor":
                assert GEN.SEMANTIC_WITNESSES["multicolor_component"](grid)
            seen.add(expected)
            unique.add(tuple(tuple(row) for row in grid))
    assert seen == set(GEN.SCHEDULE_PROFILES)
    assert len(unique) >= 250


def test_declared_canonical_shortcuts_really_fit_canonical_pairs():
    assert set(GEN.CANONICAL_SHORTCUTS) == {"edge_blind", "per_color"}
    for name, rival in GEN.CANONICAL_SHORTCUTS.items():
        for pair in canonical_pairs():
            assert rival(copy.deepcopy(pair["input"])) == pair["output"], name


def test_each_semantic_witness_refutes_its_claimed_rival():
    requested = {
        "edge_exposure": (1, "edge_blind"),
        "multicolor_component": (2, "per_color"),
        "interior_core": (0, "recolor_all"),
        "multiple_components": (0, "largest_only"),
    }
    for witness, (sample_index, rival_name) in requested.items():
        grid = GEN.generate(90210, sample_index, difficulty="hard")
        intended = outermost_layer(grid)
        assert GEN.SEMANTIC_WITNESSES[witness](grid)
        assert rival_name in GEN.WITNESS_RIVALS[witness]
        assert GEN.SEMANTIC_RIVALS[rival_name](grid) != intended


def test_every_cyclic_three_demo_lesson_refutes_every_competitor():
    assert set(GEN.LESSON_COMPETITORS) == set(GEN.SEMANTIC_RIVALS)
    period = len(GEN.SCHEDULE_PROFILES)
    for band in ("easy", "medium", "hard"):
        for seed in (0, 13, 424242):
            for start in range(period):
                demos = []
                for sample_index in range(start, start + GEN.EXAMPLES_NEEDED):
                    grid = GEN.generate(seed, sample_index, difficulty=band)
                    demos.append({"input": grid, "output": outermost_layer(grid)})
                query_grid = GEN.generate(
                    seed, start + GEN.EXAMPLES_NEEDED, difficulty=band
                )
                query = {"input": query_grid, "output": outermost_layer(query_grid)}
                assert GEN.lesson_identifiable(demos, query) == []
                for name, rival in GEN.LESSON_COMPETITORS.items():
                    assert any(
                        rival(copy.deepcopy(demo["input"])) != demo["output"]
                        for demo in demos
                    ), f"{band=} {seed=} {start=} did not refute {name}"


def test_self_check_rejects_malformed_and_structural_impostors():
    malformed = [None, [], [[]], [[0], [0, 1]], [[True] * 12 for _ in range(12)]]
    for grid in malformed:
        assert GEN.self_check(grid)

    grid = GEN.generate(44, 0, canvas_profile="12x12")

    wrong_color = copy.deepcopy(grid)
    wrong_color[0][0] = 8
    assert GEN.self_check(wrong_color)

    missing_component = copy.deepcopy(grid)
    comps = components(missing_component)
    for r, c in comps[1]:
        missing_component[r][c] = 0
    assert GEN.self_check(missing_component)

    bridge = copy.deepcopy(grid)
    first, second = components(bridge)
    # The generator promises a one-cell Chebyshev moat. Fill a shortest
    # Manhattan route; the validator must reject the merged impostor.
    a = min(first)
    b = min(second)
    r, c = a
    while c != b[1]:
        c += 1 if b[1] > c else -1
        bridge[r][c] = bridge[a[0]][a[1]]
    while r != b[0]:
        r += 1 if b[0] > r else -1
        bridge[r][c] = bridge[a[0]][a[1]]
    assert GEN.self_check(bridge)


def test_rule_and_rivals_do_not_mutate_input():
    grid = GEN.generate(91, 2)
    pristine = copy.deepcopy(grid)
    assert GEN.rule_mirror(grid) == outermost_layer(grid)
    for rival in GEN.SEMANTIC_RIVALS.values():
        rival(grid)
    assert grid == pristine


def test_task_local_lesson_probe_smoke_is_source_bound():
    probe_path = HOME / "workspace" / "lesson_probe.py"
    spec = importlib.util.spec_from_file_location("lesson_probe_b3bfd59c2c43", probe_path)
    assert spec and spec.loader
    probe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(probe)
    report = probe.audit(SOURCE, lessons_per_band=3)
    assert report["generator_sha256"] == probe.sha256_file(SOURCE)
    assert report["lessons"] == 9
    assert report["invalid_grids"] == 0
    assert report["oracle_mismatches"] == 0
    assert report["ambiguous_lessons"] == 0
    assert report["competitor_survivals"] == {
        name: 0 for name in GEN.LESSON_COMPETITORS
    }
