from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

HOME = Path(__file__).resolve().parents[1] / "workspace" / "parametric"
CANONICAL = "(rule! (let ((dummy 0)) (define (full-row? grid r color) (all? (lambda (c) (= (at grid r c) color)) (range 0 (cols grid)))) (define (full-col? grid c color) (all? (lambda (r) (= (at grid r c) color)) (range 0 (rows grid)))) (define (segments-from-dividers n dividers) (let loop ((ds (append dividers (list n))) (prev -1) (acc (list))) (if (empty? ds) (reverse acc) (let ((x (first ds))) (loop (rest ds) x (if (> (- x prev 1) 0) (cons (list (+ prev 1) x) acc) acc)))))) (define (tile-lattice grid) (let* ((divider-rows (filter (lambda (r) (full-row? grid r 9)) (range 0 (rows grid)))) (divider-cols (filter (lambda (c) (full-col? grid c 9)) (range 0 (cols grid)))) (row-bounds (segments-from-dividers (rows grid) divider-rows)) (col-bounds (segments-from-dividers (cols grid) divider-cols))) (map (lambda (rb) (map (lambda (cb) (subgrid grid (first rb) (first cb) (- (second rb) 1) (- (second cb) 1))) col-bounds)) row-bounds))) (define (assemble-tiles tile-matrix) (let* ((tr (length tile-matrix)) (tc (length (first tile-matrix))) (th (rows (first (first tile-matrix)))) (tw (cols (first (first tile-matrix)))) (h (+ (* tr th) (- tr 1))) (w (+ (* tc tw) (- tc 1)))) (for*/fold ((out (empty-grid h w 9))) ((rr (in-range tr)) (cc (in-range tc)) (r (in-range th)) (c (in-range tw))) (set-cell out (+ (* rr (+ th 1)) r) (+ (* cc (+ tw 1)) c) (at (list-ref (list-ref tile-matrix rr) cc) r c))))) (assemble-tiles (map (lambda (row) (map flip-lr row)) (tile-lattice g)))))"


def load():
    path = HOME / "prototype.py"
    spec = importlib.util.spec_from_file_location("ba29_parametric", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inputs(episode):
    return [pair["input"] for split in ("train", "test") for pair in episode[split]]


def test_default_program_is_exact_canonical_authority():
    module = load()
    assert module.program({"tile_scope": "all_tiles"}) == CANONICAL


def test_settings_share_inputs_and_each_demo_distinguishes_scope():
    module = load()
    all_tiles = module.generate_episode(17, tile_scope="all_tiles", demos=3, queries=4)
    densest = module.generate_episode(17, tile_scope="densest_only", demos=3, queries=4)
    assert inputs(all_tiles) == inputs(densest)
    for left, right in zip(all_tiles["train"], densest["train"]):
        assert left["output"] != right["output"]


def test_requested_counts_distinctness_and_large_stress():
    module = load()
    for demos in range(2, 7):
        episode = module.generate_episode(31, tile_scope="densest_only", demos=demos, queries=4)
        assert len(episode["train"]) == demos
        assert len(episode["test"]) == 4
        serialized = [json.dumps(grid) for grid in inputs(episode)]
        assert len(serialized) == len(set(serialized))
    episode = module.generate_episode(31, tile_scope="all_tiles", demos=3, queries=4)
    assert any(len(grid) == 30 and len(grid[0]) == 30 for grid in inputs(episode))
    assert any(len(grid) >= 29 and len(grid[0]) >= 29 for grid in inputs(episode))


def test_python_labels_and_wrong_intermediate_witness():
    module = load()
    for scope in module.TILE_SCOPES:
        episode = module.generate_episode(0, tile_scope=scope, demos=3, queries=4)
        for split in ("train", "test"):
            for pair in episode[split]:
                assert pair["output"] == module.apply_mode(pair["input"], scope)
    case = module.causal_case(0)
    assert case["settings"] == {"tile_scope": "densest_only"}
    assert case["output"] != case["counterfactual_output"]
    assert case["ablation"] == "wrong_intermediate"
    assert case["intermediate_value"]["densest_count"] > case["intermediate_value"]["sparsest_count"]


@pytest.mark.parametrize(
    "settings,demos,queries",
    [
        ({}, 3, 4),
        ({"tile_scope": "unknown"}, 3, 4),
        ({"tile_scope": "all_tiles", "extra": 1}, 3, 4),
        ({"tile_scope": "all_tiles"}, 1, 4),
        ({"tile_scope": "all_tiles"}, 3, 5),
    ],
)
def test_invalid_requests_fail_loudly(settings, demos, queries):
    module = load()
    with pytest.raises((TypeError, ValueError)):
        values = module.validate_settings(settings)
        module.generate_episode(0, tile_scope=values["tile_scope"], demos=demos, queries=queries)


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
                bridge.define_grid("ba29-parametric-test-grid", grid)
                return bridge.eval_text(
                    "(" + wrap_rule(program) + " ba29-parametric-test-grid)"
                )

            yield apply


def test_alternative_and_counterfactual_programs_match_python_on_protected_racket(protected_racket_apply):
    module = load()
    for scope in module.TILE_SCOPES:
        episode = module.generate_episode(17, tile_scope=scope, demos=2, queries=1)
        for pair in episode["train"] + episode["test"]:
            assert protected_racket_apply(module.program({"tile_scope": scope}), pair["input"]) == pair["output"]
    case = module.causal_case(17)
    assert protected_racket_apply(case["counterfactual_program"], case["input"]) == case["counterfactual_output"]


def _apply_tile_rival(module, grid, selector):
    from copy import deepcopy

    info = module.analyze(grid)
    selected = set(selector(info))
    out = deepcopy(grid)
    for record in info["tiles"]:
        if record["index"] not in selected:
            continue
        ra, rb, ca, cb = record["bounds"]
        mirrored = [row[::-1] for row in record["tile"]]
        for r in range(rb - ra):
            for c in range(cb - ca):
                out[ra + r][ca + c] = mirrored[r][c]
    return out


def test_minimum_demos_refute_fixed_position_and_density_shortcuts():
    module = load()
    for seed in range(64):
        episode = module.generate_episode(seed, tile_scope="densest_only", demos=2, queries=4)
        rivals = {
            "first_tile": lambda info: [0],
            "last_tile": lambda info: [len(info["tiles"]) - 1],
            "sparsest_tile": lambda info: [info["sparsest"]["index"]],
            "exactly_one_blank": lambda info: [
                record["index"]
                for record in info["tiles"]
                if record["count"] == len(record["tile"]) * len(record["tile"][0]) - 1
            ],
            "majority_filled": lambda info: [
                record["index"]
                for record in info["tiles"]
                if 2 * record["count"] > len(record["tile"]) * len(record["tile"][0])
            ],
        }
        for fixed_index in range(8):
            rivals[f"fixed_index_{fixed_index}"] = lambda info, fixed_index=fixed_index: [fixed_index]
        survivors = [
            name
            for name, selector in rivals.items()
            if all(_apply_tile_rival(module, pair["input"], selector) == pair["output"] for pair in episode["train"])
        ]
        assert survivors == [], (seed, survivors)


def test_rival_audit_tool_reports_no_surviving_shortcut():
    path = HOME / "rival_audit.py"
    spec = importlib.util.spec_from_file_location("ba29_rival_audit", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.run(seed_count=32)
    assert report["status"] == "pass"
    assert report["harmful_survivors"] == []
    assert report["all_demo_survivors"] == []
