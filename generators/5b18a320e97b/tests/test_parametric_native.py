"""Native promotion checks for the 5b18a320e97b read-direction family."""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

TASK_ID = "5b18a320e97b"
ROOT = find_root(__file__)
HOME = ROOT / "generators" / TASK_ID
PARAMETRIC = HOME / "workspace" / "parametric"


def _load(name: str):
    path = PARAMETRIC / name
    assert path.is_file(), f"missing required parametric source: {path}"
    spec = importlib.util.spec_from_file_location(
        f"_5b18a320e97b_{name.replace('.', '_')}", path
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    programs = set()
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.add(row["program_solution"])
    assert len(programs) == 1
    return next(iter(programs))


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _racket_grid(grid):
    return "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"


@pytest.fixture(scope="module")
def racket_apply():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    with RacketBridge() as bridge:
        identity = bridge.runtime_identity
        assert identity["backend"] == "racket"
        assert identity["protected"] is True

        def apply(program: str, grid):
            return bridge.eval_text(f"({wrap_rule(program)} {_racket_grid(grid)})")

        yield apply


def test_native_files_and_contract_are_complete():
    for name in (
        "adapter.py",
        "prototype.py",
        "promotion.json",
        "canonical.rkt",
        "self_audit.py",
        "build_causal_witness.py",
    ):
        assert (PARAMETRIC / name).is_file()
    contract = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": "generators/5b18a320e97b/workspace/parametric/adapter.py",
        "parameters": {"read_direction": ["forward", "reverse"]},
        "default": {"read_direction": "forward"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "resources": [
            "generators/5b18a320e97b/workspace/parametric/prototype.py",
            "generators/5b18a320e97b/workspace/parametric/canonical.rkt",
        ],
    }


def test_default_program_is_exact_canonical_and_reverse_is_one_guarded_change():
    prototype = _load("prototype.py")
    canonical = _canonical_program()
    assert prototype.program({"read_direction": "forward"}) == canonical
    reverse = prototype.program({"read_direction": "reverse"})
    assert reverse != canonical
    assert reverse.count(prototype.REVERSE_SORT_BINDING) == 1
    assert prototype.restore_canonical(reverse) == canonical
    assert hashlib.sha256((PARAMETRIC / "canonical.rkt").read_bytes()).hexdigest() == prototype.CANONICAL_SHA256


def test_settings_share_inputs_and_two_demos_identify_the_selected_rule():
    prototype = _load("prototype.py")
    forward = prototype.generate(17, {"read_direction": "forward"}, demos=2, queries=4)
    reverse = prototype.generate(17, {"read_direction": "reverse"}, demos=2, queries=4)
    assert _inputs(forward) == _inputs(reverse)
    assert prototype.fit_settings(forward["train"]) == [{"read_direction": "forward"}]
    assert prototype.fit_settings(reverse["train"]) == [{"read_direction": "reverse"}]
    assert all(a["output"] != b["output"] for a, b in zip(forward["train"], reverse["train"]))


def test_counts_are_independent_prefix_stable_and_fourth_query_is_30x30():
    prototype = _load("prototype.py")
    short = prototype.generate(23, {"read_direction": "reverse"}, demos=2, queries=1)
    medium = prototype.generate(23, {"read_direction": "reverse"}, demos=2, queries=4)
    long = prototype.generate(23, {"read_direction": "reverse"}, demos=6, queries=4)
    assert short["train"] == medium["train"] == long["train"][:2]
    assert short["test"] == medium["test"][:1]
    assert medium["test"] == long["test"]
    assert [(len(p["input"]), len(p["input"][0])) for p in long["test"]] == [
        (12, 15),
        (18, 20),
        (24, 27),
        (30, 30),
    ]
    pairs = long["train"] + long["test"]
    assert len({_freeze(pair["input"]) for pair in pairs}) == len(pairs)
    stress = long["test"][-1]["input"]
    occupied_rows = {r for r, row in enumerate(stress) if any(row)}
    occupied_cols = {c for c in range(30) if any(stress[r][c] for r in range(30))}
    assert {0, 29} <= occupied_rows
    assert {0, 29} <= occupied_cols
    assert sum(cell != 0 for row in stress for cell in row) >= 120


@pytest.mark.parametrize("seed", [0, 17])
@pytest.mark.parametrize("direction", ["forward", "reverse"])
@pytest.mark.parametrize("demos", [2, 6])
def test_generated_inputs_stay_in_canonical_grammar_and_finite_rivals_are_taught(seed, direction, demos):
    prototype = _load("prototype.py")
    generator = prototype.production_generator()
    episode = prototype.generate(seed, {"read_direction": direction}, demos=demos, queries=4)
    for pair in episode["train"] + episode["test"]:
        assert generator.self_check(pair["input"]) == []
        assert pair["output"] == prototype.mirror(pair["input"], {"read_direction": direction})
    review = prototype.self_review(episode)
    assert review["selected"] == f"intended_{direction}"
    assert review["survivors"] == [f"intended_{direction}"]
    assert review["harmful_survivors"] == []
    assert review["rivals_tested"] >= 10


def test_python_claims_match_protected_racket_for_both_settings(racket_apply):
    prototype = _load("prototype.py")
    for direction in ("forward", "reverse"):
        settings = {"read_direction": direction}
        episode = prototype.generate(0, settings, demos=3, queries=4)
        rule = prototype.program(settings)
        for pair in episode["train"] + episode["test"]:
            assert racket_apply(rule, pair["input"]) == pair["output"]


def test_public_projection_reveals_one_query_and_hashes_only_visible_bytes():
    prototype = _load("prototype.py")
    episode = prototype.generate(31, {"read_direction": "reverse"}, demos=3, queries=4)
    first = prototype.public_view(episode, 0)
    single = prototype.generate(31, {"read_direction": "reverse"}, demos=3, queries=1)
    assert first == prototype.public_view(single, 0)
    assert set(first) == {"train", "test"}
    assert len(first["train"]) == 3
    assert len(first["test"]) == 1
    assert all(set(pair) == {"input", "output"} for pair in first["train"])
    assert set(first["test"][0]) == {"input"}
    body = public_challenge_bytes(first)
    assert public_challenge_id(first) == hashlib.sha256(body).hexdigest()

    changed_private = copy.deepcopy(episode)
    changed_private["settings"] = {"private": "changed"}
    changed_private["seed"] = 999
    changed_private["program_solution"] = "private changed program"
    changed_private["test"][0]["output"] = [[9]]
    assert prototype.public_view(changed_private, 0) == first


def test_request_validation_is_strict_and_bounded():
    prototype = _load("prototype.py")
    for bad in (None, True, 0, "forward"):
        with pytest.raises(ValueError, match="settings"):
            prototype.program(bad)
    for bad in (-1, True, 1.5, "0"):
        with pytest.raises(ValueError, match="seed"):
            prototype.generate(bad, {"read_direction": "forward"}, 3, 4)
    for demos in (1, 7, True, 2.0):
        with pytest.raises(ValueError, match="demos"):
            prototype.generate(0, {"read_direction": "forward"}, demos, 4)
    for queries in (0, 5, True, 1.0):
        with pytest.raises(ValueError, match="queries"):
            prototype.generate(0, {"read_direction": "forward"}, 3, queries)


def test_reusable_self_audit_runs_protected_racket_and_writes_sorted_public_turns(tmp_path):
    audit = _load("self_audit.py")
    out = tmp_path / "audit"
    report = audit.audit(out, [0])
    assert report["status"] == "passed"
    assert report["job_count"] == 4
    assert report["racket"]["backend"] == "racket"
    assert report["racket"]["protected"] is True
    assert report["racket_evaluations"] >= 32
    assert report["public_file_count"] == 8
    names = [row["path"] for row in report["public_files"]]
    assert names == sorted(names)
    for row in report["public_files"]:
        payload = json.loads((out / row["path"]).read_text(encoding="utf-8"))
        assert len(payload["test"]) == 1
        assert set(payload["test"][0]) == {"input"}


def test_causal_witness_builder_replays_wrong_orientation_intermediate(tmp_path):
    prototype = _load("prototype.py")
    builder = _load("build_causal_witness.py")
    settings = {"read_direction": "forward"}
    rule = prototype.program(settings)
    key = json.dumps(settings, sort_keys=True, separators=(",", ":"))
    qualification = {
        "schema": "arcpuzzles-parametric-qualification-v1",
        "status": "qualified",
        "task_id": TASK_ID,
        "source_binding": {"task_id": TASK_ID, "test_binding": True},
        "programs": {key: hashlib.sha256(rule.encode()).hexdigest()},
    }
    qpath = tmp_path / "qualification.json"
    qpath.write_text(json.dumps(qualification), encoding="utf-8")
    out = tmp_path / "witness.json"
    witness = builder.build(qpath, out, seed=17)
    assert out.is_file()
    assert witness["schema"] == "arcpuzzles-sequential-dependency-witness-v1"
    assert witness["source_binding"] == qualification["source_binding"]
    assert witness["racket"] == {"backend": "racket", "protected": True}
    assert witness["step_a"] == builder.STEP_A
    assert witness["intermediate"] == builder.INTERMEDIATE
    assert witness["step_b"] == builder.STEP_B
    assert witness["why_b_depends_on_a"] == builder.WHY_B_DEPENDS_ON_A
    assert len(witness["cases"]) == 1
    case = witness["cases"][0]
    assert case["ablation"] == "wrong_intermediate"
    assert case["intermediate_value"]["orientation"] == "vertical"
    assert case["output"] != case["counterfactual_output"]
    assert case["changed_cells"] > 0
    assert hashlib.sha256(case["program"].encode()).hexdigest() == qualification["programs"][key]
