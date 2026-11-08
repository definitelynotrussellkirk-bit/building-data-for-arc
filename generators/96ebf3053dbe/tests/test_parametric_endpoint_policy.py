"""Focused tests for the native endpoint-policy parametric family."""
from __future__ import annotations

from copy import deepcopy
import importlib.util
import json
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import (
    canonical_path,
    find_root,
    load_selected_generator,
    public_challenge_bytes,
    public_challenge_id,
)

TASK_ID = "96ebf3053dbe"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"
PROTOTYPE = PARAMETRIC / "prototype.py"
ADAPTER = PARAMETRIC / "adapter.py"
PROMOTION = PARAMETRIC / "promotion.json"
VERIFY = PARAMETRIC / "verify.py"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing implementation: {path.relative_to(ROOT)}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise AssertionError("canonical program missing")


def _hand_grid() -> list[list[int]]:
    """Two lawful bars anchored at bottom/right, so anchor-side shortcuts fail."""
    grid = [[7] * 9 for _ in range(9)]
    grid[4] = [9] * 9
    grid[0][7] = 5
    grid[1][1] = 5
    grid[5][1] = 6
    grid[6][1] = 6
    grid[7][1] = 2
    grid[8][4] = grid[8][5] = grid[8][6] = 6
    grid[8][7] = 2
    return grid


def _execute(bridge: RacketBridge, program: str, grid: list[list[int]]) -> list[list[int]]:
    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


def _positions(grid: list[list[int]], color: int) -> set[tuple[int, int]]:
    return {
        (row, col)
        for row, values in enumerate(grid)
        for col, value in enumerate(values)
        if value == color
    }


