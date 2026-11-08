from __future__ import annotations

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "repo/shared/runtime"))
PROBE_PATH = Path(__file__).resolve().parents[1] / "audit_probes.py"
spec = importlib.util.spec_from_file_location("audit_probes_under_test", PROBE_PATH)
assert spec is not None and spec.loader is not None
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


def test_numeric_grid_decodes_compact_digit_rows() -> None:
    compact = ["040", "004"]
    assert probe.numeric_grid(compact) == [[0, 4, 0], [0, 0, 4]]


def test_numeric_grid_preserves_integer_matrix_without_aliasing() -> None:
    matrix = [[0, 4], [4, 0]]
    converted = probe.numeric_grid(matrix)
    assert converted == matrix
    assert converted is not matrix
    assert converted[0] is not matrix[0]


def test_leftmost_canonical_counterexample_is_validator_accepted() -> None:
    generator, _ = probe.load_generator("691d467ddb4d")
    pairs = probe.canonical_pairs("691d467ddb4d")
    numeric_pairs = [
        {
            "input": probe.numeric_grid(pair["input"]),
            "output": probe.numeric_grid(pair["output"]),
        }
        for pair in pairs
    ]
    candidates = [
        pair
        for pair in numeric_pairs
        if probe.components(pair["input"])
        and min(
            min(column for _, column in component)
            for component in probe.components(pair["input"])
        ) == 2
        and probe.border_two_rival(pair["input"]) != pair["output"]
    ]
    assert len(candidates) == 1
    assert generator.self_check(deepcopy(candidates[0]["input"])) == []
