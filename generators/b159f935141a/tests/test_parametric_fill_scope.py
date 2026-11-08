from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"
CANONICAL = """(rule!
  (for*/fold ([out g])
             ([r (in-range 1 (- (rows g) 1))]
              [c (in-range 1 (- (cols g) 1))])
    (let ((vals (list (at g (- r 1) c) (at g (+ r 1) c) (at g r (- c 1)) (at g r (+ c 1)))))
      (if (and (= (at g r c) 0)
               (not (= (first vals) 0))
               (all? (lambda (v) (= v (first vals))) vals))
          (set-cell out r c (first vals))
          out))))"""


def load():
    path = HOME / "prototype.py"
    spec = importlib.util.spec_from_file_location("b159_parametric", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_canonical_authority():
    module = load()
    assert module.program({"fill_scope": "all_qualifying"}) == CANONICAL


def test_settings_share_inputs_and_each_demo_distinguishes_scope():
    module = load()
    all_centers = module.generate_episode(17, fill_scope="all_qualifying", demos=3, queries=4)
    rarest = module.generate_episode(17, fill_scope="rarest_color_only", demos=3, queries=4)
    assert inputs(all_centers) == inputs(rarest)
    for left, right in zip(all_centers["train"], rarest["train"]):
        assert left["output"] != right["output"]


def test_requested_counts_distinctness_and_30x30_stress():
    module = load()
    for demos in range(2, 7):
        episode = module.generate_episode(41, fill_scope="rarest_color_only", demos=demos, queries=4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        serialized = [json.dumps(grid) for grid in inputs(episode)]
        assert len(serialized) == len(set(serialized))
    episode = module.generate_episode(41, fill_scope="all_qualifying", demos=3, queries=4)
    large = [grid for grid in inputs(episode) if len(grid) == 30 and len(grid[0]) == 30]
    assert len(large) == 1
    analysis = module.analyze(large[0])
    assert len(analysis["qualifying_centers"]) >= 12
    assert len(analysis["decoy_centers"]) >= 6


def test_python_labels_and_wrong_intermediate_witness():
    module = load()
    for scope in module.FILL_SCOPES:
        episode = module.generate_episode(0, fill_scope=scope, demos=3, queries=4)
        for split in ("train", "test"):
            for pair in episode[split]:
                assert pair["output"] == module.apply_mode(pair["input"], scope)
    case = module.causal_case(0)
    assert case["settings"] == {"fill_scope": "rarest_color_only"}
    assert case["output"] != case["counterfactual_output"]
    assert case["ablation"] == "wrong_intermediate"
    counts = case["intermediate_value"]["counts_by_color"]
    assert counts[str(case["intermediate_value"]["rarest_color"])] == min(counts.values())
    assert counts[str(case["intermediate_value"]["most_common_color"])] == max(counts.values())


@pytest.mark.parametrize(
    "settings,demos,queries",
    [
        ({}, 3, 4),
        ({"fill_scope": "unknown"}, 3, 4),
        ({"fill_scope": "all_qualifying", "extra": 1}, 3, 4),
        ({"fill_scope": "all_qualifying"}, 1, 4),
        ({"fill_scope": "all_qualifying"}, 3, 5),
    ],
)
def test_invalid_requests_fail_loudly(settings, demos, queries):
    module = load()
    with pytest.raises((TypeError, ValueError)):
        values = module.validate_settings(settings)
        module.generate_episode(0, fill_scope=values["fill_scope"], demos=demos, queries=queries)


@pytest.fixture(scope="module")
def protected_racket_apply():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    with pytest.MonkeyPatch.context() as patch:
        patch.setenv("ARC_REPL_SKIP_BANK_HELPERS", "1")
        with RacketBridge(timeout=20, max_calls_before_restart=128) as bridge:
            assert bridge.runtime_identity["backend"] == "racket"
            assert bridge.runtime_identity["protected"] is True

            def apply(program, grid):
                bridge.define_grid("b159-parametric-test-grid", grid)
                return bridge.eval_text(
                    "(" + wrap_rule(program) + " b159-parametric-test-grid)"
                )

            yield apply


def test_alternative_and_counterfactual_programs_match_python_on_protected_racket(protected_racket_apply):
    module = load()
    for scope in module.FILL_SCOPES:
        episode = module.generate_episode(17, fill_scope=scope, demos=2, queries=1)
        for pair in episode["train"] + episode["test"]:
            assert protected_racket_apply(module.program({"fill_scope": scope}), pair["input"]) == pair["output"]
    case = module.causal_case(17)
    assert protected_racket_apply(case["counterfactual_program"], case["input"]) == case["counterfactual_output"]


def _apply_color_rival(module, grid, selector):
    from copy import deepcopy

    info = module.analyze(grid)
    selected = set(selector(info))
    out = deepcopy(grid)
    for r, c, color in info["qualifying_centers"]:
        if color in selected:
            out[r][c] = color
    return out


def test_minimum_demos_refute_singleton_numeric_and_scan_order_shortcuts():
    module = load()
    for seed in range(64):
        episode = module.generate_episode(seed, fill_scope="rarest_color_only", demos=2, queries=4)
        rivals = {
            "singleton_only": lambda info: [color for color, count in info["counts_by_color"].items() if count == 1],
            "lowest_numeric_color": lambda info: [min(info["counts_by_color"])],
            "highest_numeric_color": lambda info: [max(info["counts_by_color"])],
            "first_qualifying_color": lambda info: [info["qualifying_centers"][0][2]],
            "last_qualifying_color": lambda info: [info["qualifying_centers"][-1][2]],
            "most_common_color": lambda info: [info["most_common_color"]],
        }
        survivors = [
            name
            for name, selector in rivals.items()
            if all(_apply_color_rival(module, pair["input"], selector) == pair["output"] for pair in episode["train"])
        ]
        assert survivors == [], (seed, survivors)
        query_info = module.analyze(episode["test"][0]["input"])
        assert min(query_info["counts_by_color"].values()) > 1


def test_rival_audit_tool_reports_no_surviving_shortcut():
    path = HOME / "rival_audit.py"
    spec = importlib.util.spec_from_file_location("b159_rival_audit", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.run(seed_count=32)
    assert report["status"] == "pass"
    assert report["harmful_survivors"] == []
    assert report["all_demo_survivors"] == []