def _inputs(episode: dict) -> list[list[list[int]]]:
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def _outputs(episode: dict) -> list[list[list[int]]]:
    return [pair["output"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_canonical_and_racket_endpoint_choices_are_literal():
    prototype = _load(PROTOTYPE, "endpoint_policy_prototype_program")
    assert prototype.program_for("opposite") == _canonical_program()

    grid = _hand_grid()
    with RacketBridge() as bridge:
        opposite = _execute(bridge, prototype.program_for("opposite"), grid)
        adjacent = _execute(bridge, prototype.program_for("adjacent"), grid)

    assert _positions(opposite, 2) == {(5, 1), (8, 4)}
    assert _positions(opposite, 5) == {(3, 1), (0, 4)}
    assert _positions(adjacent, 2) == {(6, 1), (8, 6)}
    assert _positions(adjacent, 5) == {(2, 1), (0, 6)}
    assert _positions(opposite, 6) == set()
    assert _positions(adjacent, 6) == set()
    assert opposite != adjacent


@pytest.mark.parametrize("demos", [2, 3, 4, 5, 6])
def test_counts_are_independent_inputs_are_matched_and_every_pair_teaches(demos: int):
    prototype = _load(PROTOTYPE, f"endpoint_policy_prototype_counts_{demos}")
    opposite = prototype.build_claimed_episode(
        seed=20261024,
        destination_endpoint="opposite",
        demos=demos,
        queries=4,
    )
    adjacent = prototype.build_claimed_episode(
        seed=20261024,
        destination_endpoint="adjacent",
        demos=demos,
        queries=4,
    )

    assert len(opposite["train"]) == len(adjacent["train"]) == demos
    assert len(opposite["test"]) == len(adjacent["test"]) == 4
    assert _inputs(opposite) == _inputs(adjacent)
    assert len({json.dumps(grid, separators=(",", ":")) for grid in _inputs(opposite)}) == demos + 4
    assert all(left != right for left, right in zip(_outputs(opposite), _outputs(adjacent)))
    assert opposite["settings"] == {"destination_endpoint": "opposite"}
    assert adjacent["settings"] == {"destination_endpoint": "adjacent"}


def test_sampler_preserves_production_grammar_and_has_substantive_maximum_query():
    prototype = _load(PROTOTYPE, "endpoint_policy_prototype_grammar")
    generator, _, _ = load_selected_generator(TASK_ID, root=ROOT)
    episode = prototype.build_claimed_episode(
        seed=73,
        destination_endpoint="opposite",
        demos=6,
        queries=4,
    )
    shapes = []
    for pair in episode["train"] + episode["test"]:
        grid = pair["input"]
        shapes.append((len(grid), len(grid[0])))
        assert generator.self_check(grid) == []
        assert pair["output"] == prototype.apply_python(grid, "opposite")
        assert all(type(cell) is int and 0 <= cell <= 9 for row in grid for cell in row)
    assert shapes[-1] == (29, 30)
    stress = episode["test"][-1]["input"]
    analysis = generator._analysis(stress)
    assert len(analysis["records"]) >= 4
    assert any(len(record["cells"]) >= 6 for record in analysis["records"])
    assert any(
        row in {15, 28} or col in {0, 29}
        for record in analysis["records"]
        for row, col in record["cells"] | {record["anchor"]}
    )


def test_public_projection_hides_private_data_and_sequential_first_turn_is_stable():
    prototype = _load(PROTOTYPE, "endpoint_policy_prototype_public")
    episode = prototype.build_claimed_episode(
        seed=41,
        destination_endpoint="adjacent",
        demos=3,
        queries=4,
    )
    public = prototype.public_challenge(episode)
    assert set(public) == {"train", "test"}
    assert all(set(pair) == {"input", "output"} for pair in public["train"])
    assert all(set(pair) == {"input"} for pair in public["test"])
    raw = public_challenge_bytes(public)
    public_id = public_challenge_id(public)

    private_mutation = deepcopy(episode)
    private_mutation["settings"] = {"destination_endpoint": "opposite"}
    private_mutation["program"] = "private replacement"
    private_mutation["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(prototype.public_challenge(private_mutation)) == raw
    assert public_challenge_id(prototype.public_challenge(private_mutation)) == public_id

    first = prototype.sequential_turn(episode, 0)
    assert first == prototype.public_challenge(episode, query_indices=[0])
    assert public_challenge_bytes(first) == public_challenge_bytes(
        prototype.public_challenge(episode, query_indices=[0])
    )
    assert first["test"] == [{"input": episode["test"][0]["input"]}]
    later = prototype.sequential_turn(episode, 1)
    assert later == {"test": [{"input": episode["test"][1]["input"]}]}
    serialized = json.dumps(later, sort_keys=True)
    assert "output" not in serialized
    assert "destination_endpoint" not in serialized
    assert "count" not in serialized



def test_native_adapter_contract_and_request_validation():
    prototype = _load(PROTOTYPE, "endpoint_policy_prototype_contract")
    adapter = _load(ADAPTER, "endpoint_policy_adapter_contract")
    assert json.loads(PROMOTION.read_text()) == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/96ebf3053dbe/workspace/parametric/adapter.py",
        "parameters": {"destination_endpoint": ["opposite", "adjacent"]},
        "default": {"destination_endpoint": "opposite"},
        "limits": {"demos": [2, 6], "queries": [4, 4]},
        "resources": [
            "generators/96ebf3053dbe/workspace/parametric/prototype.py"
        ],
    }
    for setting in prototype.ALLOWED_SETTINGS:
        settings = {"destination_endpoint": setting}
        assert adapter.program(settings) == prototype.program_for(setting)
        generated = adapter.generate(19, settings, 2, 4)
        assert len(generated["train"]) == 2
        assert len(generated["test"]) == 4
        assert generated["program_solution"] == prototype.program_for(setting)

    bad_calls = [
        (-1, {"destination_endpoint": "opposite"}, 2, 4),
        (True, {"destination_endpoint": "opposite"}, 2, 4),
        (0, {"destination_endpoint": "opposite"}, 1, 4),
        (0, {"destination_endpoint": "opposite"}, 7, 4),
        (0, {"destination_endpoint": "opposite"}, True, 4),
        (0, {"destination_endpoint": "opposite"}, 2, 3),
        (0, {"destination_endpoint": "opposite"}, 2, True),
        (0, {"destination_endpoint": "far"}, 2, 4),
        (0, {"destination_endpoint": "opposite", "extra": 1}, 2, 4),
    ]
    for args in bad_calls:
        with pytest.raises(ValueError):
            adapter.generate(*args)



def test_verify_materializes_protected_racket_evidence_and_rejects_finite_rivals(tmp_path):
    verify = _load(VERIFY, "endpoint_policy_verify_contract")
    out = tmp_path / "evidence"
    report = verify.verify(seed=20261024, out_dir=out)

    assert report["schema"] == "96ebf3053dbe-endpoint-policy-verification-v1"
    assert report["status"] == "passed"
    assert report["racket"]["backend"] == "racket"
    assert report["racket"]["protected"] is True
    assert report["counts"] == {
        "settings": 2,
        "demonstrations_per_setting": 3,
        "queries_per_setting": 4,
        "racket_checked_pairs": 14,
        "racket_program_evaluations": 56,
    }
    assert report["maximum_query"]["shape"] == [29, 30]
    assert report["maximum_query"]["selected_racket_matches_claim"] is True
    assert set(report["source_hashes"]) == {
        "generators/96ebf3053dbe/generator.py",
        "generators/96ebf3053dbe/workspace/parametric/prototype.py",
        "generators/96ebf3053dbe/workspace/parametric/adapter.py",
        "generators/96ebf3053dbe/workspace/parametric/promotion.json",
        "generators/96ebf3053dbe/workspace/parametric/verify.py",
    }

    assert {row["setting"] for row in report["settings"]} == set(
        verify.prototype.ALLOWED_SETTINGS
    )
    for row in report["settings"]:
        assert row["selected_racket_exact"] is True
        assert row["demos_identify_setting"] is True
        assert row["all_queries_checked"] is True
        assert {rival["name"] for rival in row["rivals"]} == {
            "alternate_setting",
            "skip_anchor",
            "erase_only",
        }
        assert all(rival["rejected_by_demonstrations"] for rival in row["rivals"])

    public_files = sorted((out / "public").glob("*.json"))
    assert len(public_files) == 2
    for path in public_files:
        raw = path.read_bytes()
        assert path.stem == __import__("hashlib").sha256(raw).hexdigest()
        challenge = json.loads(raw)
        assert len(challenge["train"]) == 3
        assert len(challenge["test"]) == 4
        assert all(set(pair) == {"input", "output"} for pair in challenge["train"])
        assert all(set(pair) == {"input"} for pair in challenge["test"])
        assert raw == public_challenge_bytes(challenge)

    for setting in verify.prototype.ALLOWED_SETTINGS:
        assert (out / "private" / "episodes" / f"{setting}.json").is_file()
        assert (out / "private" / "rules" / f"{setting}.rkt").is_file()
    draft = report["counterfactual_draft"]
    assert draft["ablation"] == "skip_a"
    assert draft["program_output"] != draft["counterfactual_output"]
    assert draft["intermediate_value"]["selected_endpoints"]
