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
    name = "_test_bd05_parametric_" + hashlib.sha256(str(path).encode()).hexdigest()
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
    assert module.program({"rank_order": "second_smallest"}) == canonical
    alternate = module.program({"rank_order": "second_largest"})
    assert alternate != canonical
    assert "list-ref" in alternate


def test_generate_count_prefixes_and_outputs_match_solver():
    module = load_prototype()
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


def test_two_demonstrations_identify_each_setting_and_queries_separate_them():
    module = load_prototype()
    for seed in (0, 17, 2**63 - 1):
        for setting in module.SETTINGS:
            episode = module.generate(seed, setting, demos=2, queries=4)
            assert module.fit_settings(episode["train"]) == [setting]
            other = next(candidate for candidate in module.SETTINGS if candidate != setting)
            assert all(
                module.solve(pair["input"], setting)
                != module.solve(pair["input"], other)
                for pair in episode["test"]
            )
            review = module.self_review(episode)
            assert review["intended_survivors"] == [
                "second_smallest" if setting["rank_order"] == "second_smallest" else "second_largest"
            ]
            assert review["harmful_survivors"] == []


def test_fourth_query_is_substantive_30x30_boundary_stress():
    module = load_prototype()
    episode = module.generate(0, {"rank_order": "second_smallest"}, demos=2, queries=4)
    grid = episode["test"][3]["input"]
    assert (len(grid), len(grid[0])) == (30, 30)
    foreground = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 3}
    assert len(foreground) >= 90
    assert any(r == 0 for r, _ in foreground)
    assert any(r == 29 for r, _ in foreground)
    assert any(c == 0 for _, c in foreground)
    assert any(c == 29 for _, c in foreground)
    assert sum(value == 8 for row in episode["test"][3]["output"] for value in row) >= 20


def test_first_two_demos_refute_declared_shortcuts_over_seed_sweep():
    module = load_prototype()
    for seed in range(32):
        for setting in module.SETTINGS:
            review = module.self_review(module.generate(seed, setting, demos=2, queries=4))
            assert review["harmful_survivors"] == [], (seed, setting, review)


@pytest.mark.parametrize(
    "args",
    [
        (-1, {"rank_order": "second_smallest"}, 3, 4),
        (True, {"rank_order": "second_smallest"}, 3, 4),
        (0, {"rank_order": "smallest"}, 3, 4),
        (0, {"rank_order": "second_smallest", "extra": 1}, 3, 4),
        (0, {"rank_order": "second_smallest"}, 1, 4),
        (0, {"rank_order": "second_smallest"}, 3, 5),
    ],
)
def test_invalid_native_requests_are_rejected(args):
    module = load_prototype()
    with pytest.raises(ValueError):
        module.generate(*args)
