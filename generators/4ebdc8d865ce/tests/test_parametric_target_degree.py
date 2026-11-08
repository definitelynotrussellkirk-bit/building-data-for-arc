from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import random

import pytest

from reviewer_support import find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "4ebdc8d865ce"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"
PROTOTYPE = PARAMETRIC / "prototype.py"
ADAPTER = PARAMETRIC / "adapter.py"
PROMOTION = PARAMETRIC / "promotion.json"
CANONICAL = PARAMETRIC / "canonical.rkt"


def _load(path: Path, name: str):
    assert path.is_file(), f"missing required file: {path}"
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def prototype():
    return _load(PROTOTYPE, "_task_4ebdc8d865ce_parametric_prototype_test")


def adapter():
    return _load(ADAPTER, "_task_4ebdc8d865ce_parametric_adapter_test")


def canonical_program() -> str:
    for line in (ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl").read_text(
        encoding="utf-8"
    ).splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical task row missing")


def _racket_grid(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


@pytest.fixture(scope="module")
def racket_apply():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    with RacketBridge() as bridge:
        assert bridge.runtime_identity["backend"] == "racket"
        assert bridge.runtime_identity["protected"] is True

        def apply(program: str, grid):
            return bridge.eval_text(f"({wrap_rule(program)} {_racket_grid(grid)})")

        yield apply


def test_default_program_is_exact_canonical_authority():
    module = prototype()
    exact = canonical_program()
    assert module.program({"target_degree": 0}) == exact
    assert CANONICAL.read_bytes() == exact.encode("utf-8")


def test_literal_fixture_recolors_selected_orthogonal_degree_only():
    module = prototype()
    grid = [
        [2, 0, 0, 2, 2, 0, 0],
        [0, 2, 0, 0, 0, 0, 2],
        [0, 0, 0, 2, 2, 2, 2],
        [2, 2, 0, 0, 0, 0, 2],
        [0, 0, 0, 2, 2, 0, 0],
    ]
    degree0 = module.transform(grid, {"target_degree": 0})
    degree1 = module.transform(grid, {"target_degree": 1})
    assert degree0[0][0] == 1 and degree0[1][1] == 1
    assert degree1[0][3:5] == [1, 1]
    assert degree1[2][3] == 1 and degree1[2][6] == 2
    assert degree0 != degree1
    assert grid[0][0] == 2


def test_settings_share_inputs_and_two_demos_eliminate_declared_rivals():
    module = prototype()
    canonical = module.generate(17, {"target_degree": 0}, demos=2, queries=4)
    endpoints = module.generate(17, {"target_degree": 1}, demos=2, queries=4)
    inputs = lambda ep: [pair["input"] for pair in ep["train"] + ep["test"]]
    assert inputs(canonical) == inputs(endpoints)
    assert module.fit_candidates(canonical["train"]) == ["target_degree_0"]
    assert module.fit_candidates(endpoints["train"]) == ["target_degree_1"]
    assert all(a["output"] != b["output"] for a, b in zip(canonical["test"], endpoints["test"]))


def test_demo_and_query_prefixes_are_independent_and_stable():
    module = prototype()
    short = module.generate(23, {"target_degree": 0}, demos=2, queries=1)
    long = module.generate(23, {"target_degree": 0}, demos=6, queries=4)
    assert short["train"] == long["train"][:2]
    assert short["test"] == long["test"][:1]
    same_queries = module.generate(23, {"target_degree": 0}, demos=2, queries=4)
    assert same_queries["test"] == long["test"]


def test_four_queries_are_distinct_and_include_substantive_30x30_boundary_case():
    module = prototype()
    episode = module.generate(31, {"target_degree": 1}, demos=6, queries=4)
    serial = [json.dumps(pair["input"], separators=(",", ":")) for pair in episode["train"] + episode["test"]]
    assert len(serial) == len(set(serial))
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes == list(module.QUERY_PROFILES[:4])
    stress = episode["test"][-1]["input"]
    assert (len(stress), len(stress[0])) == (30, 30)
    foreground = [(r, c) for r, row in enumerate(stress) for c, value in enumerate(row) if value == 2]
    assert len(foreground) >= 80
    assert any(r in (0, 29) for r, _ in foreground)
    assert any(c in (0, 29) for _, c in foreground)
    changed = sum(
        a != b
        for row_a, row_b in zip(stress, episode["test"][-1]["output"])
        for a, b in zip(row_a, row_b)
    )
    assert changed >= 20


def test_causal_witness_wrong_eight_neighbor_intermediate_changes_output():
    module = prototype()
    witness = module.causal_witness()
    assert witness["setting"] == {"target_degree": 0}
    assert witness["correct_degree_map"] != witness["wrong_eight_neighbor_degree_map"]
    assert witness["correct_output"] != witness["wrong_output"]
    assert witness["difference_cells"] >= 2


def test_retained_degree_capsule_contract_is_bounded_and_exact():
    module = prototype()
    thin = _load(PARAMETRIC / "degree_adapter.py", "_retained_degree_adapter_test")
    assert thin.program({"target_degree": 0}) == canonical_program()
    assert thin.generate(5, {"target_degree": 1}, 2, 4) == module.generate(
        5, {"target_degree": 1}, 2, 4
    )
    assert json.loads((PARAMETRIC / "degree-promotion.json").read_text(encoding="utf-8")) == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"target_degree": [0, 1]},
        "default": {"target_degree": 0},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
        ],
    }


