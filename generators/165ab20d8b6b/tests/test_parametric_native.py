from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import pytest

HOME = Path(__file__).resolve().parents[1]
PARAM = HOME / "workspace" / "parametric"


def load_prototype():
    path = PARAM / "prototype.py"
    name = "_test_165ab_parametric_" + hashlib.sha256(str(path).encode()).hexdigest()
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def serialized_inputs(episode):
    return [
        json.dumps(pair["input"], separators=(",", ":"))
        for split in ("train", "test")
        for pair in episode[split]
    ]


def test_program_default_is_exact_canonical_and_alternate_is_distinct():
    module = load_prototype()
    canonical = (PARAM / "canonical.rkt").read_text(encoding="utf-8")
    assert module.program({"neighborhood": "cardinal"}) == canonical
    alternate = module.program({"neighborhood": "moore"})
    assert alternate != canonical
    assert "(list -1 -1)" in alternate


def test_generate_count_prefixes_matched_inputs_and_solver_labels():
    module = load_prototype()
    by_setting = {}
    for setting in module.SETTINGS:
        small = module.generate(17, setting, demos=2, queries=1)
        large = module.generate(17, setting, demos=6, queries=4)
        assert small["train"] == large["train"][:2]
        assert small["test"] == large["test"][:1]
        assert small["program_solution"] == module.program(setting)
        assert len(set(serialized_inputs(large))) == 10
        for split in ("train", "test"):
            for pair in large[split]:
                assert pair["output"] == module.solve(pair["input"], setting)
        by_setting[setting["neighborhood"]] = large
    assert [p["input"] for s in ("train", "test") for p in by_setting["cardinal"][s]] == [
        p["input"] for s in ("train", "test") for p in by_setting["moore"][s]
    ]


def test_two_demonstrations_identify_each_setting_and_refute_declared_shortcuts():
    module = load_prototype()
    for seed in range(32):
        for setting in module.SETTINGS:
            episode = module.generate(seed, setting, demos=2, queries=4)
            assert module.fit_settings(episode["train"]) == [setting]
            review = module.self_review(episode)
            assert review["intended_survivors"] == [setting["neighborhood"]]
            assert review["harmful_survivors"] == [], (seed, setting, review)


def test_fourth_query_is_substantive_30x30_boundary_and_topology_stress():
    module = load_prototype()
    episode = module.generate(0, {"neighborhood": "cardinal"}, demos=2, queries=4)
    pair = episode["test"][3]
    grid = pair["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    foreground = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value}
    assert len(foreground) >= 100
    assert any(r == 0 for r, _ in foreground)
    assert any(r == 29 for r, _ in foreground)
    assert any(c == 0 for _, c in foreground)
    assert any(c == 29 for _, c in foreground)
    assert len({value for row in grid for value in row if value}) >= 5
    assert sum(value != 0 for row in pair["output"] for value in row) >= 70
    # Every generated episode includes at least one enclosed zero cell touched by a blob.
    assert module.has_enclosed_shell_cell(grid)


@pytest.mark.parametrize(
    "args",
    [
        (-1, {"neighborhood": "cardinal"}, 3, 4),
        (True, {"neighborhood": "cardinal"}, 3, 4),
        (0, {"neighborhood": "diagonal"}, 3, 4),
        (0, {"neighborhood": "cardinal", "extra": 1}, 3, 4),
        (0, {"neighborhood": "cardinal"}, 1, 4),
        (0, {"neighborhood": "cardinal"}, 3, 5),
    ],
)
def test_invalid_native_requests_are_rejected(args):
    module = load_prototype()
    with pytest.raises(ValueError):
        module.generate(*args)
