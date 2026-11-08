"""Native promotion contract for the 5d6fcce80b6a row-bound/copy family."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

ROOT = find_root(__file__)
HOME = ROOT / "generators/5d6fcce80b6a/workspace/parametric"
SETTINGS = (
    {"copy_diagonal": "main", "separator_policy": "through_last"},
    {"copy_diagonal": "anti", "separator_policy": "through_last"},
    {"copy_diagonal": "main", "separator_policy": "strict_between"},
    {"copy_diagonal": "anti", "separator_policy": "strict_between"},
)


def load_adapter():
    path = HOME / "adapter.py"
    assert path.is_file(), "native parametric adapter is missing"
    spec = importlib.util.spec_from_file_location("native_5d6fcce80b6a_test_adapter", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()]
    programs = {
        row["program_solution"]
        for row in rows
        if row.get("task_id") == "5d6fcce80b6a" and isinstance(row.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def grid_key(grid) -> str:
    return json.dumps(grid, separators=(",", ":"))


def test_native_contract_preserves_exact_canonical_default() -> None:
    adapter = load_adapter()
    default = {"copy_diagonal": "main", "separator_policy": "through_last"}
    assert adapter.program(default) == canonical_program()
    assert (HOME / "canonical.rkt").read_text() == canonical_program()
    assert len({adapter.program(setting) for setting in SETTINGS}) == 4

    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert contract["default"] == default
    assert contract["parameters"] == {
        "copy_diagonal": ["main", "anti"],
        "separator_policy": ["through_last", "strict_between"],
    }
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}


@pytest.mark.parametrize("seed", [0, 17, 934])
@pytest.mark.parametrize("demos", [2, 3, 6])
def test_all_supported_settings_share_inputs_and_are_taught(seed: int, demos: int) -> None:
    adapter = load_adapter()
    sequences = []
    for setting in SETTINGS:
        episode = adapter.generate(seed, setting, demos, 4)
        assert episode == adapter.generate(seed, setting, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        sequence = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({grid_key(grid) for grid in sequence}) == demos + 4
        certificate = adapter.teaching_check(episode)
        assert certificate["declared_survivors"] == [setting]
        assert certificate["harmful_survivors"] == []
        assert certificate["query_answers_used_for_fitting"] is False
        assert all(certificate["query_identifiable"])
        sequences.append(sequence)
    assert sequences[0] == sequences[1] == sequences[2] == sequences[3]


@pytest.mark.parametrize("queries", [1, 2, 3, 4])
def test_prefix_stability_and_sequential_public_projection(queries: int) -> None:
    adapter = load_adapter()
    setting = {"copy_diagonal": "anti", "separator_policy": "strict_between"}
    episode = adapter.generate(17, setting, 3, queries)
    one = adapter.generate(17, setting, 3, 1)
    four = adapter.generate(17, setting, 3, 4)
    assert episode["train"] == four["train"]
    assert episode["test"] == four["test"][:queries]
    assert one["test"] == four["test"][:1]

    first = adapter.model_view(episode, 0)
    assert public_challenge_bytes(first) == public_challenge_bytes(adapter.model_view(one, 0))
    assert public_challenge_id(first) == hashlib.sha256(public_challenge_bytes(first)).hexdigest()
    assert set(first) == {"train", "test"}
    assert first["test"] == [{"input": episode["test"][0]["input"]}]

    hidden = deepcopy(episode)
    hidden.update(seed=-1, settings={"private": True}, program_solution="private")
    hidden["train"][0]["private"] = "private"
    for pair in hidden["test"]:
        pair["output"] = [[9]]
    assert adapter.model_view(hidden, 0) == first


@pytest.mark.parametrize("setting", SETTINGS)
def test_python_claims_match_protected_racket(
    setting: dict[str, str], protected_racket_bridge
) -> None:
    adapter = load_adapter()
    episode = adapter.generate(17, setting, 2, 4)

    from puzzle_generators.rule_wrap import wrap_rule

    def literal(grid):
        rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
        return f"'({rows})"

    wrapped = wrap_rule(adapter.program(setting))
    for pair in episode["train"] + episode["test"]:
        actual = protected_racket_bridge.eval_text(
            f"({wrapped} {literal(pair['input'])})"
        )
        assert actual == pair["output"]


def test_four_queries_cover_real_sizes_and_substantive_30x30_output() -> None:
    adapter = load_adapter()
    episode = adapter.generate(
        17,
        {"copy_diagonal": "main", "separator_policy": "through_last"},
        2,
        4,
    )
    input_shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    output_shapes = [(len(pair["output"]), len(pair["output"][0])) for pair in episode["test"]]
    assert input_shapes == [(7, 8), (9, 10), (12, 13), (15, 15)]
    assert output_shapes == [(14, 16), (18, 20), (24, 26), (30, 30)]

    grid = episode["test"][-1]["input"]
    facts = adapter.analyze(grid)
    assert facts["height"] == 15 and facts["width"] == 15
    assert facts["first_colored"] > 0
    assert facts["last_colored"] < 14
    assert len(facts["internal_blank_rows"]) >= 3
    assert facts["nonzero_cells"] >= 70
    nonzero = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    assert any(c == 0 for _, c in nonzero)
    assert any(c == 14 for _, c in nonzero)


def test_wrong_row_bound_intermediate_changes_final_output_in_racket(
    protected_racket_bridge,
) -> None:
    adapter = load_adapter()
    setting = {"copy_diagonal": "anti", "separator_policy": "strict_between"}
    pair = adapter.generate(17, setting, 2, 4)["test"][-1]
    facts = adapter.analyze(pair["input"])
    assert facts["last_colored"] > facts["first_colored"] + 2
    wrong = facts["first_colored"]
    counterfactual = adapter.counterfactual_program(setting, wrong_last_colored=wrong)

    from puzzle_generators.rule_wrap import wrap_rule

    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in pair["input"])
    literal = f"'({rows})"
    correct = protected_racket_bridge.eval_text(
        f"({wrap_rule(adapter.program(setting))} {literal})"
    )
    ablated = protected_racket_bridge.eval_text(
        f"({wrap_rule(counterfactual)} {literal})"
    )
    assert correct == pair["output"]
    assert ablated != correct


@pytest.mark.parametrize(
    "seed,demos,queries",
    [
        (True, 2, 4),
        (1.0, 2, 4),
        (-1, 2, 4),
        (2**63, 2, 4),
        (0, True, 4),
        (0, 1, 4),
        (0, 7, 4),
        (0, 2, 0),
        (0, 2, 5),
        (0, 2, 4.0),
    ],
)
def test_invalid_generation_requests_fail(seed, demos, queries) -> None:
    with pytest.raises((TypeError, ValueError)):
        load_adapter().generate(seed, SETTINGS[0], demos, queries)


@pytest.mark.parametrize(
    "setting",
    [
        {},
        {"copy_diagonal": "main"},
        {"copy_diagonal": "main", "separator_policy": "through_last", "extra": 1},
        {"copy_diagonal": True, "separator_policy": "through_last"},
        {"copy_diagonal": "main", "separator_policy": 1},
        {"copy_diagonal": "other", "separator_policy": "through_last"},
        {"copy_diagonal": "main", "separator_policy": "other"},
    ],
)
def test_settings_are_exact_and_typed(setting) -> None:
    with pytest.raises((TypeError, ValueError)):
        load_adapter().program(setting)
