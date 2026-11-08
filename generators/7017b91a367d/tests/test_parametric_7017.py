"""Contract and causal tests for the overlap-map flood parametric family."""
from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAM = HOME / "workspace" / "parametric"


def _load():
    path = PARAM / "prototype.py"
    spec = importlib.util.spec_from_file_location("overlap_parametric", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_missing_implementation_red_gate():
    assert (PARAM / "prototype.py").is_file(), "parametric prototype has not been implemented"


def test_exact_default_program_and_distinct_flood_program():
    mod = _load()
    canonical = "(rule! (let ((dummy 0)) (define (t13c-panel grid idx top-rows) (subgrid grid 0 (* idx 6) (- top-rows 1) (+ (* idx 6) 4))) (let ((panels (map (lambda (i) (t13c-panel g i (rows g))) (range 3)))) (grid-from-fn 5 5 (lambda (r c) (let ((cnt (count-where (lambda (panel) (not (= (at panel r c) 0))) panels))) (cond ((= cnt 0) 0) ((= cnt 1) 2) ((= cnt 2) 4) (else 8))))))))"
    assert mod.program({"overlap_policy": "count_map"}) == canonical
    assert mod.program({"overlap_policy": "flood_from_triples"}) != canonical


@pytest.mark.parametrize("demos", [2, 3, 6])
@pytest.mark.parametrize("queries", [1, 4])
def test_count_bounds_prefix_stability_and_matched_inputs(demos, queries):
    mod = _load()
    a = mod.generate(17, {"overlap_policy": "count_map"}, demos, queries)
    b = mod.generate(17, {"overlap_policy": "flood_from_triples"}, demos, queries)
    assert len(a["train"]) == len(b["train"]) == demos
    assert len(a["test"]) == len(b["test"]) == queries
    assert [p["input"] for p in a["train"] + a["test"]] == [p["input"] for p in b["train"] + b["test"]]
    assert len({str(p["input"]) for p in a["train"] + a["test"]}) == demos + queries
    prefix = mod.generate(17, {"overlap_policy": "count_map"}, 2, 1)
    assert prefix["train"] == a["train"][:2]
    assert prefix["test"] == a["test"][:1]
    for settings, episode in [({"overlap_policy": "count_map"}, a), ({"overlap_policy": "flood_from_triples"}, b)]:
        for pair in episode["train"] + episode["test"]:
            assert (len(pair["input"]), len(pair["input"][0])) == (5, 17)
            assert (len(pair["output"]), len(pair["output"][0])) == (5, 5)
            assert pair["output"] == mod.transform(pair["input"], settings)


def test_flood_uses_count_map_connectivity_and_singles_counterfactual_changes_result():
    mod = _load()
    grid = mod.scene(0, "demo", 0)
    counts = mod.count_map(grid)
    flooded = mod.transform(grid, {"overlap_policy": "flood_from_triples"})
    wrong = mod.transform_flood_through_singles(grid)
    assert any(value == 8 for row in counts for value in row)
    assert any(counts[r][c] == 4 and flooded[r][c] == 8 for r in range(5) for c in range(5))
    assert any(counts[r][c] == 4 and flooded[r][c] == 4 for r in range(5) for c in range(5))
    assert wrong != flooded


def test_panels_remain_connected_and_each_scene_teaches_both_stages():
    mod = _load()
    for seed in (0, 17, 97):
        for domain in ("demo", "query"):
            for index in range(6 if domain == "demo" else 4):
                grid = mod.scene(seed, domain, index)
                facts = mod.features(grid)
                assert all(facts["panel_connected"])
                assert facts["reachable_double_cells"] >= 1
                assert facts["unreachable_double_cells"] >= 1
                assert facts["single_cells"] >= 1


def test_two_demonstrations_identify_setting_and_refute_declared_rivals():
    mod = _load()
    for seed in (0, 17, 97):
        for policy in mod.POLICIES:
            episode = mod.generate(seed, {"overlap_policy": policy}, 2, 4)
            report = mod.teaching_check(episode, {"overlap_policy": policy})
            assert report["survivors"] == [{"overlap_policy": policy}]
            assert report["surviving_rivals"] == []


def test_fixed_panel_domain_is_documented_instead_of_fake_30x30_padding():
    mod = _load()
    assert mod.DOMAIN_LIMIT == "5x17 input (three aligned 5x5 panels); 5x5 output"
    episode = mod.generate(97, {"overlap_policy": "flood_from_triples"}, 6, 4)
    assert all((len(p["input"]), len(p["input"][0])) == (5, 17) for p in episode["train"] + episode["test"])


@pytest.mark.parametrize(
    "args",
    [
        (-1, {"overlap_policy": "count_map"}, 2, 4),
        (0, {"overlap_policy": "bad"}, 2, 4),
        (0, {"extra": "count_map"}, 2, 4),
        (0, {"overlap_policy": "count_map"}, 1, 4),
        (0, {"overlap_policy": "count_map"}, 7, 4),
        (0, {"overlap_policy": "count_map"}, 2, 0),
        (0, {"overlap_policy": "count_map"}, 2, 5),
    ],
)
def test_rejects_invalid_requests(args):
    mod = _load()
    with pytest.raises(ValueError):
        mod.generate(*args)


def test_reusable_audit_tool_covers_boundaries_and_rivals_without_racket():
    path = PARAM / "audit.py"
    spec = importlib.util.spec_from_file_location("overlap_audit", path)
    assert spec and spec.loader
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    report = audit.build_report(seeds=(0, 17), use_racket=False)
    assert report["status"] == "PASS"
    assert report["requests"] == 2 * 2 * 2 * 2
    assert report["surviving_rivals"] == []
