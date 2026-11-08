"""Focused contract and teaching checks for the opt-in parametric family."""
from __future__ import annotations

from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
CANONICAL_PROGRAM = "(rule! (let ((dummy 0)) (define (e8b-list< a b) (cond ((empty? a) #f) ((< (first a) (first b)) #t) ((> (first a) (first b)) #f) (else (e8b-list< (rest a) (rest b))))) (let ((largest (first (sort (filter (lambda (obj) (= (obj-color obj) 1)) (objects g 0)) (lambda (a b) (or (> (obj-size a) (obj-size b)) (and (= (obj-size a) (obj-size b)) (e8b-list< (obj-bbox a) (obj-bbox b))))))))) (paint-cells g (obj-cells largest) 7))))"


def _load(name: str, path: Path):
    spec = spec_from_file_location(name, path)
    assert spec and spec.loader
    module = module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_adapter_preserves_exact_canonical_program_and_validates_settings():
    prototype = _load("largest_partner_prototype", PARAMETRIC / "prototype.py")
    adapter = _load("largest_partner_adapter", PARAMETRIC / "adapter.py")

    assert adapter.program({"mode": "canonical"}) == CANONICAL_PROGRAM
    assert adapter.program({"mode": "size_keyed_partner"}) == prototype.PARTNER_PROGRAM

    for invalid in ({}, {"mode": "unknown"}, {"mode": "canonical", "extra": 1}, None):
        with pytest.raises(ValueError):
            adapter.program(invalid)


def _components_4(grid, color=1):
    height, width = len(grid), len(grid[0])
    seen = set()
    components = []
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
                r, c = current
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nxt = (r + dr, c + dc)
                    if (
                        0 <= nxt[0] < height
                        and 0 <= nxt[1] < width
                        and grid[nxt[0]][nxt[1]] == color
                        and nxt not in seen
                    ):
                        seen.add(nxt)
                        stack.append(nxt)
            components.append(tuple(sorted(cells)))
    return sorted(components, key=min)


def _expected_output(grid, mode):
    components = _components_4(grid)
    largest = max(components, key=len)
    out = [row[:] for row in grid]
    for row, col in largest:
        out[row][col] = 7
    if mode == "size_keyed_partner":
        partner_size = len(largest) - 3
        partner = next(component for component in components if len(component) == partner_size)
        for row, col in partner:
            out[row][col] = 2
    return out


@pytest.mark.parametrize("seed", [0, 17, 991])
@pytest.mark.parametrize("demos", range(2, 7))
@pytest.mark.parametrize("mode", ["canonical", "size_keyed_partner"])
def test_episode_counts_distinct_inputs_geometry_and_python_labels(seed, demos, mode):
    prototype = _load(f"largest_partner_proto_{seed}_{demos}_{mode}", PARAMETRIC / "prototype.py")
    episode = prototype.generate_episode(seed, mode=mode, demos=demos, queries=4)

    assert len(episode["train"]) == demos
    assert len(episode["test"]) == 4
    assert episode["program_solution"] == prototype.rule_text(mode)

    pairs = episode["train"] + episode["test"]
    serialized = [repr(pair["input"]) for pair in pairs]
    assert len(serialized) == len(set(serialized))
    assert [max(map(len, _components_4(pair["input"]))) for pair in episode["train"][:2]] == [5, 7]

    for pair in pairs:
        grid = pair["input"]
        assert 8 <= len(grid) <= 30
        assert 10 <= len(grid[0]) <= 30
        assert all(type(cell) is int for row in grid for cell in row)
        assert {cell for row in grid for cell in row} <= {0, 1, 8}
        components = _components_4(grid)
        sizes = sorted(map(len, components))
        assert sizes[:3] == [2, 3, 4]
        assert sizes[-1] in {5, 6, 7}
        assert len(sizes) == 4
        assert pair["output"] == _expected_output(grid, mode)

    stress = next(pair["input"] for pair in episode["test"] if len(pair["input"]) == 30 and len(pair["input"][0]) == 30)
    nonzero = [(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value]
    assert len(nonzero) >= 45
    assert {0, 29} <= {r for r, _ in nonzero}
    assert {0, 29} <= {c for _, c in nonzero}
    assert 8 in {stress[r][c] for r, c in nonzero}


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True, "mode": "canonical", "demos": 3, "queries": 4},
        {"seed": -1, "mode": "canonical", "demos": 3, "queries": 4},
        {"seed": 0, "mode": "unknown", "demos": 3, "queries": 4},
        {"seed": 0, "mode": "canonical", "demos": 1, "queries": 4},
        {"seed": 0, "mode": "canonical", "demos": 7, "queries": 4},
        {"seed": 0, "mode": "canonical", "demos": 3, "queries": 3},
        {"seed": 0, "mode": "canonical", "demos": 3, "queries": 5},
    ],
)
def test_episode_rejects_out_of_contract_requests(kwargs):
    prototype = _load("largest_partner_bad_requests", PARAMETRIC / "prototype.py")
    with pytest.raises(ValueError):
        prototype.generate_episode(**kwargs)


def test_bounded_teaching_audit_refutes_declared_shortcuts():
    audit = _load("largest_partner_audit", PARAMETRIC / "audit.py")
    report = audit.python_audit(seeds=(0, 17), demo_counts=range(2, 7))

    assert report["episodes"] == 20
    assert report["ambiguities"] == []
    assert report["distinct_inputs"] == report["pairs"]
    assert report["stress_30x30"] == 20
    assert {
        "canonical_only",
        "fixed_size_2_partner",
        "fixed_size_3_partner",
        "fixed_size_4_partner",
        "second_largest_partner",
        "smallest_partner",
        "largest_minus_2_partner",
    } <= set(report["rivals"])
