from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
TASK = "f22baf82ea81"
HOME = ROOT / "generators" / TASK
PARAM = HOME / "workspace" / "parametric"
sys.path.insert(0, str(ROOT / "shared" / "runtime"))


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _prototype():
    return _load(PARAM / "prototype.py", "test_f22_parametric_prototype")


def _adapter():
    return _load(PARAM / "adapter.py", "test_f22_parametric_adapter")


def _generator():
    return _load(HOME / "generator.py", "test_f22_generator")


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def _inner_facts(grid):
    cells = [(r, c, grid[r][c]) for r in range(len(grid)) for c in range(len(grid[0])) if grid[r][c] != 0]
    r0 = min(r for r, _, _ in cells)
    r1 = max(r for r, _, _ in cells)
    c0 = min(c for _, c, _ in cells)
    c1 = max(c for _, c, _ in cells)
    outer = grid[r0][c0]
    inner = {(r - r0, c - c0) for r, c, v in cells if v != outer}
    ir0 = min(r for r, _ in inner)
    ir1 = max(r for r, _ in inner)
    ic0 = min(c for _, c in inner)
    ic1 = max(c for _, c in inner)
    solid = len(inner) == (ir1 - ir0 + 1) * (ic1 - ic0 + 1)
    centered = (ir0 + ir1 == r1 - r0) and (ic0 + ic1 == c1 - c0)
    return solid, centered


def test_parametric_artifact_files_exist():
    expected = {
        "README.md",
        "adapter.py",
        "audit.py",
        "canonical.rkt",
        "counterfactual_crop_rotate.rkt",
        "promotion.json",
        "prototype.py",
        "rotate_cw.rkt",
    }
    assert expected <= {p.name for p in PARAM.iterdir() if p.is_file()}


def test_default_program_matches_catalog_exactly():
    from arcpuzzles import Catalog

    adapter = _adapter()
    record = Catalog(ROOT).get(TASK)
    programs = {
        variant["program_solution"]
        for variant in record["variants"]
        if isinstance(variant.get("program_solution"), str)
    }
    assert len(programs) == 1
    canonical = next(iter(programs))
    assert adapter.program({"post_transform": "as_is"}) == canonical
    assert (PARAM / "canonical.rkt").read_bytes() == canonical.encode("utf-8")


def test_programs_are_distinct_complete_rules():
    adapter = _adapter()
    canonical = adapter.program({"post_transform": "as_is"})
    rotated = adapter.program({"post_transform": "rotate_cw"})
    assert canonical.startswith("(rule!") and rotated.startswith("(rule!")
    assert canonical != rotated
    assert hashlib.sha256(canonical.encode()).hexdigest() != hashlib.sha256(rotated.encode()).hexdigest()


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"post_transform": "bad"}, {"post_transform": 1}, {"post_transform": "as_is", "x": 1}],
)
def test_invalid_settings_rejected(settings):
    adapter = _adapter()
    with pytest.raises(ValueError):
        adapter.program(settings)


@pytest.mark.parametrize(
    "seed,demos,queries",
    [(True, 2, 4), (-1, 2, 4), (0, 1, 4), (0, 7, 4), (0, 2, 0), (0, 2, 5), (1.0, 2, 4)],
)
def test_invalid_requests_rejected(seed, demos, queries):
    adapter = _adapter()
    with pytest.raises(ValueError):
        adapter.generate(seed, {"post_transform": "as_is"}, demos, queries)


def test_minimum_demos_identify_each_setting_and_declared_rivals():
    p = _prototype()
    for seed in (0, 17, 2**63 - 1):
        for mode in p.TRANSFORMS:
            episode = p.generate_episode(seed, mode, demos=2, queries=4)
            assert p.teaching_survivors(episode["train"]) == [mode]


