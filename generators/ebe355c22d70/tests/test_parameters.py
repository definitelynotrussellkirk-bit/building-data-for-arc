"""Behavioral tests for the native bbox-relay parametric family."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest


HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
CANONICAL = "(rule! (let ((dummy 0)) (define (nonzero-points grid) (sort (map (lambda (cell) (list (first cell) (second cell))) (filter (lambda (cell) (not (= (third cell) 0))) (grid-cells grid))) cell<)) (define pts (nonzero-points g)) (define r0 (apply min (map first pts))) (define r1 (apply max (map first pts))) (define c0 (apply min (map second pts))) (define c1 (apply max (map second pts))) (empty-grid (+ 1 (- r1 r0)) (+ 1 (- c1 c0)) 8)))"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


adapter = _load("ebe355c22d70_parametric_adapter_test", PARAMETRIC / "adapter.py")
prototype = _load("ebe355c22d70_parametric_prototype_test", PARAMETRIC / "prototype.py")


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _grid_ok(grid):
    return (
        type(grid) is list
        and 1 <= len(grid) <= 30
        and type(grid[0]) is list
        and 1 <= len(grid[0]) <= 30
        and all(
            type(row) is list
            and len(row) == len(grid[0])
            and all(type(cell) is int and 0 <= cell <= 9 for cell in row)
            for row in grid
        )
    )


def _bbox_nonzero(grid):
    cells = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value != 0
    ]
    assert cells
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _components(grid):
    """Independent same-color four-neighbor components, excluding 0 and 1."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color in (0, 1) or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if (
                        0 <= nr < h
                        and 0 <= nc < w
                        and (nr, nc) not in seen
                        and grid[nr][nc] == color
                    ):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            result.append((color, sorted(cells)))
    return result


def _normalized_mask(cells):
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    occupied = set(cells)
    return [
        [8 if (r, c) in occupied else 0 for c in range(c0, c1 + 1)]
        for r in range(r0, r1 + 1)
    ]


