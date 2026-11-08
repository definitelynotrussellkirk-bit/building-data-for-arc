"""Native special-period contract and lesson regressions (Python claims only).

Protected Racket label/teaching evidence is produced by build_prototype.py and
the independent native qualifier; these tests exercise the authoring surface.
"""
from __future__ import annotations

import importlib.util
import hashlib
import json
from pathlib import Path

import pytest

from reviewer_support import canonical_path, find_root, public_challenge_bytes, public_challenge_id

HOME = Path(__file__).resolve().parents[1]
PARAMETRIC = HOME / "workspace/parametric"
ROOT = find_root(__file__)


def load_adapter():
    path = PARAMETRIC / "adapter.py"
    assert path.is_file(), "native adapter has not been implemented"
    spec = importlib.util.spec_from_file_location("test_443eebb271d9_native", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def inputs(episode, split):
    return [pair["input"] for pair in episode[split]]


def test_native_contract_and_exact_canonical_default():
    adapter = load_adapter()
    contract = json.loads((PARAMETRIC / "promotion.json").read_text())
    assert contract["parameters"] == {"special_period": [3, 2]}
    assert contract["default"] == {"special_period": 3}
    assert contract["limits"] == {"demos": [2, 6], "queries": [1, 4]}
    with canonical_path(ROOT).open() as handle:
        canonical = {row["program_solution"] for line in handle
                     if (row := json.loads(line)).get("task_id") == "443eebb271d9"}
    assert canonical == {adapter.program({"special_period": 3})}
    assert adapter.program({"special_period": 2}) not in canonical


def test_every_native_program_uses_the_real_runtime_rule_contract():
    from puzzle_generators.rule_wrap import wrap_rule
    adapter = load_adapter()
    for period in (3, 2):
        callable_source = wrap_rule(adapter.program({"special_period": period}))
        assert callable_source.startswith("(lambda (g)")


@pytest.mark.parametrize("seed", [0, 17, 2**63 - 1])
@pytest.mark.parametrize("demos", [2, 3, 4, 5, 6])
def test_counts_distinctness_and_inputs_matched_across_settings(seed, demos):
    adapter = load_adapter()
    original = adapter.generate(seed, {"special_period": 3}, demos, 4)
    alternate = adapter.generate(seed, {"special_period": 2}, demos, 4)
    assert original == adapter.generate(seed, {"special_period": 3}, demos, 4)
    assert len(original["train"]) == demos
    assert len(original["test"]) == 4
    assert inputs(original, "train") == inputs(alternate, "train")
    assert inputs(original, "test") == inputs(alternate, "test")
    pairs = original["train"] + original["test"]
    assert len({json.dumps(p["input"]) for p in pairs}) == demos + 4
    assert original["program_solution"] == adapter.program({"special_period": 3})
    assert alternate["program_solution"] == adapter.program({"special_period": 2})
    assert any(a["output"] != b["output"]
               for a, b in zip(original["train"], alternate["train"]))


def test_demo_count_and_query_count_do_not_change_the_first_turn():
    adapter = load_adapter()
    for period in (3, 2):
        short = adapter.generate(23, {"special_period": period}, 2, 1)
        full = adapter.generate(23, {"special_period": period}, 2, 4)
        extra = adapter.generate(23, {"special_period": period}, 6, 4)
        assert short["train"] == full["train"] == extra["train"][:2]
        assert short["test"] == full["test"][:1] == extra["test"][:1]
        single = {"train": short["train"], "test": short["test"]}
        first_turn = {"train": full["train"], "test": full["test"][:1]}
        assert public_challenge_bytes(single) == public_challenge_bytes(first_turn)


def test_minimum_lesson_teaches_whole_disconnected_glyph():
    from reviewer_support import load_selected_generator
    generator, _, _ = load_selected_generator("443eebb271d9", root=ROOT)
    adapter = load_adapter()
    for seed in (0, 1, 17, 23):
        episode = adapter.generate(seed, {"special_period": 3}, 2, 4)
        assert any(generator._largest_component_rival(p["input"]) != p["output"]
                   for p in episode["train"])
        assert all(generator.self_check(p["input"]) == []
                   for p in episode["train"] + episode["test"])


def test_four_queries_include_lawful_minimum_and_substantive_thirty_square():
    adapter = load_adapter()
    for period in (3, 2):
        episode = adapter.generate(17, {"special_period": period}, 3, 4)
        sizes = {(len(p["input"]), len(p["input"][0])) for p in episode["test"]}
        assert (11, 18) in sizes
        assert (30, 30) in sizes
        large = next(p for p in episode["test"] if len(p["input"]) == len(p["input"][0]) == 30)
        colored = [(r, c) for r, row in enumerate(large["output"])
                   for c, value in enumerate(row) if value]
        assert len(colored) >= 100
        assert max(r for r, _ in colored) >= 28
        assert max(c for _, c in colored) >= 28


def test_large_query_is_not_one_memorizable_grid_for_every_seed():
    adapter = load_adapter()
    large_inputs = [next(p["input"] for p in adapter.generate(seed, {"special_period": 3}, 2, 4)["test"]
                         if len(p["input"]) == len(p["input"][0]) == 30)
                    for seed in range(16)]
    assert len({json.dumps(grid) for grid in large_inputs}) >= 8


def test_minimum_demos_reject_only_the_first_special_copy():
    """A plausible wrong rule: select copy p once instead of every p-th copy."""
    def single_special(grid, period):
        cells = [(r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 7]
        r0, c0 = min(r for r, _ in cells), min(c for _, c in cells)
        gh = max(r for r, _ in cells) - r0 + 1
        gw = max(c for _, c in cells) - c0 + 1
        mask = {(r - r0, c - c0) for r, c in cells}
        out = [[0] * len(grid[0]) for _ in grid]
        for r in range(r0, len(grid)):
            for c in range(c0, len(grid[0])):
                instance = (c - c0) // (gw + 1)
                repeat = (r - r0) // (gh + 1)
                if ((r - r0) % (gh + 1), (c - c0) % (gw + 1)) in mask:
                    if repeat == 0 or instance == period - 1:
                        out[r][c] = 6 if instance == period - 1 else 7
        return out
    adapter = load_adapter()
    for seed in (0, 2, 3, 17):
        for period in (3, 2):
            episode = adapter.generate(seed, {"special_period": period}, 2, 4)
            assert any(single_special(p["input"], period) != p["output"] for p in episode["train"]), (seed, period)


@pytest.mark.parametrize("settings", [{}, {"special_period": True}, {"special_period": 3.0},
                                     {"special_period": "3"}, {"special_period": 4},
                                     {"special_period": 3, "extra": 0}])
def test_invalid_settings_fail_closed(settings):
    adapter = load_adapter()
    with pytest.raises((TypeError, ValueError)):
        adapter.program(settings)
    with pytest.raises((TypeError, ValueError)):
        adapter.generate(0, settings, 3, 4)


@pytest.mark.parametrize("seed,demos,queries", [(True, 3, 4), (-1, 3, 4), (2**63, 3, 4),
                                               (0, True, 4), (0, 1, 4), (0, 7, 4),
                                               (0, 3, False), (0, 3, 0), (0, 3, 5)])
def test_invalid_scalars_and_counts_fail_closed(seed, demos, queries):
    with pytest.raises((TypeError, ValueError)):
        load_adapter().generate(seed, {"special_period": 3}, demos, queries)


def test_public_identity_depends_only_on_visible_bytes():
    adapter = load_adapter()
    episode = adapter.generate(17, {"special_period": 2}, 3, 4)
    first_turn = {"train": episode["train"], "test": episode["test"][:1]}
    before = public_challenge_id(first_turn)
    first_turn["settings"] = {"special_period": 99}
    first_turn["program_solution"] = "private changed source"
    first_turn["test"][0]["output"] = [[9]]
    assert public_challenge_id(first_turn) == before
    serialized = public_challenge_bytes(first_turn)
    assert b"special_period" not in serialized
    assert b"program_solution" not in serialized
    assert set(json.loads(serialized)["test"][0]) == {"input"}


def test_public_writer_saves_only_hash_named_single_query_views(tmp_path):
    path = PARAMETRIC / "build_prototype.py"
    spec = importlib.util.spec_from_file_location("test_native_special_period_builder", path)
    builder = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(builder)
    episode = load_adapter().generate(17, {"special_period": 2}, 3, 4)
    ids = builder.write_public_views(tmp_path, episode)
    assert len(set(ids)) == 4
    assert len(list(tmp_path.iterdir())) == 4
    for identifier in ids:
        body = (tmp_path / (identifier + ".json")).read_bytes()
        assert identifier == hashlib.sha256(body).hexdigest()
        public = json.loads(body)
        assert set(public) == {"train", "test"}
        assert len(public["test"]) == 1
        assert set(public["test"][0]) == {"input"}
    episode["settings"] = {"special_period": 3}
    episode["program_solution"] = "changed private text"
    for pair in episode["test"]:
        pair["output"] = [[9]]
    assert builder.write_public_views(tmp_path, episode) == ids
