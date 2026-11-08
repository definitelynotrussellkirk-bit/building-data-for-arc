"""Contract, teaching, privacy, and boundary tests for the size-relay family."""
from __future__ import annotations

from collections import Counter, defaultdict
from importlib.util import module_from_spec, spec_from_file_location
import json
from pathlib import Path
import sys

import pytest

for ancestor in Path(__file__).resolve().parents:
    runtime = ancestor / "shared" / "runtime"
    if (runtime / "reviewer_support.py").is_file():
        sys.path.insert(0, str(runtime))
        break
    if (ancestor / "reviewer_support.py").is_file():
        sys.path.insert(0, str(ancestor))
        break

from reviewer_support import public_challenge_bytes, public_challenge_id  # noqa: E402

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
CANONICAL = "(rule!\n  ;; alt: (crop-object g (largest-object g 0))\n  (extract-largest g 0))"
MODES = ("largest_component", "largest_size_relay")


def _load(name: str, path: Path):
    spec = spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _components(grid):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for start_r in range(height):
        for start_c in range(width):
            color = grid[start_r][start_c]
            if color == 0 or (start_r, start_c) in seen:
                continue
            stack = [(start_r, start_c)]
            seen.add((start_r, start_c))
            cells = set()
            while stack:
                row, col = stack.pop()
                cells.add((row, col))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = row + dr, col + dc
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and nxt not in seen
                        and grid[nxt[0]][nxt[1]] == color
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            result.append((color, cells))
    return result


def _crop_from_cells(grid, cells, *, mask_color=None):
    r0 = min(row for row, _ in cells)
    r1 = max(row for row, _ in cells)
    c0 = min(col for _, col in cells)
    c1 = max(col for _, col in cells)
    if mask_color is None:
        return [row[c0 : c1 + 1] for row in grid[r0 : r1 + 1]]
    return [
        [mask_color if grid[row][col] == mask_color else 0 for col in range(c0, c1 + 1)]
        for row in range(r0, r1 + 1)
    ]


def _independent_semantics(grid):
    components = _components(grid)
    sizes = [len(cells) for _, cells in components]
    largest_size = max(sizes)
    largest = [(color, cells) for color, cells in components if len(cells) == largest_size]
    assert len(largest) == 1
    source_color, source_cells = largest[0]
    counts = Counter(value for row in grid for value in row if value)
    relay_colors = [
        color
        for color, count in counts.items()
        if color != source_color and count == largest_size
    ]
    assert len(relay_colors) == 1
    relay_color = relay_colors[0]
    relay_cells = {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == relay_color
    }
    return {
        "source_color": source_color,
        "source_cells": source_cells,
        "key": largest_size,
        "relay_color": relay_color,
        "canonical": _crop_from_cells(grid, source_cells),
        "relay": _crop_from_cells(grid, relay_cells, mask_color=relay_color),
        "counts": counts,
        "components": components,
    }


def test_adapter_preserves_exact_canonical_bytes_and_validates_settings():
    adapter = _load("db89_size_relay_adapter", PARAMETRIC / "adapter.py")
    prototype = _load("db89_size_relay_prototype", PARAMETRIC / "prototype.py")

    assert (PARAMETRIC / "canonical.rkt").read_text() == CANONICAL
    assert adapter.program({"mode": "largest_component"}) == CANONICAL
    assert adapter.program({"mode": "largest_size_relay"}) == prototype.SIZE_RELAY_PROGRAM
    assert (PARAMETRIC / "wrong_intermediate_plus_one.rkt").read_text() == prototype.WRONG_INTERMEDIATE_PROGRAM

    for invalid in (
        None,
        {},
        {"mode": "unknown"},
        {"mode": "largest_component", "extra": True},
    ):
        with pytest.raises(ValueError):
            adapter.program(invalid)


