"""Native parametric contract for b5c887448ed9."""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

ROOT = find_root(__file__)
HOME = ROOT / "generators/b5c887448ed9/workspace/parametric"
SETTINGS = (
    {"overwrite_policy": "reading_order"},
    {"overwrite_policy": "longest_path_last"},
)


def load_adapter():
    path = HOME / "adapter.py"
    assert path.is_file()
    spec = importlib.util.spec_from_file_location("native_b5c887448ed9_test_adapter", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    rows = [json.loads(line) for line in canonical_path(ROOT).read_text().splitlines()]
    programs = {
        row["program_solution"]
        for row in rows
        if row.get("task_id") == "b5c887448ed9" and isinstance(row.get("program_solution"), str)
    }
    assert len(programs) == 1
    return next(iter(programs))


def grid_key(grid) -> str:
    return json.dumps(grid, separators=(",", ":"))


def test_contract_preserves_exact_canonical_default():
    adapter = load_adapter()
    assert adapter.program(SETTINGS[0]) == canonical_program()
    assert (HOME / "canonical.rkt").read_text() == canonical_program()
    assert adapter.program(SETTINGS[1]) != canonical_program()
    contract = json.loads((HOME / "promotion.json").read_text())
    assert contract["default"] == SETTINGS[0]
    assert contract["parameters"] == {"overwrite_policy": ["reading_order", "longest_path_last"]}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 3


@pytest.mark.parametrize("seed", [0, 17, 919])
@pytest.mark.parametrize("demos", [2, 3, 6])
def test_settings_share_inputs_and_demos_identify_policy(seed: int, demos: int):
    adapter = load_adapter()
    sequences = []
    for setting in SETTINGS:
        episode = adapter.generate(seed, setting, demos, 4)
        assert episode == adapter.generate(seed, setting, demos, 4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        grids = [pair["input"] for pair in episode["train"] + episode["test"]]
        assert len({grid_key(grid) for grid in grids}) == demos + 4
        certificate = adapter.teaching_check(episode)
        assert certificate["declared_survivors"] == [setting]
        assert certificate["harmful_survivors"] == []
        assert certificate["query_answers_used_for_fitting"] is False
        assert all(certificate["query_identifiable"])
        sequences.append(grids)
    assert sequences[0] == sequences[1]


@pytest.mark.parametrize("queries", [1, 2, 3, 4])
def test_prefix_stability_and_public_projection(queries: int):
    adapter = load_adapter()
    setting = SETTINGS[1]
    episode = adapter.generate(17, setting, 3, queries)
    one = adapter.generate(17, setting, 3, 1)
    four = adapter.generate(17, setting, 3, 4)
    assert episode["train"] == four["train"]
    assert episode["test"] == four["test"][:queries]
    assert one["test"] == four["test"][:1]
    first = adapter.model_view(episode, 0)
    assert public_challenge_bytes(first) == public_challenge_bytes(adapter.model_view(one, 0))
    assert public_challenge_id(first) == hashlib.sha256(public_challenge_bytes(first)).hexdigest()
    assert first["test"] == [{"input": episode["test"][0]["input"]}]
    hidden = deepcopy(episode)
    hidden.update(settings={"private": True}, program_solution="private", seed=-1)
    for pair in hidden["test"]:
        pair["output"] = [[9]]
    assert adapter.model_view(hidden, 0) == first


@pytest.mark.parametrize("setting", SETTINGS)
def test_python_claims_match_protected_racket(setting, protected_racket_bridge):
    adapter = load_adapter()
    from puzzle_generators.rule_wrap import wrap_rule

    def literal(grid):
        rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in grid)
        return f"'({rows})"

    episode = adapter.generate(17, setting, 2, 4)
    wrapped = wrap_rule(adapter.program(setting))
    for pair in episode["train"] + episode["test"]:
        assert protected_racket_bridge.eval_text(f"({wrapped} {literal(pair['input'])})") == pair["output"]


def test_queries_reach_substantive_30x30_and_vary_route_priority():
    adapter = load_adapter()
    episode = adapter.generate(17, SETTINGS[1], 2, 4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes == [(14, 16), (18, 20), (24, 27), (30, 30)]
    facts = [adapter.analyze(pair["input"]) for pair in episode["test"]]
    assert all(row["reading_order"] != row["longest_path_order"] for row in facts)
    assert len({tuple(row["path_lengths"]) for row in facts}) == 4
    assert facts[-1]["route_count"] == 9
    assert facts[-1]["painted_cells"] >= 170
    assert facts[-1]["crossing_cells"] >= 8


def test_wrong_priority_intermediate_changes_final_racket_output(protected_racket_bridge):
    adapter = load_adapter()
    from puzzle_generators.rule_wrap import wrap_rule
    pair = adapter.generate(17, SETTINGS[1], 2, 4)["test"][-1]
    facts = adapter.analyze(pair["input"])
    assert facts["reading_order"] != facts["longest_path_order"]
    counterfactual = adapter.counterfactual_program(SETTINGS[1])
    rows = " ".join("(" + " ".join(map(str, row)) + ")" for row in pair["input"])
    literal = f"'({rows})"
    correct = protected_racket_bridge.eval_text(f"({wrap_rule(adapter.program(SETTINGS[1]))} {literal})")
    wrong = protected_racket_bridge.eval_text(f"({wrap_rule(counterfactual)} {literal})")
    assert correct == pair["output"]
    assert wrong != correct


@pytest.mark.parametrize("setting", [{}, {"overwrite_policy": "other"}, {"overwrite_policy": True}, {"overwrite_policy": "reading_order", "x": 1}])
def test_invalid_settings_fail(setting):
    with pytest.raises((TypeError, ValueError)):
        load_adapter().program(setting)


@pytest.mark.parametrize("seed,demos,queries", [(True,2,4),(-1,2,4),(0,1,4),(0,7,4),(0,2,0),(0,2,5),(0,2,4.0)])
def test_invalid_requests_fail(seed, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        load_adapter().generate(seed, SETTINGS[0], demos, queries)
