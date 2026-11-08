from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
SOURCE = HOME / "workspace/parametric/native_family.py"
ROOT = HOME.parents[1]


def family():
    assert SOURCE.is_file(), "native parametric family is not implemented"
    spec = importlib.util.spec_from_file_location("d4_matrix_native_test", SOURCE)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    for line in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == "397767b9f88c":
            return row["program_solution"]
    raise AssertionError("canonical task missing")


def test_exact_default_and_sequential_largest_block_rule() -> None:
    mod = family()
    assert mod.program() == canonical_program()
    assert mod.program({"finish": "all_matches"}) == canonical_program()
    episode = mod.generate(0, {"finish": "largest_equivalence_blocks"}, demos=3, queries=4)
    pair = episode["train"][0]
    intermediate = mod.transform(pair["input"], {"finish": "all_matches"})
    actual = mod.transform(pair["input"], {"finish": "largest_equivalence_blocks"})
    assert actual == pair["output"]
    assert actual != intermediate
    assert actual != mod.wrong_order_transform(pair["input"])
    assert mod.wrong_order_program().startswith("(rule!")


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
def test_episode_contract_prefixes_matched_inputs_and_identification(seed: int) -> None:
    mod = family()
    full = [mod.generate(seed, setting, demos=6, queries=4) for setting in mod.SETTINGS]
    shared = [pair["input"] for pair in full[0]["train"] + full[0]["test"]]
    assert len({json.dumps(grid) for grid in shared}) == 10
    for setting, episode in zip(mod.SETTINGS, full):
        assert episode == mod.generate(seed, setting, demos=6, queries=4)
        assert episode["settings"] == setting
        assert episode["program_solution"] == mod.program(setting)
        assert [pair["input"] for pair in episode["train"] + episode["test"]] == shared
        for demos, queries in ((3, 1), (4, 2), (6, 4)):
            smaller = mod.generate(seed, setting, demos=demos, queries=queries)
            assert smaller["train"] == episode["train"][:demos]
            assert smaller["test"] == episode["test"][:queries]
    for index in range(3):
        assert full[0]["train"][index]["output"] != full[1]["train"][index]["output"]


def test_first_three_demos_falsify_named_rivals_for_both_settings() -> None:
    mod = family()
    for seed in range(8):
        for setting in mod.SETTINGS:
            episode = mod.generate(seed, setting, demos=3, queries=4)
            truth = [pair["output"] for pair in episode["train"]]
            for name, rival in mod.semantic_rivals(setting).items():
                predicted = [rival(pair["input"]) for pair in episode["train"]]
                assert predicted != truth, (seed, setting, name)


def test_bank_has_diagonal_reflection_witness_and_substantive_30_square() -> None:
    mod = family()
    episode = mod.generate(29, {"finish": "all_matches"}, demos=6, queries=4)
    pairs = episode["train"] + episode["test"]
    assert all(mod.has_diagonal_reflection_witness(pair["input"]) for pair in pairs)
    large = [pair for pair in pairs if len(pair["input"]) == len(pair["input"][0]) == 30]
    assert len(large) == 1
    grid = large[0]["input"]
    assert sum(value != 0 for row in grid for value in row) >= 70
    assert all(any(grid[r][c] for r in range(r0, r0 + 15) for c in range(c0, c0 + 15))
               for r0 in (0, 15) for c0 in (0, 15))
    assert any(grid[0]) and any(grid[-1]) and any(row[0] for row in grid) and any(row[-1] for row in grid)


@pytest.mark.parametrize("kwargs", [
    {"seed": True}, {"seed": -1}, {"seed": 2**63},
    {"demos": 2}, {"demos": 7}, {"demos": 3.0},
    {"queries": 0}, {"queries": 5}, {"queries": True},
    {"settings": {}}, {"settings": {"finish": "other"}},
    {"settings": {"finish": "all_matches", "extra": 1}},
])
def test_strict_request_controls(kwargs) -> None:
    request = {"seed": 0, "settings": {"finish": "all_matches"}, "demos": 3, "queries": 4}
    request.update(kwargs)
    with pytest.raises(ValueError):
        family().generate(**request)