@pytest.mark.parametrize("seed", [0, 17, 991])
@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("mode", MODES)
def test_episode_contract_exact_labels_and_constructive_dependency(seed, demos, mode):
    prototype = _load(
        f"db89_size_relay_{seed}_{demos}_{mode}", PARAMETRIC / "prototype.py"
    )
    episode = prototype.generate_episode(seed, mode=mode, demos=demos, queries=4)

    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    assert episode["program_solution"] == prototype.rule_text(mode)

    pairs = episode["train"] + episode["test"]
    serial = [json.dumps(pair["input"], separators=(",", ":")) for pair in pairs]
    assert len(serial) == len(set(serial))

    for pair in pairs:
        grid = pair["input"]
        assert 1 <= len(grid) <= 30
        assert 1 <= len(grid[0]) <= 30
        assert all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)

        semantics = _independent_semantics(grid)
        source_components = [
            cells
            for color, cells in semantics["components"]
            if color == semantics["source_color"]
        ]
        assert len(source_components) >= 2  # refutes whole-source-color envelope
        assert max(map(len, source_components)) == semantics["key"]
        assert semantics["counts"][semantics["relay_color"]] == semantics["key"]
        non_source_plus_one = [
            color
            for color, count in semantics["counts"].items()
            if color != semantics["source_color"] and count == semantics["key"] + 1
        ]
        assert len(non_source_plus_one) == 1
        assert all(
            len(cells) < semantics["key"]
            for color, cells in semantics["components"]
            if (color, cells) != (semantics["source_color"], semantics["source_cells"])
        )

        expected = semantics["canonical"] if mode == "largest_component" else semantics["relay"]
        assert pair["output"] == expected
        assert semantics["canonical"] != semantics["relay"]

    first_two = episode["train"][:2]
    relay_ranks = []
    relay_colors = []
    for pair in first_two:
        semantics = _independent_semantics(pair["input"])
        source = semantics["source_color"]
        ranked = sorted(
            (color for color in semantics["counts"] if color != source),
            key=lambda color: (-semantics["counts"][color], color),
        )
        relay_ranks.append(ranked.index(semantics["relay_color"]) + 1)
        relay_colors.append(semantics["relay_color"])
    assert relay_ranks == [2, 4]
    assert relay_colors[0] != relay_colors[1]

    stress_pair = episode["test"][3]
    stress = stress_pair["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    nonzero = [(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value]
    assert len(nonzero) >= 90
    assert {0, 29} <= {r for r, _ in nonzero}
    assert {0, 29} <= {c for _, c in nonzero}
    if mode == "largest_size_relay":
        assert (len(stress_pair["output"]), len(stress_pair["output"][0])) == (30, 30)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True, "mode": "largest_component", "demos": 3, "queries": 4},
        {"seed": -1, "mode": "largest_component", "demos": 3, "queries": 4},
        {"seed": 0, "mode": "unknown", "demos": 3, "queries": 4},
        {"seed": 0, "mode": "largest_component", "demos": 1, "queries": 4},
        {"seed": 0, "mode": "largest_component", "demos": 7, "queries": 4},
        {"seed": 0, "mode": "largest_component", "demos": 3, "queries": 3},
        {"seed": 0, "mode": "largest_component", "demos": 3, "queries": 5},
    ],
)
def test_episode_rejects_out_of_contract_requests(kwargs):
    prototype = _load("db89_size_relay_bad_requests", PARAMETRIC / "prototype.py")
    with pytest.raises(ValueError):
        prototype.generate_episode(**kwargs)


def test_public_turn_projection_masks_answers_and_private_fields():
    prototype = _load("db89_size_relay_public", PARAMETRIC / "prototype.py")
    episode = prototype.generate_episode(17, mode="largest_size_relay", demos=3, queries=4)
    ids = []
    for query_index, pair in enumerate(episode["test"]):
        public = {"train": episode["train"], "test": [{"input": pair["input"]}]}
        enriched = {
            **public,
            "settings": {"mode": "largest_size_relay"},
            "program_solution": episode["program_solution"],
            "private_query_answer": pair["output"],
            "future_queries": episode["test"][query_index + 1 :],
        }
        assert public_challenge_bytes(enriched) == public_challenge_bytes(public)
        body = json.loads(public_challenge_bytes(enriched))
        assert body["test"] == [{"input": pair["input"]}]
        assert "output" not in body["test"][0]
        ids.append(public_challenge_id(enriched))
    assert len(ids) == len(set(ids)) == 4


def test_bounded_self_audit_refutes_declared_shortcuts_and_has_causal_witness():
    audit = _load("db89_size_relay_audit", PARAMETRIC / "audit.py")
    report = audit.python_audit(seeds=range(8), demo_counts=range(2, 7))

    assert report["episodes"] == 80
    assert report["ambiguities"] == []
    assert report["distinct_inputs"] == report["pairs"]
    assert report["stress_30x30"] == 80
    assert report["relay_ranks"] >= {2, 3, 4}
    assert {
        "other_setting",
        "wrong_intermediate_plus_one",
        "source_color_envelope",
        "most_frequent_non_source",
        "least_frequent_non_source",
        "fixed_rank_1",
        "fixed_rank_2",
        "fixed_rank_3",
        "fixed_rank_4",
        "first_numeric_non_source",
        "last_numeric_non_source",
    } <= set(report["rivals"])

    witness = audit.python_causal_witness(seed=17)
    assert witness["key"] + 1 == witness["wrong_key"]
    assert witness["correct_output"] != witness["wrong_output"]
    assert witness["correct_color"] != witness["wrong_color"]
