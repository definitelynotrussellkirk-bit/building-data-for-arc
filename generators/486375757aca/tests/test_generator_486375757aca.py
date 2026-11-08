"""Focused semantic regressions for the seeded-frame generator."""
from __future__ import annotations

import copy
import importlib.util
import json
from pathlib import Path

import pytest


TASK_ID = "486375757aca"
HERE = Path(__file__).resolve()
REPO = HERE.parents[3]
GENERATOR = HERE.parents[1] / "generator.py"

_spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", GENERATOR)
assert _spec and _spec.loader
GEN = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(GEN)


def _normalize_grid(value):
    if isinstance(value, list) and value and isinstance(value[0], str):
        return [[int(cell) for cell in row] for row in value]
    return [[int(cell) for cell in row] for row in value]


def _canonical_pairs():
    pairs = []
    with (REPO / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            for split in ("train", "test"):
                raw = row.get(split, [])
                if isinstance(raw, dict):
                    raw = [raw]
                for pair in raw:
                    pairs.append({
                        "input": _normalize_grid(pair["input"]),
                        "output": _normalize_grid(pair["output"]),
                    })
    return pairs


def _pair(grid):
    return {"input": copy.deepcopy(grid), "output": GEN.rule_mirror(grid)}


def test_rule_hash_self_check_and_mirror_cover_every_canonical_pair():
    assert GEN.RULE_HASH == "32695808b436"
    pairs = _canonical_pairs()
    assert len(pairs) == 4
    for pair in pairs:
        before = copy.deepcopy(pair["input"])
        assert GEN.self_check(pair["input"]) == []
        assert GEN.strict_canonical_like(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]
        assert pair["input"] == before


def test_every_declared_profile_round_trips_in_every_band():
    assert set(GEN.AXES) == {"scene_profile"}
    assert tuple(GEN.AXES["scene_profile"]["valid"].split("|")) == GEN.SCENE_PROFILES
    assert GEN.HELPFUL_TEXTURES == GEN.DEGENERATE_TEXTURES == ()
    for band in ("easy", "medium", "hard"):
        for index, profile in enumerate(GEN.SCENE_PROFILES):
            grid = GEN.generate(10_000 + index, index, difficulty=band, scene_profile=profile)
            assert GEN.observe_overrides(grid) == {"scene_profile": profile}
            assert GEN.self_check(grid) == []
            assert GEN.strict_canonical_like(grid) == []
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis="touching_pair_8x12")
    with pytest.raises(ValueError, match="unknown difficulty"):
        GEN.generate(1, 0, difficulty="expert")


def test_every_three_demo_window_refutes_all_named_rivals():
    assert GEN.EXAMPLES_NEEDED == 3
    for band in ("easy", "medium", "hard"):
        for start in range(18):
            seed = 20_000 + start
            grids = [
                GEN.generate(seed, start + offset, difficulty=band)
                for offset in range(GEN.EXAMPLES_NEEDED + 1)
            ]
            demos = [_pair(grid) for grid in grids[: GEN.EXAMPLES_NEEDED]]
            query = _pair(grids[GEN.EXAMPLES_NEEDED])
            assert GEN.lesson_identifiable(demos, query) == []
            for rival in GEN.LESSON_COMPETITORS.values():
                assert any(rival(pair["input"]) != pair["output"] for pair in demos)


def test_touching_profiles_expose_component_bbox_and_last_seed_semantics():
    touching = [name for name in GEN.SCENE_PROFILES if "touching" in name]
    assert touching
    for index, profile in enumerate(touching):
        grid = GEN.generate(30_000 + index, index, scene_profile=profile)
        official = GEN.rule_mirror(grid)
        assert GEN.SEMANTIC_WITNESSES["multi_seed_component"](grid)
        assert GEN.SEMANTIC_WITNESSES["internal_blue_overwritten"](grid)
        assert GEN.SEMANTIC_RIVALS["first_seed_per_component"](grid) != official
        assert GEN.SEMANTIC_RIVALS["fill_each_frame_independently"](grid) != official
        assert GEN.SEMANTIC_RIVALS["preserve_internal_blue"](grid) != official


def test_determinism_freshness_and_profile_schedule():
    for band in (None, "easy", "medium", "hard"):
        first = GEN.generate(42, 17, difficulty=band)
        second = GEN.generate(42, 17, difficulty=band)
        assert first == second
        assert first is not second
        assert all(a is not b for a, b in zip(first, second))
        assert GEN.observe_overrides(first)["scene_profile"] == GEN.schedule_profile(
            42, 17, difficulty=band
        )
