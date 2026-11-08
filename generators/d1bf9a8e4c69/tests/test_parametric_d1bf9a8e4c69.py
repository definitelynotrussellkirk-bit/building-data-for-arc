"""Native parametric regressions for d1bf9a8e4c69.

The default setting must remain byte-identical to the selected canonical Racket
rule.  The alternative composes that corner extraction with an input-dependent
nearest-corner bridge while keeping inputs matched across settings.
"""
from __future__ import annotations

from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

TASK_ID = "d1bf9a8e4c69"
_SOURCE = Path(__file__).resolve()
_RUNTIME = next(
    candidate / "shared" / "runtime"
    for candidate in _SOURCE.parents
    if (candidate / "shared" / "runtime" / "reviewer_support.py").is_file()
)
sys.path.insert(0, str(_RUNTIME))
from reviewer_support import find_root, public_challenge_bytes, public_challenge_id  # noqa: E402

REPO = find_root(__file__)
HOME = REPO / "generators" / TASK_ID / "workspace" / "parametric"
ADAPTER_PATH = HOME / "adapter.py"
PROTOTYPE_PATH = HOME / "prototype.py"
PROMOTION_PATH = HOME / "promotion.json"
from puzzle_generators.rule_wrap import wrap_rule  # noqa: E402


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _canonical_program() -> str:
    for line in (REPO / "shared" / "data" / "canonical" / "puzzles.jsonl").read_text().splitlines():
        row = json.loads(line)
        if row.get("task_id") == TASK_ID:
            return row["program_solution"]
    raise AssertionError("canonical row missing")


def _modules():
    return (
        _load(PROTOTYPE_PATH, "_test_d1bf9a8e4c69_parametric_prototype"),
        _load(ADAPTER_PATH, "_test_d1bf9a8e4c69_parametric_adapter"),
    )


def _inputs(episode):
    return [pair["input"] for pair in episode["train"] + episode["test"]]


def _key(grid):
    return json.dumps(grid, separators=(",", ":"))


def test_parametric_sources_exist_and_contract_is_finite():
    assert ADAPTER_PATH.is_file()
    assert PROTOTYPE_PATH.is_file()
    assert PROMOTION_PATH.is_file()
    contract = json.loads(PROMOTION_PATH.read_text())
    assert contract == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"finish": ["corners_only", "nearest_corner_bridge"]},
        "default": {"finish": "corners_only"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 3,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/prototype.py",
            f"generators/{TASK_ID}/workspace/parametric/rules/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/rules/nearest_corner_bridge.rkt",
        ],
    }


def test_default_program_is_exact_canonical_and_all_programs_wrap():
    _prototype, adapter = _modules()
    canonical = _canonical_program()
    assert adapter.program({"finish": "corners_only"}).encode() == canonical.encode()
    assert (HOME / "rules" / "canonical.rkt").read_bytes() == canonical.encode()
    for finish in adapter.FINISHES:
        program = adapter.program({"finish": finish})
        assert program.lstrip().startswith("(rule!")
        wrapped = wrap_rule(program)
        assert isinstance(wrapped, str) and wrapped.strip()


def test_generation_is_matched_deterministic_prefix_stable_and_distinct():
    _prototype, adapter = _modules()
    settings = [{"finish": finish} for finish in adapter.FINISHES]
    for seed in (0, 17, 91):
        episodes = [adapter.generate(seed, deepcopy(setting), demos=6, queries=4) for setting in settings]
        assert episodes[0] == adapter.generate(seed, settings[0], demos=6, queries=4)
        assert [_key(g) for g in _inputs(episodes[0])] == [_key(g) for g in _inputs(episodes[1])]
        assert len({_key(g) for g in _inputs(episodes[0])}) == 10
        for setting, full in zip(settings, episodes, strict=True):
            small = adapter.generate(seed, deepcopy(setting), demos=2, queries=1)
            middle = adapter.generate(seed, deepcopy(setting), demos=3, queries=2)
            assert small["train"] == full["train"][:2]
            assert small["test"] == full["test"][:1]
            assert middle["train"] == full["train"][:3]
            assert middle["test"] == full["test"][:2]
            assert full["program_solution"] == adapter.program(setting)


def test_every_supported_demo_identifies_setting_and_minimum_prefix_refutes_rivals():
    prototype, adapter = _modules()
    for seed in (0, 17, 91):
        canonical = adapter.generate(seed, {"finish": "corners_only"}, demos=6, queries=4)
        bridge = adapter.generate(seed, {"finish": "nearest_corner_bridge"}, demos=6, queries=4)
        assert all(a["output"] != b["output"] for a, b in zip(canonical["train"], bridge["train"]))
        for finish, episode in (("corners_only", canonical), ("nearest_corner_bridge", bridge)):
            demos = episode["train"][:2]
            survivors = []
            for name, solver in prototype.RIVAL_SOLVERS.items():
                if all(solver(pair["input"]) == pair["output"] for pair in demos):
                    survivors.append(name)
            assert survivors == [finish], (seed, finish, survivors)