def test_public_projection_hides_settings_program_answers_and_future_queries():
    module = prototype()
    episode = module.generate(41, {"target_degree": 1}, demos=3, queries=4)
    original = public_challenge_bytes(episode)
    original_id = public_challenge_id(episode)
    mutated = copy.deepcopy(episode)
    mutated["settings"] = {"private": "changed"}
    mutated["seed"] = 999
    mutated["program_solution"] = "private changed"
    mutated["test"][0]["output"] = [[9]]
    assert public_challenge_bytes(mutated) == original
    assert public_challenge_id(mutated) == original_id
    visible = json.loads(original)
    assert all(set(pair) == {"input"} for pair in visible["test"])
    assert hashlib.sha256(original).hexdigest() == original_id


def test_protected_racket_matches_labels_and_causal_rival(racket_apply):
    module = prototype()
    before = random.getstate()
    for setting in module.SETTINGS:
        for seed, demos in ((0, 2), (17, 6)):
            episode = module.generate(seed, setting, demos=demos, queries=4)
            for pair in episode["train"] + episode["test"]:
                assert racket_apply(module.program(setting), pair["input"]) == pair["output"]
    witness = module.causal_witness()
    assert racket_apply(module.program(witness["setting"]), witness["input"]) == witness["correct_output"]
    assert racket_apply(module.EIGHT_NEIGHBOR_DEGREE_ZERO_PROGRAM, witness["input"]) == witness["wrong_output"]
    assert random.getstate() == before



def test_reusable_self_audit_core_reports_bounded_success():
    module = prototype()
    audit = _load(PARAMETRIC / "self_audit.py", "_task_4ebdc8d865ce_self_audit_test")

    def fake_apply(program, grid):
        if program == module.EIGHT_NEIGHBOR_DEGREE_ZERO_PROGRAM:
            values = module.degree_map(grid, diagonals=True)
            return module._paint_by_map(grid, values, lambda degree, _r, _c: degree == 0)
        for setting in module.SETTINGS:
            if program == module.program(setting):
                return module.transform(grid, setting)
        raise AssertionError("unexpected program")

    report = audit.run_audit(fake_apply, backend={"backend": "test-double", "protected": False})
    assert report["status"] == "pass"
    assert report["jobs"] == 4
    assert report["label_evaluations"] == 32
    assert report["causal_witness"]["difference_cells"] >= 2
    assert report["stress"]["shape"] == [30, 30]
    assert report["finite_rivals"]["survivors"] == {
        "target_degree_0": ["target_degree_0"],
        "target_degree_1": ["target_degree_1"],
    }

def test_invalid_requests_fail_loudly_without_silent_shortening():
    module = prototype()
    bad_settings = [None, {}, {"target_degree": 2}, {"target_degree": True}, {"target_degree": 0, "extra": 1}]
    for settings in bad_settings:
        with pytest.raises((TypeError, ValueError)):
            module.generate(0, settings, demos=2, queries=4)
    for args in [(-1, {"target_degree": 0}, 2, 4), (0, {"target_degree": 0}, 1, 4), (0, {"target_degree": 0}, 7, 4), (0, {"target_degree": 0}, 2, 0), (0, {"target_degree": 0}, 2, 5)]:
        with pytest.raises(ValueError):
            module.generate(*args)
