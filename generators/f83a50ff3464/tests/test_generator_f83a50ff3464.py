from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys

import pytest


TASK_ID = "f83a50ff3464"
GENERATOR_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
RUNTIME_ROOT = REPO_ROOT / "shared" / "runtime"
if str(RUNTIME_ROOT) not in sys.path:
    sys.path.insert(0, str(RUNTIME_ROOT))


def _load_generator():
    path = GENERATOR_DIR / "generator.py"
    spec = importlib.util.spec_from_file_location(
        f"test_{TASK_ID}_generator", path
    )
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def gen():
    return _load_generator()


def _canonical_row() -> dict:
    path = REPO_ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"canonical row {TASK_ID} not found")


def _pair(gen, seed: int, sample_index: int, band: str) -> dict:
    grid = gen.generate(seed, sample_index, difficulty=band)
    return {"input": grid, "output": gen.rule_mirror(grid)}


def test_unknown_override_is_rejected(gen):
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, difficulty="easy", typo_axis=1)


def test_every_scene_profile_round_trips_through_observer(gen):
    assert len(gen.SCENE_PROFILES) >= 8
    for index, profile in enumerate(gen.SCENE_PROFILES):
        grid = gen.generate(
            seed=17,
            sample_index=index,
            difficulty="medium",
            scene_profile=profile,
        )
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.observe_overrides(grid) == {"scene_profile": profile}
        output = gen.rule_mirror(grid)
        changed = {
            (r, c)
            for r, row in enumerate(grid)
            for c, value in enumerate(row)
            if output[r][c] != value
        }
        assert changed == gen._fires(grid)
        assert changed


def test_each_declared_witness_has_a_real_rival_counterexample(gen):
    witness_hits = {name: 0 for name in gen.SEMANTIC_WITNESSES}
    for index, profile in enumerate(gen.SCENE_PROFILES):
        grid = gen.generate(
            seed=29,
            sample_index=index,
            difficulty="hard",
            scene_profile=profile,
        )
        oracle = gen.rule_mirror(grid)
        for witness_name, witness in gen.SEMANTIC_WITNESSES.items():
            if not witness(grid):
                continue
            witness_hits[witness_name] += 1
            claimed = gen.WITNESS_RIVALS[witness_name]
            assert claimed
            assert any(
                gen.SEMANTIC_RIVALS[rival_name](grid) != oracle
                for rival_name in claimed
            )
    assert all(count > 0 for count in witness_hits.values()), witness_hits


def test_every_four_demo_schedule_window_identifies_the_rule(gen):
    assert gen.EXAMPLES_NEEDED == 4
    for band in ("easy", "medium", "hard"):
        for start in range(8):
            demos = [
                _pair(gen, seed=101 + start, sample_index=start + offset, band=band)
                for offset in range(gen.EXAMPLES_NEEDED)
            ]
            query = _pair(
                gen,
                seed=211 + start,
                sample_index=start + gen.EXAMPLES_NEEDED,
                band=band,
            )
            assert gen.lesson_identifiable(demos, query) == []


def test_canonical_demonstrations_fit_all_declared_shortcuts(gen):
    row = _canonical_row()
    assert row["train"]
    for pair in row["train"]:
        grid = pair["input"]
        expected = pair["output"]
        assert gen.self_check(grid) == []
        assert gen.strict_canonical_like(grid) == []
        assert gen.rule_mirror(grid) == expected
        for name, shortcut in gen.CANONICAL_SHORTCUTS.items():
            assert shortcut(grid) == expected, name
