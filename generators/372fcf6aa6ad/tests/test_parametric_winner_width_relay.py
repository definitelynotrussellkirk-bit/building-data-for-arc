from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import random

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "372fcf6aa6ad"
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
ADAPTER_PATH = PARAMETRIC / "adapter.py"
VERIFY_PATH = PARAMETRIC / "verify.py"
COUNTERFACTUAL_PATH = PARAMETRIC / "wrong_winner_height.rkt"
MODES = ("canonical", "winner_width_relay")


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def adapter():
    return _load(ADAPTER_PATH, "_372_parametric_adapter")


def verifier():
    return _load(VERIFY_PATH, "_372_parametric_verify")


def canonical_program() -> str:
    programs = {
        row["program_solution"]
        for line in canonical_path(find_root(__file__)).read_text(encoding="utf-8").splitlines()
        if (row := json.loads(line)).get("task_id") == TASK_ID
    }
    assert len(programs) == 1
    return programs.pop()


@pytest.fixture(scope="module")
def racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    with RacketBridge(timeout=20) as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True
        counter = 0

        def apply(program: str, grid: list[list[int]]) -> list[list[int]]:
            nonlocal counter
            counter += 1
            name = f"winner-width-{counter}"
            bridge.define_grid(name, grid)
            return bridge.eval_text(f"({wrap_rule(program)} {name})")

        yield apply


def first_turn(episode: dict) -> dict:
    return {"train": episode["train"], "test": [{"input": episode["test"][0]["input"]}]}


def test_default_program_is_exact_canonical_and_relay_is_distinct():
    module = adapter()
    canonical = module.program({"mode": "canonical"})
    relay = module.program({"mode": "winner_width_relay"})
    assert canonical == canonical_program()
    assert relay != canonical
    assert relay.startswith("(rule!")
    assert hashlib.sha256(relay.encode()).hexdigest() != hashlib.sha256(canonical.encode()).hexdigest()


@pytest.mark.parametrize("mode", MODES)
def test_generation_is_setting_neutral_deterministic_prefix_stable_and_rng_safe(mode):
    module = adapter()
    before = random.getstate()
    episode = module.generate(17, {"mode": mode}, demos=2, queries=4)
    other_mode = MODES[1] if mode == MODES[0] else MODES[0]
    other = module.generate(17, {"mode": other_mode}, demos=2, queries=4)
    one = module.generate(17, {"mode": mode}, demos=2, queries=1)
    six = module.generate(17, {"mode": mode}, demos=6, queries=4)

    inputs = lambda value: [p["input"] for p in value["train"] + value["test"]]
    assert inputs(episode) == inputs(other)
    assert episode == module.generate(17, {"mode": mode}, demos=2, queries=4)
    assert random.getstate() == before
    assert episode["train"] == six["train"][:2]
    assert episode["test"] == six["test"]
    assert episode["train"] == one["train"]
    assert episode["test"][0] == one["test"][0]
    signatures = [json.dumps(grid, separators=(",", ":")) for grid in inputs(six)]
    assert len(signatures) == len(set(signatures)) == 10


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("demos,queries", [(2, 1), (2, 4), (3, 4), (6, 1), (6, 4)])
def test_supported_count_boundaries_are_identifiable(mode, demos, queries):
    module = adapter()
    episode = module.generate(3, {"mode": mode}, demos=demos, queries=queries)
    certificate = module.certificate(episode["train"], [p["input"] for p in episode["test"]])
    assert certificate["survivors"] == [mode]
    assert certificate["query_changing_survivors"] == []


