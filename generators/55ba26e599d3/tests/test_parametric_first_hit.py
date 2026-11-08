"""Behavioral contract for the opt-in first-blue-component family."""
from __future__ import annotations

import copy
import importlib.util
import json
import random
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes

HOME = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def adapter():
    path = HOME / "workspace/parametric/adapter.py"
    assert path.is_file(), "Native first-hit parametric adapter has not been built"
    spec = importlib.util.spec_from_file_location("first_hit_test_adapter", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def grid(*rows):
    return [[int(v) for v in row] for row in rows]


def test_default_is_exact_canonical_source(adapter):
    root = find_root(__file__)
    programs = set()
    for line in canonical_path(root).read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == "55ba26e599d3":
            programs.add(row["program_solution"])
    assert programs == {adapter.program({"reach": "line_only"})}


def test_literal_first_hit_component_and_unchanged_input(adapter):
    inp = grid("20001", "01100", "00001", "00011", "00002")
    snapshot = copy.deepcopy(inp)
    canonical = grid("20001", "03100", "00201", "00031", "00002")
    first_hit = grid("20001", "03300", "00201", "00031", "00002")
    assert adapter.solve_python(inp, "line_only") == canonical
    assert adapter.solve_python(inp, "first_blue_component") == first_hit
    assert inp == snapshot


def test_component_uses_four_neighbors_and_original_input(adapter):
    # (1,2) attaches to first hit; (2,3) only touches it diagonally.
    inp = grid("20000", "01100", "00010", "00011", "00002")
    expected = grid("20000", "03300", "00210", "00031", "00002")
    assert adapter.solve_python(inp, "first_blue_component") == expected


def test_float_interpolation_order_matches_authority(adapter):
    # Hand-calculated canonical t=(15.0/22.0) gives r=7 at this half step.
    inp = [[0] * 23 for _ in range(12)]
    inp[0][0] = inp[11][22] = 2
    inp[2][4] = 1
    result = adapter.solve_python(inp, "line_only")
    assert result[7][15] == 2
    assert result[8][15] == 0


@pytest.mark.parametrize("reach", ["line_only", "first_blue_component"])
@pytest.mark.parametrize("demos", [2, 3, 6])
def test_independent_counts_distinct_inputs_and_prefix(adapter, reach, demos):
    setting = {"reach": reach}
    full = adapter.generate(17, setting, demos, 4)
    short = adapter.generate(17, setting, demos, 1)
    assert len(full["train"]) == demos
    assert len(full["test"]) == 4
    assert full["program_solution"] == adapter.program(setting)
    assert full["train"] == short["train"]
    assert full["test"][:1] == short["test"]
    inputs = [p["input"] for split in ("train", "test") for p in full[split]]
    assert len({json.dumps(g) for g in inputs}) == demos + 4
    for inp in inputs:
        assert 5 <= len(inp) <= 30 and 5 <= len(inp[0]) <= 30
        assert all(type(v) is int and v in (0, 1, 2) for row in inp for v in row)
        assert sum(v == 2 for row in inp for v in row) == 2
    first_turn = {"train": full["train"], "test": full["test"][:1]}
    assert public_challenge_bytes(first_turn) == public_challenge_bytes(short)


def test_matched_inputs_across_settings_and_real_maximum_canvas(adapter):
    first = adapter.generate(101, {"reach": "line_only"}, 3, 4)
    second = adapter.generate(101, {"reach": "first_blue_component"}, 3, 4)
    for split in ("train", "test"):
        assert [p["input"] for p in first[split]] == [p["input"] for p in second[split]]
    assert first["train"][0]["output"] != second["train"][0]["output"]
    large = next(p["input"] for p in second["test"] if len(p["input"]) == len(p["input"][0]) == 30)
    assert sum(v == 1 for row in large for v in row) >= 60
    for r0, c0 in ((0, 0), (0, 15), (15, 0), (15, 15)):
        assert any(large[r][c] == 1 for r in range(r0, r0 + 15) for c in range(c0, c0 + 15))


def test_demo_count_does_not_change_queries_and_no_global_rng_side_effect(adapter):
    state = random.getstate()
    small = adapter.generate(29, {"reach": "first_blue_component"}, 2, 4)
    full = adapter.generate(29, {"reach": "first_blue_component"}, 6, 4)
    assert random.getstate() == state
    assert full["train"][:2] == small["train"]
    assert full["test"] == small["test"]
    saved = copy.deepcopy(full)
    full["test"][0]["input"][0][0] = 9
    assert adapter.generate(29, {"reach": "first_blue_component"}, 6, 4) == saved


def test_no_blue_hit_keeps_off_path_blues_and_still_draws_line(adapter):
    inp = grid("20001", "00000", "00000", "00000", "00002")
    expected = grid("20001", "02000", "00200", "00020", "00002")
    assert adapter.solve_python(inp, "first_blue_component") == expected


def extended_segment_rival(inp, reach):
    """Independent plausible rival: continue the endpoint-defined line to edges."""
    h, w = len(inp), len(inp[0])
    (r1, c1), (r2, c2) = [(r, c) for r, row in enumerate(inp)
                          for c, value in enumerate(row) if value == 2]
    dr, dc = r2 - r1, c2 - c1
    steps = max(abs(dr), abs(dc))
    extended = [(round(r1 + (i / steps) * dr), round(c1 + (i / steps) * dc))
                for i in range(-steps, 2 * steps + 1)]
    extended = [(r, c) for r, c in extended if 0 <= r < h and 0 <= c < w]
    result = copy.deepcopy(inp)
    for r, c in extended:
        result[r][c] = {0: 2, 1: 3, 2: 2}[inp[r][c]]
    hit = next(((r, c) for r, c in extended if inp[r][c] == 1), None)
    if reach == "first_blue_component" and hit is not None:
        pending, visited = [hit], {hit}
        while pending:
            r, c = pending.pop()
            result[r][c] = 3
            for nr, nc in ((r-1, c), (r+1, c), (r, c-1), (r, c+1)):
                if 0 <= nr < h and 0 <= nc < w and inp[nr][nc] == 1 and (nr, nc) not in visited:
                    visited.add((nr, nc))
                    pending.append((nr, nc))
    return result


@pytest.mark.parametrize("reach", ["line_only", "first_blue_component"])
def test_minimum_demos_reject_extending_line_past_endpoints(adapter, reach):
    episode = adapter.generate(17, {"reach": reach}, 2, 4)
    assert any(extended_segment_rival(pair["input"], reach) != pair["output"]
               for pair in episode["train"]), "All demos allow the wrong boundary-to-boundary line"


def test_private_changes_cannot_change_visible_bytes_or_first_turn(adapter):
    episode = adapter.generate(19, {"reach": "first_blue_component"}, 3, 4)
    original = public_challenge_bytes(episode)
    changed = copy.deepcopy(episode)
    changed.update(seed=999, settings={"reach": "unrelated"}, program_solution="private replacement")
    for pair in changed["test"]:
        pair["output"] = [[9]]
    assert public_challenge_bytes(changed) == original
    first_turn = {"train": episode["train"], "test": episode["test"][:1]}
    first_bytes = public_challenge_bytes(first_turn)
    changed["test"][1]["input"] = [[8]]
    assert public_challenge_bytes({"train": changed["train"], "test": changed["test"][:1]}) == first_bytes


@pytest.mark.parametrize("args", [
    (True, {"reach": "line_only"}, 3, 4),
    (-1, {"reach": "line_only"}, 3, 4),
    (2**63, {"reach": "line_only"}, 3, 4),
    (0, {"reach": "line_only"}, True, 4),
    (0, {"reach": "line_only"}, 1, 4),
    (0, {"reach": "line_only"}, 7, 4),
    (0, {"reach": "line_only"}, 3, 0),
    (0, {"reach": "line_only"}, 3, 5),
    (0, {}, 3, 4),
    (0, {"reach": "last"}, 3, 4),
    (0, {"reach": "line_only", "extra": 1}, 3, 4),
])
def test_invalid_requests_are_rejected(adapter, args):
    with pytest.raises(ValueError):
        adapter.generate(*args)

