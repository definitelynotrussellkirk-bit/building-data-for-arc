"""Native-contract tests for the marker-count rotation parametric family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from collections import Counter
from pathlib import Path

import pytest

from arc_repl.racket_bridge import RacketBridge
from puzzle_generators.rule_wrap import wrap_rule
from reviewer_support import canonical_pairs, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "5553241d87bf"
HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def load(name: str):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"missing {path.name}"
    spec = importlib.util.spec_from_file_location(f"marker_count_rotation_{name}", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_program() -> str:
    root = find_root(__file__)
    ledger = root / "shared" / "data" / "canonical" / "puzzles.jsonl"
    return next(
        json.loads(line)["program_solution"]
        for line in ledger.read_text(encoding="utf-8").splitlines()
        if json.loads(line).get("task_id") == TASK_ID
    )


def racket_outputs(programs: dict[str, str], grids: list[list[list[int]]]):
    with RacketBridge() as bridge:
        symbols = {}
        for index, (name, source) in enumerate(programs.items()):
            symbol = f"__marker_rotation_rule_{index}"
            bridge.eval_text(f"(define {symbol} {wrap_rule(source)})")
            symbols[name] = symbol
        inputs = []
        for index, grid in enumerate(grids):
            symbol = f"__marker_rotation_grid_{index}"
            bridge.define_grid(symbol, grid)
            inputs.append(symbol)
        return {
            name: [bridge.eval_text(f"({symbol} {grid})") for grid in inputs]
            for name, symbol in symbols.items()
        }


def test_native_adapter_contract_and_exact_canonical_default():
    adapter = load("adapter")
    promotion = json.loads((HOME / "promotion.json").read_text(encoding="utf-8"))
    settings = {"stamp_transform": "identity"}
    episode = adapter.generate(17, settings, 3, 4)
    assert promotion["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert promotion["default"] == settings
    assert promotion["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert episode["program_solution"] == adapter.program(settings) == canonical_program()
    prototype = load("prototype")
    for pair in canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True):
        assert prototype.transform(pair["input"], settings) == pair["output"]


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_matched_inputs_teach_both_settings_and_declared_shortcuts(demos):
    module = load("prototype")
    settings = [
        {"stamp_transform": "identity"},
        {"stamp_transform": "marker_count_rotation"},
    ]
    expected_rivals = set(module.SETTINGS) | set(module.SHORTCUTS)
    for seed in (0, 17, 239):
        episodes = [module.generate(seed, setting, demos, 4) for setting in settings]
        inputs = [
            [pair["input"] for pair in episode["train"] + episode["test"]]
            for episode in episodes
        ]
        assert inputs[0] == inputs[1]
        assert len({json.dumps(grid, separators=(",", ":")) for grid in inputs[0]}) == demos + 4
        for episode in episodes:
            chosen = episode["settings"][module.PARAMETER_NAME]
            certificate = episode["certificate"]
            assert certificate["identified"] is True
            assert certificate["survivors"] == [chosen]
            assert set(certificate["rejected"]) >= expected_rivals - {chosen}
            assert all(certificate["query_identifiable"])
            for pair in episode["train"] + episode["test"]:
                facts = module.features(pair["input"])
                assert facts["template_zeros"]
                assert set(facts["target_dot_counts"]) >= {1, 2, 3, 4}
        for left, right in zip(
            episodes[0]["train"] + episodes[0]["test"],
            episodes[1]["train"] + episodes[1]["test"],
        ):
            assert left["output"] != right["output"]


def test_python_and_protected_racket_agree_for_settings_and_shortcuts():
    module = load("prototype")
    episode = module.generate(17, {"stamp_transform": "marker_count_rotation"}, 2, 2)
    grids = [pair["input"] for pair in episode["train"] + episode["test"]]
    programs = module.rival_programs()
    actual = racket_outputs(programs, grids)
    expected = {
        name: [module.rival_outputs(grid)[name] for grid in grids]
        for name in programs
    }
    assert actual == expected


def test_demo_query_prefixes_and_public_projection_are_private_invariant():
    module = load("prototype")
    settings = {"stamp_transform": "marker_count_rotation"}
    two = module.generate(17, settings, 2, 4)
    six = module.generate(17, settings, 6, 4)
    one = module.generate(17, settings, 3, 1)
    four = module.generate(17, settings, 3, 4)
    assert two["train"] == six["train"][:2]
    assert two["test"] == six["test"]
    assert one["train"] == four["train"]
    assert one["test"] == four["test"][:1]
    assert module.visible_turn(one, 0) == module.visible_turn(four, 0)
    assert public_challenge_bytes(one) == module.visible_turn(four, 0)
    assert public_challenge_id(one) == hashlib.sha256(public_challenge_bytes(one)).hexdigest()
    changed = copy.deepcopy(four)
    changed["settings"] = {"stamp_transform": "private"}
    changed["program_solution"] = "private"
    changed["test"][0]["output"][0][0] = 9
    assert public_challenge_bytes(four) == public_challenge_bytes(changed)
    for index in range(4):
        visible = json.loads(module.visible_turn(four, index))
        assert set(visible) == {"train", "test"}
        assert visible["test"] == [{"input": four["test"][index]["input"]}]


def test_fourth_query_is_substantive_exact_30_by_30_stress():
    module = load("prototype")
    episode = module.generate(17, {"stamp_transform": "marker_count_rotation"}, 2, 4)
    grid = episode["test"][-1]["input"]
    facts = module.features(grid)
    assert (len(grid), len(grid[0])) == (30, 30)
    assert facts["logical_shape"] == [5, 5]
    assert facts["cell_shape"] == [5, 5]
    assert facts["target_count"] >= 18
    counts = Counter(facts["target_dot_counts"])
    assert set(counts) == {1, 2, 3, 4}
    assert min(counts.values()) >= 4
    nonzero = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    assert any(r == 0 for r, _ in nonzero) and any(r == 29 for r, _ in nonzero)
    assert any(c == 0 for _, c in nonzero) and any(c == 29 for _, c in nonzero)


def test_wrong_intermediate_changes_final_stamp():
    module = load("prototype")
    episode = module.generate(17, {"stamp_transform": "marker_count_rotation"}, 2, 4)
    grid = episode["test"][0]["input"]
    facts = module.features(grid)
    target = next(record for record in facts["targets"] if record["dot_count"] == 2)
    correct = module.transform(grid, {"stamp_transform": "marker_count_rotation"})
    wrong = module.transform_with_count_override(grid, target["index"], 1)
    assert correct != wrong
    r0, r1, c0, c1 = target["bounds"]
    assert [row[c0 : c1 + 1] for row in correct[r0 : r1 + 1]] != [
        row[c0 : c1 + 1] for row in wrong[r0 : r1 + 1]
    ]


def test_verifier_rejects_bad_requests_tampering_duplicates_and_booleans():
    module = load("prototype")
    episode = module.generate(0, {"stamp_transform": "identity"}, 2, 4)
    for kind in ("label", "program", "duplicate", "boolean"):
        bad = copy.deepcopy(episode)
        if kind == "label":
            bad["test"][0]["output"][0][0] = (bad["test"][0]["output"][0][0] + 1) % 10
        elif kind == "program":
            bad["program_solution"] = module.program(
                {"stamp_transform": "marker_count_rotation"}
            )
        elif kind == "duplicate":
            bad["test"][0] = copy.deepcopy(bad["train"][0])
        else:
            bad["train"][0]["input"][0][0] = False
        with pytest.raises(ValueError):
            module.verify_episode(bad)

    invalid = [
        (True, {"stamp_transform": "identity"}, 3, 4),
        (-1, {"stamp_transform": "identity"}, 3, 4),
        (0, {"stamp_transform": "identity"}, 1, 4),
        (0, {"stamp_transform": "identity"}, 7, 4),
        (0, {"stamp_transform": "identity"}, 3, 0),
        (0, {"stamp_transform": "identity"}, 3, 5),
        (0, {"stamp_transform": "mirror"}, 3, 4),
        (0, {"stamp_transform": "identity", "extra": 1}, 3, 4),
    ]
    for args in invalid:
        with pytest.raises(ValueError):
            module.generate(*args)
