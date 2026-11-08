from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest


TASK_ID = "42a152269589"
GENERATOR = Path(__file__).resolve().parents[1] / "generator.py"


def _load_generator():
    spec = importlib.util.spec_from_file_location(f"generator_{TASK_ID}", GENERATOR)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _canonical_row() -> dict:
    repo_root = Path(__file__).resolve().parents[3]
    candidates = (
        repo_root / "shared/data/canonical/puzzles.jsonl",
        repo_root / "data/canonical/puzzles.jsonl",
        Path.cwd() / "data/canonical/puzzles.jsonl",
    )
    ledger = next((path for path in candidates if path.is_file()), None)
    assert ledger is not None, f"canonical ledger not found; tried {candidates}"
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"canonical task {TASK_ID} not found in {ledger}")


def test_rule_pin_and_exact_axis_contract_are_declared() -> None:
    gen = _load_generator()
    assert gen.RULE_HASH == "2578a5c05f72"
    assert set(gen.AXES) == {"grid_h", "grid_w", "n_pieces"}
    assert gen.INCOMPATIBLE_OVERRIDE_COMBINATIONS == []


def test_self_check_accepts_every_canonical_input() -> None:
    gen = _load_generator()
    row = _canonical_row()
    pairs = list(row["train"]) + list(row["test"])
    failures = [gen.self_check(pair["input"]) for pair in pairs]
    assert failures == [[] for _ in pairs]


def test_python_rule_mirror_matches_every_canonical_output() -> None:
    gen = _load_generator()
    row = _canonical_row()
    pairs = list(row["train"]) + list(row["test"])
    for index, pair in enumerate(pairs):
        assert gen.rule_mirror(pair["input"]) == pair["output"], index


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_three_slot_schedule_teaches_rotation_reflection_and_repeated_colors(difficulty: str) -> None:
    gen = _load_generator()
    grids = [gen.generate(71, index, difficulty=difficulty) for index in range(3)]

    assert [gen.schedule_profile(71, index, difficulty) for index in range(3)] == [
        "translation_anchor",
        "rotation_required",
        "reflection_and_repeat",
    ]
    assert gen._translation_only_pack(grids[1]) is None
    assert gen._rotation_only_pack(grids[1]) is not None
    assert gen._rotation_only_pack(grids[2]) is None
    assert gen.rule_mirror(grids[2]) is not None
    assert gen._has_repeated_component_color(grids[2])


@pytest.mark.parametrize("n_pieces", [3, 4, 5])
@pytest.mark.parametrize("grid_w", [10, 12, 13])
def test_exact_overrides_are_observable(n_pieces: int, grid_w: int) -> None:
    gen = _load_generator()
    grid = gen.generate(
        313,
        2,
        difficulty="hard",
        grid_h=10,
        grid_w=grid_w,
        n_pieces=n_pieces,
    )
    assert gen.observe_overrides(grid) == {
        "grid_h": 10,
        "grid_w": grid_w,
        "n_pieces": n_pieces,
    }
    assert gen.self_check(grid) == []
    out = gen.rule_mirror(grid)
    assert len(out) == 3 and all(len(row) == 4 for row in out)


def test_unknown_override_is_rejected() -> None:
    gen = _load_generator()
    with pytest.raises(ValueError, match="unknown override"):
        gen.generate(0, 0, invented_axis="x")


def test_default_census_is_valid_diverse_and_canonical_profiled() -> None:
    gen = _load_generator()
    seen_inputs: set[str] = set()
    seen_outputs: set[str] = set()
    profiles: set[str] = set()
    widths: set[int] = set()

    for difficulty in ("easy", "medium", "hard"):
        for sample_index in range(12):
            grid = gen.generate(1000 + sample_index, sample_index, difficulty=difficulty)
            assert gen.self_check(grid) == []
            assert gen.strict_canonical_like(grid) == []
            out = gen.rule_mirror(grid)
            assert len(out) == 3 and all(len(row) == 4 for row in out)
            seen_inputs.add(json.dumps(grid, separators=(",", ":")))
            seen_outputs.add(json.dumps(out, separators=(",", ":")))
            profiles.add(gen.schedule_profile(0, sample_index, difficulty))
            widths.add(len(grid[0]))

    assert profiles == set(gen.SCHEDULE_PROFILES)
    assert widths == {10, 11, 12, 13}
    assert len(seen_inputs) >= 30
    assert len(seen_outputs) >= 24
