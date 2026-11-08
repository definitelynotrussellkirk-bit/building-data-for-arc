"""Focused source-review and native-parametric tests for 0d191ce876ab."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

from arcpuzzles.parametric_worker import evaluate_contract
from reviewer_support import canonical_path, find_root, public_challenge_bytes


TASK_ID = "0d191ce876ab"
HOME = Path(__file__).resolve().parents[1]
REPO = HOME.parents[1]
PROTOTYPE = HOME / "workspace/parametric/prototype.py"
PROMOTION = HOME / "workspace/parametric/promotion.json"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing runnable source: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def base():
    return _load(HOME / "generator.py", "generator_0d191ce876ab_test")


@pytest.fixture(scope="module")
def p():
    return _load(PROTOTYPE, "parametric_0d191ce876ab_test")


def _canonical_program() -> str:
    rows = [json.loads(line) for line in canonical_path(find_root(__file__)).read_text().splitlines()]
    programs = {row["program_solution"] for row in rows if row["task_id"] == TASK_ID}
    assert len(programs) == 1
    return next(iter(programs))


def _adjacent_survivors(base, grid) -> bool:
    cells = {(r, c) for r, c, _ in base._survivor_cells(grid)}
    return any((r + dr, c + dc) in cells for r, c in cells for dr, dc in ((1, 0), (0, 1)))


def _merge_then_nonzero_neighbor_filter(grid):
    merged = [[2 if value == 1 else value for value in row] for row in grid]
    height, width = len(merged), len(merged[0])
    output = [[0] * width for _ in range(height)]
    for r in range(1, height - 1):
        for c in range(1, width - 1):
            value = merged[r][c]
            if (value != 0 and merged[r - 1][c] != 0 and merged[r + 1][c] != 0
                    and merged[r][c - 1] != 0 and merged[r][c + 1] != 0):
                output[r][c] = value
    return output


def test_base_pins_rule_and_rejects_unknown_or_coercive_overrides(base):
    assert base.RULE_HASH == "ddef27a30643"
    with pytest.raises(ValueError, match="unknown override"):
        base.generate(0, 0, __unknown_axis__=1)
    with pytest.raises((TypeError, ValueError)):
        base.generate(0, 0, n_keep=True)


def test_n_keep_override_is_exact_and_sampler_refutes_one_center_per_object(base):
    grid = base.generate(0, 0, difficulty="easy", n_keep=6, n_drop=0)
    assert len(base._survivor_cells(grid)) == 6
    assert base.self_check(grid) == []
    draws = [base.generate(17, index, difficulty="medium") for index in range(8)]
    assert all(base.self_check(grid) == [] for grid in draws)
    assert any(_adjacent_survivors(base, grid) for grid in draws)


def test_default_program_is_byte_exact_and_settings_are_strict(p):
    assert p.program({"preprocess": "identity"}) == _canonical_program()
    assert p.program({"preprocess": "merge_1_into_2"}) != _canonical_program()
    for bad in (
        {}, {"preprocess": "wrong"}, {"preprocess": "identity", "extra": 1},
        {"preprocess": True},
    ):
        with pytest.raises(ValueError):
            p.program(bad)


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_counts_matched_inputs_prefix_stability_and_two_demo_identification(p, demos):
    identity = p.generate(23, {"preprocess": "identity"}, demos, 4)
    merged = p.generate(23, {"preprocess": "merge_1_into_2"}, demos, 4)
    one = p.generate(23, {"preprocess": "identity"}, demos, 1)
    assert len(identity["train"]) == demos and len(identity["test"]) == 4
    assert len(merged["train"]) == demos and len(merged["test"]) == 4
    for split in ("train", "test"):
        assert [pair["input"] for pair in identity[split]] == [pair["input"] for pair in merged[split]]
    assert any(a["output"] != b["output"] for a, b in zip(identity["train"], merged["train"]))
    visible = {"train": identity["train"], "test": [{"input": identity["test"][0]["input"]}]}
    assert public_challenge_bytes(visible) == public_challenge_bytes(one)
    inputs = [json.dumps(pair["input"]) for split in ("train", "test") for pair in identity[split]]
    assert len(inputs) == len(set(inputs))

    other = {"preprocess": "merge_1_into_2"}
    assert any(p.transform(pair["input"], other) != pair["output"] for pair in identity["train"])
    other = {"preprocess": "identity"}
    assert any(p.transform(pair["input"], other) != pair["output"] for pair in merged["train"])


def test_fourth_query_is_substantive_30_square_and_all_claims_match_transform(p):
    for setting in ("identity", "merge_1_into_2"):
        settings = {"preprocess": setting}
        episode = p.generate(5, settings, 2, 4)
        grid = episode["test"][3]["input"]
        assert len(grid) == 30 and all(len(row) == 30 for row in grid)
        for r0 in (0, 15):
            for c0 in (0, 15):
                assert sum(cell != 0 for row in grid[r0:r0 + 15] for cell in row[c0:c0 + 15]) >= 20
        for split in ("train", "test"):
            for pair in episode[split]:
                assert pair["output"] == p.transform(pair["input"], settings)


def test_merge_lessons_preserve_an_unaffected_survivor_colour(p):
    """Catch a shortcut that paints every surviving location with colour 2."""
    episode = p.generate(0, {"preprocess": "merge_1_into_2"}, 2, 4)
    assert all(
        any(value not in (0, 2) for row in pair["output"] for value in row)
        for pair in episode["train"]
    )


def test_merge_lessons_refute_post_merge_color_agnostic_neighbors(p):
    """Catch a wrong stage-B rule that fits the old demos but fails a query."""
    episode = p.generate(9, {"preprocess": "merge_1_into_2"}, 2, 4)
    candidate_train = [
        _merge_then_nonzero_neighbor_filter(pair["input"]) for pair in episode["train"]
    ]
    candidate_test = [
        _merge_then_nonzero_neighbor_filter(pair["input"]) for pair in episode["test"]
    ]
    assert any(got != pair["output"] for got, pair in zip(candidate_train, episode["train"]))
    assert any(got != pair["output"] for got, pair in zip(candidate_test, episode["test"]))


def test_merge_stage_changes_intermediate_consumed_by_survivor_filter(p):
    episode = p.generate(17, {"preprocess": "merge_1_into_2"}, 2, 4)
    pair = next(
        pair for pair in [*episode["train"], *episode["test"]]
        if p.transform(pair["input"], {"preprocess": "identity"}) != pair["output"]
    )
    intermediate = p.intermediate(pair["input"], {"preprocess": "merge_1_into_2"})
    assert intermediate != pair["input"]
    assert p.survivor_filter(intermediate) == pair["output"]
    assert p.survivor_filter(pair["input"]) != pair["output"]


@pytest.mark.parametrize("case", [
    {"seed": True}, {"demos": 1}, {"demos": 7}, {"demos": 2.0},
    {"queries": 0}, {"queries": 5}, {"queries": True},
])
def test_invalid_generation_requests_are_rejected(p, case):
    args = {"seed": 0, "settings": {"preprocess": "identity"}, "demos": 2, "queries": 4}
    args.update(case)
    with pytest.raises(ValueError):
        p.generate(**args)


def test_native_worker_contract_identifies_both_settings(p):
    contract = json.loads(PROMOTION.read_text())
    programs = {
        p.program({"preprocess": "identity"}): {"preprocess": "identity"},
        p.program({"preprocess": "merge_1_into_2"}): {"preprocess": "merge_1_into_2"},
    }

    def apply(program, grid):
        return p.transform(grid, programs[program])

    jobs = [
        {"seed": seed, "settings": {"preprocess": setting}, "demos": 2, "queries": 4}
        for seed in (0, 17) for setting in ("identity", "merge_1_into_2")
    ]
    report = evaluate_contract(REPO, TASK_ID, contract, jobs, apply_program=apply)
    assert len(report["episodes"]) == 4
    assert all(check["survivors"] == [check["settings"]] for check in report["checks"])
