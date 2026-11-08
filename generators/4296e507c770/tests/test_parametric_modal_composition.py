"""Native-contract tests for the modal transform-composition family."""
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

TASK_ID = "4296e507c770"
HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"


def load(name: str):
    path = HOME / f"{name}.py"
    assert path.is_file(), f"missing {path.name}"
    spec = importlib.util.spec_from_file_location(f"modal_transform_{name}", path)
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
            symbol = f"__modal_transform_rule_{index}"
            bridge.eval_text(f"(define {symbol} {wrap_rule(source)})")
            symbols[name] = symbol
        inputs = []
        for index, grid in enumerate(grids):
            symbol = f"__modal_transform_grid_{index}"
            bridge.define_grid(symbol, grid)
            inputs.append(symbol)
        return {
            name: [bridge.eval_text(f"({symbol} {grid})") for grid in inputs]
            for name, symbol in symbols.items()
        }


def test_native_adapter_contract_and_exact_canonical_default():
    adapter = load("adapter")
    promotion = json.loads((HOME / "promotion.json").read_text(encoding="utf-8"))
    setting = {"stamp_rule": "direct"}
    episode = adapter.generate(17, setting, 3, 4)
    assert promotion["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert promotion["default"] == setting
    assert promotion["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert episode["program_solution"] == adapter.program(setting) == canonical_program()
    prototype = load("prototype")
    for pair in canonical_pairs(TASK_ID, root=find_root(__file__), labeled_only=True):
        assert prototype.transform(pair["input"], setting) == pair["output"]


@pytest.mark.parametrize("demos", [2, 3, 6])
def test_matched_inputs_teach_both_settings_and_shortcuts(demos):
    module = load("prototype")
    settings = [
        {"stamp_rule": "direct"},
        {"stamp_rule": "modal_postcompose"},
    ]
    expected_rivals = set(module.SETTINGS) | set(module.SHORTCUTS)
    for seed in (0, 17, 239):
        episodes = [module.generate(seed, setting, demos, 4) for setting in settings]
        input_lists = [
            [pair["input"] for pair in episode["train"] + episode["test"]]
            for episode in episodes
        ]
        assert input_lists[0] == input_lists[1]
        assert len({json.dumps(grid, separators=(",", ":")) for grid in input_lists[0]}) == demos + 4
        for episode in episodes:
            chosen = episode["settings"][module.PARAMETER_NAME]
            certificate = episode["certificate"]
            assert certificate["identified"] is True
            assert certificate["survivors"] == [chosen]
            assert set(certificate["rejected"]) >= expected_rivals - {chosen}
            assert all(certificate["query_identifiable"])
            for pair in episode["train"] + episode["test"]:
                facts = module.features(pair["input"])
                assert facts["marker_count"] == 5
                assert set(facts["marker_counts"]) == {3, 4, 5, 6}
                assert sorted(facts["marker_counts"].values()) == [1, 1, 1, 2]
                assert facts["modal_color"] in {3, 4, 5, 6}
                assert facts["d4_orbit_size"] == 8
        # Every demonstration uses a non-identity modal cue, so the two settings differ.
        for left, right in zip(episodes[0]["train"], episodes[1]["train"]):
            assert left["output"] != right["output"]


def test_seed_changes_shape_layout_and_marker_order_without_changing_teachability():
    module = load("prototype")
    fingerprints = set()
    for seed in range(32):
        episode = module.generate(seed, {"stamp_rule": "modal_postcompose"}, 2, 4)
        fingerprints.add(
            hashlib.sha256(
                json.dumps(episode["train"][0]["input"], separators=(",", ":")).encode()
            ).hexdigest()
        )
        assert episode["certificate"]["survivors"] == ["modal_postcompose"]
    # Seed variation must change structural content, not merely select one of
    # the eight D4 orientations of a single frozen lesson.
    assert len(fingerprints) >= 24


def test_python_and_protected_racket_agree_for_settings_and_shortcuts():
    module = load("prototype")
    episode = module.generate(17, {"stamp_rule": "modal_postcompose"}, 2, 2)
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
    setting = {"stamp_rule": "modal_postcompose"}
    two = module.generate(17, setting, 2, 4)
    six = module.generate(17, setting, 6, 4)
    one = module.generate(17, setting, 3, 1)
    four = module.generate(17, setting, 3, 4)
    assert two["train"] == six["train"][:2]
    assert two["test"] == six["test"]
    assert one["train"] == four["train"]
    assert one["test"] == four["test"][:1]
    assert module.visible_turn(one, 0) == module.visible_turn(four, 0)
    assert public_challenge_bytes(one) == module.visible_turn(four, 0)
    assert public_challenge_id(one) == hashlib.sha256(public_challenge_bytes(one)).hexdigest()
    changed = copy.deepcopy(four)
    changed["settings"] = {"stamp_rule": "private"}
    changed["program_solution"] = "private"
    changed["test"][0]["output"][0][0] = 9
    assert public_challenge_bytes(four) == public_challenge_bytes(changed)
    for index in range(4):
        visible = json.loads(module.visible_turn(four, index))
        assert set(visible) == {"train", "test"}
        assert visible["test"] == [{"input": four["test"][index]["input"]}]


def test_fourth_query_is_substantive_exact_30_by_30_stress():
    module = load("prototype")
    episode = module.generate(17, {"stamp_rule": "modal_postcompose"}, 2, 4)
    grid = episode["test"][-1]["input"]
    output = episode["test"][-1]["output"]
    facts = module.features(grid)
    assert (len(grid), len(grid[0])) == (30, 30)
    assert facts["template_size"] == 9
    assert facts["marker_count"] == 5
    assert facts["modal_color"] == 3
    assert facts["d4_orbit_size"] == 8
    nonzero = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    stamped = {(r, c) for r, row in enumerate(output) for c, value in enumerate(row) if value == 8}
    for cells in (nonzero, stamped):
        assert any(r == 0 for r, _ in cells) and any(r == 29 for r, _ in cells)
        assert any(c == 0 for _, c in cells) and any(c == 29 for _, c in cells)
    assert len(stamped) >= 35


def test_wrong_intermediate_and_wrong_order_change_final_output():
    module = load("prototype")
    episode = module.generate(17, {"stamp_rule": "modal_postcompose"}, 2, 4)
    grid = episode["train"][0]["input"]
    facts = module.features(grid)
    correct = module.transform(grid, {"stamp_rule": "modal_postcompose"})
    wrong_intermediate = module.transform_with_modal_override(grid, 6 if facts["modal_color"] != 6 else 4)
    wrong_order = module.rival_outputs(grid)["modal_precompose"]
    assert correct != wrong_intermediate
    assert correct != wrong_order


def test_verifier_rejects_bad_requests_tampering_duplicates_and_booleans():
    module = load("prototype")
    episode = module.generate(0, {"stamp_rule": "direct"}, 2, 4)
    for kind in ("label", "program", "duplicate", "boolean"):
        bad = copy.deepcopy(episode)
        if kind == "label":
            bad["test"][0]["output"][0][0] = (bad["test"][0]["output"][0][0] + 1) % 10
        elif kind == "program":
            bad["program_solution"] = module.program({"stamp_rule": "modal_postcompose"})
        elif kind == "duplicate":
            bad["test"][0] = copy.deepcopy(bad["train"][0])
        else:
            bad["train"][0]["input"][0][0] = False
        with pytest.raises(ValueError):
            module.verify_episode(bad)

    invalid = [
        (True, {"stamp_rule": "direct"}, 3, 4),
        (-1, {"stamp_rule": "direct"}, 3, 4),
        (0, {"stamp_rule": "direct"}, 1, 4),
        (0, {"stamp_rule": "direct"}, 7, 4),
        (0, {"stamp_rule": "direct"}, 3, 0),
        (0, {"stamp_rule": "direct"}, 3, 5),
        (0, {"stamp_rule": "mirror"}, 3, 4),
        (0, {"stamp_rule": "direct", "extra": 1}, 3, 4),
    ]
    for args in invalid:
        with pytest.raises(ValueError):
            module.generate(*args)