def _independent_outputs(grid):
    r0, c0, r1, c1 = _bbox_nonzero(grid)
    outer = [[8] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    short_side = min(r1 - r0 + 1, c1 - c0 + 1)
    matches = [cells for _, cells in _components(grid) if len(cells) == short_side]
    assert len(matches) == 1
    return outer, _normalized_mask(matches[0])


def test_default_program_preserves_canonical_bytes_and_alternate_is_distinct():
    assert adapter.program({"mode": "outer_fill"}) == CANONICAL
    alternate = adapter.program({"mode": "short_side_relay"})
    assert alternate != CANONICAL
    assert alternate.startswith("(rule!")


@pytest.mark.parametrize("demos", range(2, 7))
def test_supported_counts_are_distinct_and_inputs_are_matched_across_settings(demos):
    episodes = {
        mode: prototype.generate(17, {"mode": mode}, demos=demos, queries=4)
        for mode in ("outer_fill", "short_side_relay")
    }
    for episode in episodes.values():
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        pairs = episode["train"] + episode["test"]
        assert all(_grid_ok(pair["input"]) and _grid_ok(pair["output"]) for pair in pairs)
        assert len({_freeze(pair["input"]) for pair in pairs}) == len(pairs)
    assert [pair["input"] for pair in episodes["outer_fill"]["train"] + episodes["outer_fill"]["test"]] == [
        pair["input"]
        for pair in episodes["short_side_relay"]["train"] + episodes["short_side_relay"]["test"]
    ]


def test_labels_follow_outer_bbox_and_short_side_component_independently():
    canonical = prototype.generate(0, {"mode": "outer_fill"}, demos=3, queries=4)
    relay = prototype.generate(0, {"mode": "short_side_relay"}, demos=3, queries=4)
    for canonical_pair, relay_pair in zip(
        canonical["train"] + canonical["test"], relay["train"] + relay["test"]
    ):
        assert canonical_pair["input"] == relay_pair["input"]
        outer, selected = _independent_outputs(canonical_pair["input"])
        assert canonical_pair["output"] == outer
        assert relay_pair["output"] == selected
        assert outer != selected


@pytest.mark.parametrize("seed", [0, 17, 41])
@pytest.mark.parametrize("mode", ["outer_fill", "short_side_relay"])
def test_two_demonstrations_identify_the_setting_and_refute_named_shortcuts(seed, mode):
    episode = prototype.generate(seed, {"mode": mode}, demos=2, queries=4)
    certificate = prototype.certify(episode)
    assert certificate["survivors"] == [{"mode": mode}]
    assert certificate["extra_refutations"]
    assert all(indices for indices in certificate["extra_refutations"].values())
    assert len(certificate["queries"]) == 4


def test_queries_include_a_substantive_30_by_30_stress_scene():
    episode = prototype.generate(17, {"mode": "short_side_relay"}, demos=3, queries=4)
    grid = episode["test"][3]["input"]
    output = episode["test"][3]["output"]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert sum(value != 0 for row in grid for value in row) >= 70
    assert len(_components(grid)) >= 6
    assert len(output) >= 2 and len(output[0]) >= 2
    r0, c0, r1, c1 = _bbox_nonzero(grid)
    assert r1 - r0 + 1 >= 27 and c1 - c0 + 1 >= 27
    assert (r0 == 0 or r1 == 29) and (c0 == 0 or c1 == 29)


def test_public_turn_reveals_one_query_without_private_fields_or_future_inputs():
    episode = prototype.generate(9, {"mode": "short_side_relay"}, demos=3, queries=4)
    first = prototype.public_turn(episode, 0)
    second = prototype.public_turn(episode, 1)
    assert set(first) == {"train", "test"}
    assert len(first["test"]) == 1
    assert set(first["test"][0]) == {"input"}
    assert first["test"][0]["input"] == episode["test"][0]["input"]
    assert second["test"][0]["input"] == episode["test"][1]["input"]
    assert first != second
    visible = json.dumps(first, sort_keys=True)
    for forbidden in ("short_side_relay", "program_solution", "settings", "output_sha256"):
        assert forbidden not in visible
    leaked = copy.deepcopy(first)
    leaked["test"].append({"input": episode["test"][1]["input"]})
    assert leaked != first


@pytest.mark.parametrize(
    "args",
    [
        (-1, {"mode": "outer_fill"}, 3, 4),
        (0, {}, 3, 4),
        (0, {"mode": "unknown"}, 3, 4),
        (0, {"mode": "outer_fill", "extra": 1}, 3, 4),
        (0, {"mode": "outer_fill"}, 1, 4),
        (0, {"mode": "outer_fill"}, 7, 4),
        (0, {"mode": "outer_fill"}, True, 4),
        (0, {"mode": "outer_fill"}, 3, 3),
        (0, {"mode": "outer_fill"}, 3, 5),
    ],
)
def test_invalid_requests_are_rejected(args):
    with pytest.raises(ValueError):
        prototype.generate(*args)


def test_wrong_long_side_intermediate_changes_a_relay_query_answer():
    episode = prototype.generate(17, {"mode": "short_side_relay"}, demos=3, queries=4)
    differences = []
    for pair in episode["test"]:
        counterfactual = prototype.RIVAL_TRANSFORMS["long_side_component"](pair["input"])
        differences.append(counterfactual != pair["output"])
    assert any(differences)


def test_stress_audit_sweeps_supported_counts_and_matched_inputs(tmp_path):
    audit = _load("ebe355c22d70_parametric_audit_test", PARAMETRIC / "audit.py")
    report = audit.stress(seed_count=3)
    assert report["schema"] == "ebe355c22d70-bbox-relay-stress-v1"
    assert report["seed_count"] == 3
    assert report["episodes"] == 30
    assert report["visible_pairs"] == 240
    assert report["matched_input_checks"] == 15
    assert report["failures"] == []
    assert report["modes"] == ["outer_fill", "short_side_relay"]
    assert report["demo_counts"] == [2, 3, 4, 5, 6]
    destination = tmp_path / "stress.json"
    audit.write_report(report, destination)
    assert json.loads(destination.read_text()) == report


def test_sampler_recovers_from_seed_eight_greedy_placement_dead_end():
    for mode in ("outer_fill", "short_side_relay"):
        episode = prototype.generate(8, {"mode": mode}, demos=6, queries=4)
        assert len(episode["train"]) == 6
        assert len(episode["test"]) == 4