def test_all_claims_match_protected_racket_and_wrong_intermediate_changes_output(racket):
    module = adapter()
    for mode in MODES:
        episode = module.generate(0, {"mode": mode}, demos=3, queries=4)
        program = module.program({"mode": mode})
        for pair in episode["train"] + episode["test"]:
            assert racket(program, pair["input"]) == pair["output"]

    relay_episode = module.generate(0, {"mode": "winner_width_relay"}, demos=3, queries=4)
    witness = next(
        pair
        for pair in relay_episode["test"] + relay_episode["train"]
        if module.explain_dependency(pair["input"])["selector"]
        != module.explain_dependency(pair["input"])["counterfactual_selector"]
    )
    correct = racket(module.program({"mode": "winner_width_relay"}), witness["input"])
    wrong = racket(COUNTERFACTUAL_PATH.read_text(encoding="utf-8"), witness["input"])
    assert correct == witness["output"]
    assert wrong == module.transform(witness["input"], "winner_height_clamped")
    assert wrong != correct


def test_relay_covers_all_selectors_and_repairs_size_before_holes_shortcut():
    module = adapter()
    selectors = set()
    size_first_disagreements = 0
    for seed in range(8):
        episode = module.generate(seed, {"mode": "winner_width_relay"}, demos=6, queries=4)
        for pair in episode["train"] + episode["test"]:
            explanation = module.explain_dependency(pair["input"])
            selectors.add(explanation["selector"])
            size_first_disagreements += (
                module.transform(pair["input"], "size_first_relay") != pair["output"]
            )
    assert selectors == {1, 2, 3}
    assert size_first_disagreements > 0


def test_fourth_query_is_substantive_30x30_and_touches_all_boundaries():
    module = adapter()
    pair = module.generate(91, {"mode": "winner_width_relay"}, demos=3, queries=4)["test"][3]
    grid = pair["input"]
    occupied = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value]
    assert (len(grid), len(grid[0])) == (30, 30)
    assert len(occupied) >= 90
    assert len({value for _, _, value in occupied}) == 5
    assert any(r == 0 for r, _, _ in occupied)
    assert any(r == 29 for r, _, _ in occupied)
    assert any(c == 0 for _, c, _ in occupied)
    assert any(c == 29 for _, c, _ in occupied)
    assert pair["output"] != module.transform(grid, "canonical")


def test_public_first_turn_hides_private_data_and_matches_one_query_call():
    module = adapter()
    episode = module.generate(5, {"mode": "winner_width_relay"}, demos=3, queries=4)
    visible = first_turn(episode)
    raw = public_challenge_bytes(visible)
    assert json.loads(raw) == visible
    assert b"program_solution" not in raw and b"settings" not in raw
    assert public_challenge_id(visible) == hashlib.sha256(raw).hexdigest()
    one = module.generate(5, {"mode": "winner_width_relay"}, demos=3, queries=1)
    assert public_challenge_bytes(one) == raw


@pytest.mark.parametrize(
    "seed,settings,demos,queries",
    [
        (True, {"mode": "canonical"}, 2, 4),
        (-1, {"mode": "canonical"}, 2, 4),
        (2**63, {"mode": "canonical"}, 2, 4),
        (0, {"mode": "wrong"}, 2, 4),
        (0, {"mode": "canonical", "extra": 1}, 2, 4),
        (0, {"mode": "canonical"}, 1, 4),
        (0, {"mode": "canonical"}, 7, 4),
        (0, {"mode": "canonical"}, 2, 0),
        (0, {"mode": "canonical"}, 2, 5),
        (0, {"mode": "canonical"}, 2, True),
    ],
)
def test_bad_requests_fail_explicitly(seed, settings, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        adapter().generate(seed, settings, demos, queries)


def test_bounded_verifier_runs_racket_and_named_rivals(tmp_path):
    report = verifier().run_audit(seed_start=0, seed_count=3, racket_seed_count=1)
    assert report["status"] == "passed"
    assert report["episodes"] == 6
    assert report["lesson_failures"] == []
    assert report["racket_failures"] == []
    assert report["selector_values"] == [1, 2, 3]
    assert report["racket_evaluations"] >= 15
    path = tmp_path / "audit.json"
    verifier().write_report(path, report)
    assert json.loads(path.read_text()) == report
