from __future__ import annotations

from collections import Counter
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import random
import sys

import pytest


TASK_ID = "c0bd45c81959"
HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace" / "parametric"
ADAPTER_PATH = PARAMETRIC / "adapter.py"


def _load_adapter():
    spec = importlib.util.spec_from_file_location(f"parametric_{TASK_ID}", ADAPTER_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def adapter():
    return _load_adapter()


def _canonical_source():
    from arcpuzzles.catalog import Catalog

    catalog = Catalog(Path("."))
    row = catalog.describe(TASK_ID)
    programs = {
        variant["program_solution"]
        for variant in catalog._variants()[row.get("rule_task_id", TASK_ID)]
    }
    assert len(programs) == 1
    return next(iter(programs))


def _key(grid):
    return tuple(tuple(row) for row in grid)


def _all_input_keys(episode):
    return [_key(pair["input"]) for split in ("train", "test") for pair in episode[split]]


def _bbox_output(modes, *, endpoints_only=False, full=False):
    counts = Counter(value for row in modes for value in row)
    repeated = [value for value, count in counts.items() if count == 2]
    if len(repeated) != 1:
        return [[0] * 5 for _ in range(4)]
    target = repeated[0]
    points = [(r, c) for r in range(2) for c in range(3) if modes[r][c] == target]
    r0, r1 = min(r for r, _ in points), max(r for r, _ in points)
    c0, c1 = min(c for _, c in points), max(c for _, c in points)
    result = [[0] * 5 for _ in range(4)]
    for r in range(2):
        for c in range(3):
            chosen = full or ((r, c) in points if endpoints_only else r0 <= r <= r1 and c0 <= c <= c1)
            if chosen:
                result[r + 1][c + 1] = target
    return result


def _first_cell_modes(grid):
    return [
        [grid[1 + 4 * br][1 + 3 * bc] for bc in range(3)]
        for br in range(2)
    ]


def _racket_apply(bridge, program, grid):
    from puzzle_generators.rule_wrap import wrap_rule

    literal = "'(" + " ".join("(" + " ".join(map(str, row)) + ")" for row in grid) + ")"
    return bridge.eval_text(f"({wrap_rule(program)} {literal})")


def test_contract_and_default_program_preserve_exact_canonical_bytes(adapter):
    promotion = json.loads((PARAMETRIC / "promotion.json").read_text(encoding="utf-8"))
    assert promotion == {
        "schema": "arcpuzzles-parametric-adapter-v1",
        "adapter": f"generators/{TASK_ID}/workspace/parametric/adapter.py",
        "parameters": {"operation": ["all_modes", "duplicate_bbox"]},
        "default": {"operation": "all_modes"},
        "limits": {"demos": [2, 6], "queries": [1, 4]},
        "qualification_demos": 2,
        "resources": [
            f"generators/{TASK_ID}/workspace/parametric/canonical.rkt",
            f"generators/{TASK_ID}/workspace/parametric/duplicate-bbox.rkt",
        ],
    }
    assert adapter.program({"operation": "all_modes"}) == _canonical_source()
    assert (PARAMETRIC / "canonical.rkt").read_text(encoding="utf-8") == _canonical_source()
    assert adapter.program({"operation": "duplicate_bbox"}) == (
        PARAMETRIC / "duplicate-bbox.rkt"
    ).read_text(encoding="utf-8")


def test_settings_and_counts_are_strictly_validated(adapter):
    bad_settings = [None, [], "all_modes", {}, {"operation": "unknown"}, {"operation": 1}, {"operation": True}, {"operation": "all_modes", "extra": 1}]
    for settings in bad_settings:
        with pytest.raises((TypeError, ValueError)):
            adapter.program(settings)
        with pytest.raises((TypeError, ValueError)):
            adapter.generate(0, settings, 2, 1)
    valid = {"seed": 0, "settings": {"operation": "all_modes"}, "demos": 2, "queries": 1}
    for name, values in {
        "seed": [-1, 2**63, True, 1.5, "0"],
        "demos": [1, 7, False, 2.0, "2"],
        "queries": [0, 5, True, 1.0, "1"],
    }.items():
        for value in values:
            with pytest.raises((TypeError, ValueError)):
                adapter.generate(**{**valid, name: value})


def test_generated_episodes_are_correct_distinct_and_prefix_stable(adapter):
    for operation in adapter.OPERATIONS:
        settings = {"operation": operation}
        full = adapter.generate(17, settings, demos=6, queries=4)
        assert len(full["train"]) == 6
        assert len(full["test"]) == 4
        assert full["program_solution"] == adapter.program(settings)
        keys = _all_input_keys(full)
        assert len(keys) == len(set(keys))
        for split in ("train", "test"):
            for pair in full[split]:
                assert pair["output"] == adapter.solve(pair["input"], operation)
                assert adapter.extract_modes(pair["input"])
        for demos in (2, 3, 5):
            shorter = adapter.generate(17, settings, demos=demos, queries=4)
            assert shorter["train"] == full["train"][:demos]
            assert shorter["test"] == full["test"]
        for queries in (1, 2, 3):
            shorter = adapter.generate(17, settings, demos=6, queries=queries)
            assert shorter["train"] == full["train"]
            assert shorter["test"] == full["test"][:queries]


def test_settings_share_inputs_but_change_every_mandatory_demo_label(adapter):
    canonical = adapter.generate(9, {"operation": "all_modes"}, demos=6, queries=4)
    alternate = adapter.generate(9, {"operation": "duplicate_bbox"}, demos=6, queries=4)
    assert _all_input_keys(canonical) == _all_input_keys(alternate)
    for left, right in zip(canonical["train"][:2], alternate["train"][:2]):
        assert left["input"] == right["input"]
        assert left["output"] != right["output"]


def test_two_demos_refute_first_cell_endpoints_and_fixed_full_bbox_shortcuts(adapter):
    episode = adapter.generate(23, {"operation": "duplicate_bbox"}, demos=2, queries=4)
    rivals = {"first_cell": [], "endpoints_only": [], "full_bbox": []}
    for pair in episode["train"]:
        modes = adapter.extract_modes(pair["input"])
        rivals["first_cell"].append(_bbox_output(_first_cell_modes(pair["input"])))
        rivals["endpoints_only"].append(_bbox_output(modes, endpoints_only=True))
        rivals["full_bbox"].append(_bbox_output(modes, full=True))
    for name, outputs in rivals.items():
        assert any(output != pair["output"] for output, pair in zip(outputs, episode["train"])), name


def test_query_profiles_cover_fixed_domain_boundaries_without_fake_30x30_padding(adapter):
    episode = adapter.generate(5, {"operation": "duplicate_bbox"}, demos=2, queries=4)
    shapes = [(len(pair["input"]), len(pair["input"][0])) for pair in episode["test"]]
    assert shapes == list(adapter.QUERY_SHAPES)
    assert max(max(shape) for shape in shapes) == 14
    assert adapter.DOMAIN_LIMIT == "fixed six 3x2 blocks; larger canvases add only ignored background"


def test_racket_programs_match_python_claims(adapter):
    from arc_repl.racket_bridge import RacketBridge

    with RacketBridge(max_calls_before_restart=64) as bridge:
        for operation in adapter.OPERATIONS:
            settings = {"operation": operation}
            episode = adapter.generate(31, settings, demos=2, queries=2)
            program = adapter.program(settings)
            for pair in episode["train"] + episode["test"]:
                assert _racket_apply(bridge, program, pair["input"]) == pair["output"]


def test_generation_is_deterministic_fresh_and_global_rng_pure(adapter):
    settings = {"operation": "duplicate_bbox"}
    state = random.getstate()
    first = adapter.generate(17, settings, demos=6, queries=4)
    assert random.getstate() == state
    second = adapter.generate(17, settings, demos=6, queries=4)
    assert first == second and first is not second
    original = deepcopy(second)
    first["train"][0]["input"][0][0] = 9
    first["test"][0]["output"][0][0] = 9
    assert second == original