def test_grammar_covers_object_identity_orientations_and_substantive_30x30():
    prototype, adapter = _modules()
    episode = adapter.generate(17, {"finish": "nearest_corner_bridge"}, demos=6, queries=4)
    all_inputs = _inputs(episode)
    states = [prototype.corner_state(grid) for grid in all_inputs]
    assert {state["orientation"] for state in states} >= {"down_right", "down_left", "horizontal", "vertical"}
    assert {len(state["groups"]) for state in states} >= {2, 3, 4}
    assert any(state["has_repeated_color_components"] for state in states)
    large = episode["test"][3]
    assert len(large["input"]) == len(large["input"][0]) == 30
    assert sum(value != 0 for row in large["input"] for value in row) >= 70
    changed = sum(a != b for ra, rb in zip(large["input"], large["output"], strict=True) for a, b in zip(ra, rb, strict=True))
    assert changed >= 80


def test_causal_intermediate_changes_when_original_cells_replace_corner_candidates():
    prototype, adapter = _modules()
    episode = adapter.generate(17, {"finish": "nearest_corner_bridge"}, demos=3, queries=4)
    witnesses = []
    for pair in episode["train"] + episode["test"]:
        intended = prototype.solve(pair["input"], "nearest_corner_bridge")
        wrong = prototype.wrong_intermediate_solve(pair["input"])
        if intended != wrong:
            state = prototype.corner_state(pair["input"])
            witnesses.append((pair, state, intended, wrong))
    assert witnesses
    pair, state, intended, wrong = witnesses[0]
    assert state["nearest_corner_pair"] != state["nearest_original_pair"]
    assert pair["output"] == intended
    assert sum(a != b for ra, rb in zip(intended, wrong, strict=True) for a, b in zip(ra, rb, strict=True)) >= 2


def test_public_sequential_reveals_hide_settings_programs_answers_and_future_queries():
    _prototype, adapter = _modules()
    episode = adapter.generate(17, {"finish": "nearest_corner_bridge"}, demos=3, queries=4)
    ids = []
    for index, query in enumerate(episode["test"]):
        public = {"train": deepcopy(episode["train"]), "test": [{"input": deepcopy(query["input"])}]}
        payload = public_challenge_bytes(public)
        decoded = json.loads(payload)
        assert decoded == public
        assert "finish" not in payload.decode()
        assert "program" not in payload.decode()
        assert query["output"] not in decoded["test"]
        assert len(decoded["test"]) == 1
        ids.append(public_challenge_id(public))
        mutated = deepcopy(episode)
        mutated["test"][index]["output"][0][0] = (mutated["test"][index]["output"][0][0] + 1) % 10
        same_public = {"train": deepcopy(mutated["train"]), "test": [{"input": deepcopy(mutated["test"][index]["input"])}]}
        assert public_challenge_id(same_public) == ids[-1]
    assert len(ids) == len(set(ids)) == 4


@pytest.mark.parametrize(
    "settings",
    [
        {}, {"finish": "unknown"}, {"finish": 1}, {"finish": "corners_only", "extra": 1}, [], None,
    ],
)
def test_invalid_settings_fail_loudly(settings):
    _prototype, adapter = _modules()
    with pytest.raises(ValueError):
        adapter.program(settings)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"seed": True, "demos": 2, "queries": 1},
        {"seed": -1, "demos": 2, "queries": 1},
        {"seed": 0, "demos": 1, "queries": 1},
        {"seed": 0, "demos": 7, "queries": 1},
        {"seed": 0, "demos": 2, "queries": 0},
        {"seed": 0, "demos": 2, "queries": 5},
    ],
)
def test_invalid_request_counts_fail_loudly(kwargs):
    _prototype, adapter = _modules()
    with pytest.raises(ValueError):
        adapter.generate(settings={"finish": "corners_only"}, **kwargs)


def test_production_generator_bytes_remain_unchanged():
    path = REPO / "generators" / TASK_ID / "generator.py"
    assert hashlib.sha256(path.read_bytes()).hexdigest() == "458e1558ab9ada63796e1b5ab6a9601f4bd28094c0687140aedf17390105c86b"


def test_per_color_rival_preserves_first_seen_component_color_order():
    prototype, _adapter = _modules()
    grid = [
        [7, 7, 0, 2, 2],
        [7, 0, 0, 2, 0],
        [0, 0, 0, 0, 0],
        [7, 7, 0, 0, 0],
        [7, 0, 0, 0, 0],
    ]
    groups = prototype._corner_groups(grid, merge_by_color=True)
    assert [group["color"] for group in groups] == [7, 2]


def test_self_audit_python_core_refutes_rivals_and_exports_causal_case():
    audit_path = HOME / "self_audit.py"
    assert audit_path.is_file()
    audit = _load(audit_path, "_test_d1bf9a8e4c69_self_audit")
    report = audit.run_audit(
        seeds=[0],
        demo_counts=[2],
        queries=4,
        apply_program=audit.python_apply,
        runtime_identity={"backend": "python-mirror", "protected": False},
    )
    assert report["passed"] is True
    assert report["job_count"] == 2
    assert report["finding_count"] == 0
    assert {tuple(job["survivors"]) for job in report["jobs"]} == {
        ("corners_only",),
        ("nearest_corner_bridge",),
    }
    case = report["causal_case"]
    assert case["settings"] == {"finish": "nearest_corner_bridge"}
    assert case["program"] == audit.programs()["nearest_corner_bridge"]
    assert case["counterfactual_program"] == audit.programs()["nearest_original_cells"]
    assert case["ablation"] == "wrong_intermediate"
    assert case["output"] != case["counterfactual_output"]
    assert case["changed_cells"] >= 2
    assert case["intermediate_value"]["selected_corner_pair"] != case["intermediate_value"]["counterfactual_original_pair"]
