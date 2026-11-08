from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

ROOT = Path(__file__).resolve().parents[3]
TASK = "0261c073ae3f"
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
    return _load(PARAM / "prototype.py", "test_0261_parametric_prototype")


def _adapter():
    return _load(PARAM / "adapter.py", "test_0261_parametric_adapter")


def _generator():
    return _load(HOME / "generator.py", "test_0261_generator")


def _freeze(grid):
    return tuple(tuple(row) for row in grid)


def test_parametric_artifact_files_exist():
    expected = {
        "README.md",
        "adapter.py",
        "audit.py",
        "canonical.rkt",
        "counterfactual_raw_or.rkt",
        "or.rkt",
        "preflight_compat.py",
        "promotion.json",
        "prototype.py",
    }
    assert expected <= {path.name for path in PARAM.iterdir() if path.is_file()}


def test_preflight_compat_accepts_single_test_object_without_rewriting_authority():
    compat = _load(PARAM / "preflight_compat.py", "test_0261_preflight_compat")
    pair = {"input": ["10"], "output": ["01"]}
    assert compat.record_pairs({"test": pair}, "test") == [pair]
    assert compat.record_pairs({"train": [pair]}, "train") == [pair]
    with pytest.raises(ValueError, match="list or object"):
        compat.record_pairs({"test": "bad"}, "test")


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
    assert adapter.program({"boolean_op": "xor"}) == canonical
    assert (PARAM / "canonical.rkt").read_bytes() == canonical.encode("utf-8")


def test_programs_are_distinct_complete_rules():
    adapter = _adapter()
    xor = adapter.program({"boolean_op": "xor"})
    union = adapter.program({"boolean_op": "or"})
    assert xor.startswith("(rule!") and union.startswith("(rule!")
    assert xor != union
    assert hashlib.sha256(xor.encode()).hexdigest() != hashlib.sha256(union.encode()).hexdigest()


@pytest.mark.parametrize(
    "settings",
    [None, {}, {"boolean_op": "bad"}, {"boolean_op": 1}, {"boolean_op": "xor", "x": 1}],
)
def test_invalid_settings_rejected(settings):
    with pytest.raises(ValueError):
        _adapter().program(settings)


@pytest.mark.parametrize(
    "seed,demos,queries",
    [(True, 2, 4), (-1, 2, 4), (0, 1, 4), (0, 7, 4), (0, 2, 0), (0, 2, 5), (1.0, 2, 4)],
)
def test_invalid_requests_rejected(seed, demos, queries):
    with pytest.raises(ValueError):
        _adapter().generate(seed, {"boolean_op": "xor"}, demos, queries)


def test_minimum_demos_identify_each_setting_and_declared_rivals():
    p = _prototype()
    for seed in (0, 17, 2**63 - 1):
        for op in p.BOOLEAN_OPS:
            episode = p.generate_episode(seed, op, demos=2, queries=4)
            assert p.teaching_survivors(episode["train"]) == [op]


def test_settings_share_inputs_and_counts_are_prefix_stable():
    adapter = _adapter()
    for seed in (0, 17, 999):
        full = {
            op: adapter.generate(seed, {"boolean_op": op}, 6, 4)
            for op in ("xor", "or")
        }
        xor_inputs = [pair["input"] for split in ("train", "test") for pair in full["xor"][split]]
        or_inputs = [pair["input"] for split in ("train", "test") for pair in full["or"][split]]
        assert xor_inputs == or_inputs
        assert len({_freeze(grid) for grid in xor_inputs}) == 10
        for demos, queries in ((2, 1), (2, 4), (3, 2), (6, 4)):
            current = adapter.generate(seed, {"boolean_op": "xor"}, demos, queries)
            assert current["train"] == full["xor"]["train"][:demos]
            assert current["test"] == full["xor"]["test"][:queries]


def test_solver_normalizes_translated_mixed_color_panels_before_boolean_op():
    p = _prototype()
    grid = [
        [0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0],
        [0, 2, 0, 0, 0, 5, 0, 0, 8, 8, 0],
        [0, 3, 3, 0, 0, 5, 0, 0, 0, 8, 0],
        [0, 0, 3, 0, 0, 5, 0, 0, 0, 8, 0],
        [0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 0],
    ]
    # Normalized masks are A={(0,0),(1,0),(1,1),(2,1)} and
    # B={(0,0),(0,1),(1,1),(2,1)}.
    assert p.solve(grid, "xor") == [[0, 7], [7, 0], [0, 0]]
    assert p.solve(grid, "or") == [[7, 7], [7, 7], [0, 7]]


def test_translation_and_panel_colors_do_not_change_normalized_answer():
    p = _prototype()
    first = p.generate_episode(4, "xor", demos=2, queries=4)["train"][0]["input"]
    second = p.retranslate_and_recolor(first)
    assert second != first
    assert p.solve(second, "xor") == p.solve(first, "xor")
    assert p.solve(second, "or") == p.solve(first, "or")


def test_maximum_query_is_substantive_30_square():
    p = _prototype()
    for seed in (0, 17):
        episode = p.generate_episode(seed, "xor", demos=2, queries=4)
        grid = episode["test"][3]["input"]
        assert (len(grid), len(grid[0])) == (30, 30)
        nonzero = sum(value != 0 for row in grid for value in row)
        assert nonzero >= 420
        assert p.self_check(grid) == []
        output = episode["test"][3]["output"]
        assert len(output) >= 24 and len(output[0]) >= 12


def test_base_generator_retains_valid_varied_normalized_operands():
    g = _generator()
    separators = set()
    output_shapes = set()
    mixed_panel_seen = False
    p = _prototype()
    for index in range(64):
        grid = g.generate(271, index)
        assert g.self_check(grid) == []
        sep = next(c for c in range(len(grid[0])) if all(row[c] == 5 for row in grid))
        separators.add((len(grid), len(grid[0]), sep))
        output = p.solve(grid, "xor")
        output_shapes.add((len(output), len(output[0])))
        left_colors = {row[c] for row in grid for c in range(sep) if row[c] not in (0, 5)}
        mixed_panel_seen |= len(left_colors) > 1
    assert len(separators) >= 8
    assert len(output_shapes) >= 3
    assert mixed_panel_seen


def test_promotion_contract_declares_native_limits_and_resources():
    contract = json.loads((PARAM / "promotion.json").read_text())
    assert contract["schema"] == "arcpuzzles-parametric-adapter-v1"
    assert contract["parameters"] == {"boolean_op": ["xor", "or"]}
    assert contract["default"] == {"boolean_op": "xor"}
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
        for op in ("xor", "or"):
            episode = adapter.generate(0, {"boolean_op": op}, 2, 4)
            wrapped = wrap_rule(adapter.program({"boolean_op": op}))
            for pair in (episode["train"][0], episode["test"][3]):
                literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in pair["input"]) + ")"
                assert bridge.eval_text(f"({wrapped} {literal})") == pair["output"]
    finally:
        bridge.close()