def test_settings_share_inputs_and_counts_are_prefix_stable():
    adapter = _adapter()
    for seed in (0, 17, 999):
        full = {
            mode: adapter.generate(seed, {"post_transform": mode}, 6, 4)
            for mode in ("as_is", "rotate_cw")
        }
        left_inputs = [p["input"] for split in ("train", "test") for p in full["as_is"][split]]
        right_inputs = [p["input"] for split in ("train", "test") for p in full["rotate_cw"][split]]
        assert left_inputs == right_inputs
        assert len({_freeze(g) for g in left_inputs}) == 10
        for demos, queries in ((2, 1), (2, 4), (3, 2), (6, 4)):
            current = adapter.generate(seed, {"post_transform": "as_is"}, demos, queries)
            assert current["train"] == full["as_is"]["train"][:demos]
            assert current["test"] == full["as_is"]["test"][:queries]


def test_solver_literal_crop_swap_and_rotation():
    p = _prototype()
    grid = [
        [0, 0, 0, 0, 0, 0],
        [0, 2, 2, 2, 2, 0],
        [0, 2, 4, 2, 2, 0],
        [0, 2, 4, 4, 2, 0],
        [0, 2, 2, 2, 2, 0],
        [0, 0, 0, 0, 0, 0],
    ]
    canonical = [
        [4, 4, 4, 4],
        [4, 2, 4, 4],
        [4, 2, 2, 4],
        [4, 4, 4, 4],
    ]
    assert p.solve(grid, "as_is") == canonical
    assert p.solve(grid, "rotate_cw") == p.rotate_cw(canonical)


def test_maximum_query_is_substantive_30_square():
    p = _prototype()
    for seed in (0, 17):
        episode = p.generate_episode(seed, "as_is", demos=2, queries=4)
        grid = episode["test"][3]["input"]
        assert (len(grid), len(grid[0])) == (30, 30)
        nonzero = sum(v != 0 for row in grid for v in row)
        colors = {v for row in grid for v in row if v != 0}
        assert nonzero >= 500
        assert len(colors) == 2
        assert p.self_check(grid) == []


def test_base_generator_supports_non_solid_and_off_center_inner_masks():
    g = _generator()
    non_solid = g.generate(11, 0, inner_shape="connected_growth", region_h=8, region_w=9)
    off_center = g.generate(19, 0, inner_shape="off_center_rect", region_h=8, region_w=9)
    assert g.self_check(non_solid) == []
    assert g.self_check(off_center) == []
    solid_a, centered_a = _inner_facts(non_solid)
    solid_b, centered_b = _inner_facts(off_center)
    assert solid_a is False
    assert centered_b is False


def test_default_base_sampler_has_topology_spread():
    g = _generator()
    facts = [_inner_facts(g.generate(123, i)) for i in range(64)]
    assert any(not solid for solid, _ in facts)
    assert any(not centered for _, centered in facts)
    assert any(solid for solid, _ in facts)


def test_promotion_contract_declares_native_limits_and_resources():
    contract = json.loads((PARAM / "promotion.json").read_text())
    assert contract["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert contract["parameters"] == {"post_transform": ["as_is", "rotate_cw"]}
    assert contract["default"] == {"post_transform": "as_is"}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    assert contract["qualification_demos"] == 2


def test_selected_labels_execute_in_protected_racket():
    from arc_repl.racket_bridge import RacketBridge
    from puzzle_generators.rule_wrap import wrap_rule

    adapter = _adapter()
    bridge = RacketBridge(timeout=30, max_calls_before_restart=16)
    try:
        identity = bridge.runtime_identity
        assert identity["backend"] == "racket" and identity["protected"] is True
        for mode in ("as_is", "rotate_cw"):
            episode = adapter.generate(0, {"post_transform": mode}, 2, 4)
            wrapped = wrap_rule(adapter.program({"post_transform": mode}))
            for pair in (episode["train"][0], episode["test"][3]):
                literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in pair["input"]) + ")"
                assert bridge.eval_text(f"({wrapped} {literal})") == pair["output"]
    finally:
        bridge.close()
