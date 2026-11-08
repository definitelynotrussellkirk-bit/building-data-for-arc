from __future__ import annotations

from collections import Counter
import importlib.util
import json
from pathlib import Path
import sys

import pytest


REPO = Path(__file__).resolve().parents[3]
HOME = REPO / "generators/040bfb038c65/workspace/parametric"


def _load_adapter(monkeypatch):
    monkeypatch.syspath_prepend(str(REPO / "shared/runtime"))
    monkeypatch.syspath_prepend(str(HOME))
    path = HOME / "adapter.py"
    spec = importlib.util.spec_from_file_location("test_040_parametric_adapter", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _components(grid, color=4):
    height, width = len(grid), len(grid[0])
    seen = set()
    result = []
    for row in range(height):
        for col in range(width):
            if grid[row][col] != color or (row, col) in seen:
                continue
            stack = [(row, col)]
            seen.add((row, col))
            cells = []
            while stack:
                current = stack.pop()
                cells.append(current)
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    neighbor = current[0] + dr, current[1] + dc
                    if (
                        0 <= neighbor[0] < height
                        and 0 <= neighbor[1] < width
                        and grid[neighbor[0]][neighbor[1]] == color
                        and neighbor not in seen
                    ):
                        seen.add(neighbor)
                        stack.append(neighbor)
            result.append(tuple(sorted(cells)))
    return sorted(result, key=min)


def _normalize(cells):
    top = min(row for row, _ in cells)
    left = min(col for _, col in cells)
    return tuple(sorted((row - top, col - left) for row, col in cells))


def _transforms(cells):
    original = list(_normalize(cells))
    variants = set()
    for reflected in (False, True):
        current = (
            [(row, -col) for row, col in original]
            if reflected
            else list(original)
        )
        for _ in range(4):
            variants.add(_normalize(current))
            current = [(col, -row) for row, col in current]
    return variants


def _roles(grid):
    objects = _components(grid)
    signatures = [min(_transforms(obj)) for obj in objects]
    counts = Counter(signatures)
    oddballs = [obj for obj, signature in zip(objects, signatures) if counts[signature] == 1]
    majorities = [obj for obj, signature in zip(objects, signatures) if counts[signature] > 1]
    assert len(oddballs) == 1 and len(majorities) == 3
    return majorities, oddballs[0]


def _cyan_cells(grid):
    return {(row, col) for row, values in enumerate(grid) for col, value in enumerate(values) if value == 8}


def _expected_farthest_partner(input_grid):
    majorities, oddball = _roles(input_grid)
    odd_anchor = min(oddball)
    partner = max(
        majorities,
        key=lambda obj: abs(min(obj)[0] - odd_anchor[0]) + abs(min(obj)[1] - odd_anchor[1]),
    )
    return set(partner)


def test_adapter_supports_independent_demo_counts_and_four_query_stress(monkeypatch):
    """Catch adapters that hard-code one lesson size or merely pad a small stress case."""
    adapter = _load_adapter(monkeypatch)
    for demos in (2, 3, 6):
        episode = adapter.generate(73, {"target": "outsider"}, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        all_pairs = episode["train"] + episode["test"]
        serialized = [json.dumps(pair["input"], separators=(",", ":")) for pair in all_pairs]
        assert len(serialized) == len(set(serialized))

        stress = episode["test"][-1]["input"]
        assert (len(stress), len(stress[0])) == (30, 30)
        yellow = {(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value == 4}
        assert any(r == 0 for r, _ in yellow)
        assert any(r == 29 for r, _ in yellow)
        assert any(c == 0 for _, c in yellow)
        assert any(c == 29 for _, c in yellow)
        assert len(_components(stress)) == 4


def test_settings_share_inputs_but_select_different_objects(monkeypatch):
    """Catch setting-dependent input leakage and a non-causal alternate labeler."""
    adapter = _load_adapter(monkeypatch)
    canonical = adapter.generate(101, {"target": "outsider"}, 3, 4)
    composed = adapter.generate(101, {"target": "farthest_partner"}, 3, 4)

    canonical_pairs = canonical["train"] + canonical["test"]
    composed_pairs = composed["train"] + composed["test"]
    assert [pair["input"] for pair in canonical_pairs] == [pair["input"] for pair in composed_pairs]

    for canonical_pair, composed_pair in zip(canonical_pairs, composed_pairs):
        majorities, oddball = _roles(canonical_pair["input"])
        assert _cyan_cells(canonical_pair["output"]) == set(oddball)
        assert _cyan_cells(composed_pair["output"]) == _expected_farthest_partner(composed_pair["input"])
        assert canonical_pair["output"] != composed_pair["output"]


def test_default_program_is_exact_canonical_and_settings_are_strict(monkeypatch):
    """Catch canonical drift and silent fallback from malformed private settings."""
    adapter = _load_adapter(monkeypatch)
    from arcpuzzles import Catalog

    catalog = Catalog(REPO)
    programs = {
        row["program_solution"]
        for row in catalog._variants()["040bfb038c65"]
        if isinstance(row.get("program_solution"), str)
    }
    assert programs == {adapter.program({"target": "outsider"})}
    assert adapter.program({"target": "farthest_partner"}) != adapter.program({"target": "outsider"})

    with pytest.raises(ValueError, match="target"):
        adapter.program({"target": "unknown"})
    with pytest.raises(ValueError, match="settings"):
        adapter.generate(0, {}, 3, 4)
    with pytest.raises(ValueError, match="queries"):
        adapter.generate(0, {"target": "outsider"}, 3, 3)


def test_finite_teaching_audit_refutes_rivals_and_checks_public_projection(monkeypatch):
    """Catch visible-demo shortcuts or leakage of private settings/future answers."""
    monkeypatch.syspath_prepend(str(REPO / "shared/runtime"))
    monkeypatch.syspath_prepend(str(HOME))
    path = HOME / "audit.py"
    spec = importlib.util.spec_from_file_location("test_040_parametric_audit", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)

    report = module.run_audit(seeds=(0, 17), demo_counts=(2, 3, 6))
    assert report["schema"] == "arcpuzzles-parametric-teaching-audit-v1"
    assert report["status"] == "passed"
    assert report["ambiguous_cases"] == []
    assert report["episodes_checked"] == 12
    assert report["query_rotations_checked"] == 48
    assert report["projection"]["settings_visible"] is False
    assert report["projection"]["query_outputs_visible"] is False
    assert report["projection"]["future_queries_visible_on_first_turn"] is False
