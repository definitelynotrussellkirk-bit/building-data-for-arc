"""Regression tests for the linked frame-area/object-size generator repair."""

from __future__ import annotations

import importlib.util
import json
import random
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GENERATOR_PATH = (
    ROOT
    / "puzzle_generators"
    / "per_puzzle"
    / "c4ad042d2888"
    / "generator.py"
)


def load_generator():
    spec = importlib.util.spec_from_file_location(
        "generator_c4ad042d2888",
        GENERATOR_PATH,
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def canonical_inputs() -> list[list[list[int]]]:
    with (ROOT / "data" / "canonical" / "puzzles.jsonl").open() as source:
        for line in source:
            row = json.loads(line)
            if row.get("task_id") != "c4ad042d2888":
                continue
            tests = row["test"] if isinstance(row["test"], list) else [row["test"]]
            return [pair["input"] for pair in [*row["train"], *tests]]
    raise AssertionError("canonical task c4ad042d2888 is missing")


def clone(grid):
    return [row[:] for row in grid]


def test_canonical_inputs_match_all_linked_profiles_and_self_check():
    generator = load_generator()
    inputs = canonical_inputs()
    signatures = {generator.canonical_profile_signature(grid) for grid in inputs}

    assert signatures == generator._CANONICAL_SIGNATURES
    assert all(generator.self_check(grid) == [] for grid in inputs)


def test_default_prior_reaches_every_profile_in_every_band():
    generator = load_generator()
    for band in ("easy", "medium", "hard"):
        counts = {signature: 0 for signature in generator._CANONICAL_SIGNATURES}
        for seed in range(400):
            grid = generator.generate(seed, seed, difficulty=band)
            signature = generator.canonical_profile_signature(grid)
            if signature in counts:
                counts[signature] += 1

        assert sum(counts.values()) >= 70, (band, counts)
        assert all(count > 0 for count in counts.values()), (band, counts)


def test_exact_override_boundaries_are_observable():
    generator = load_generator()
    for band in ("easy", "medium", "hard"):
        for n_pairs in (2, 3):
            for clip_mode in (False, True):
                grid = generator.generate(
                    91,
                    37,
                    difficulty=band,
                    grid_h=12,
                    grid_w=16,
                    n_pairs=n_pairs,
                    clip_mode=clip_mode,
                    palette_kind="varied",
                )
                observed = generator.observe_overrides(grid)
                assert (len(grid), len(grid[0])) == (12, 16)
                assert observed["n_pairs"] == n_pairs
                assert observed["clip_mode"] is clip_mode
                assert generator.self_check(grid) == []


def test_structural_checker_rejects_targeted_impostors():
    generator = load_generator()
    valid = generator.generate(123, 17, difficulty="hard", clip_mode=True)
    frames, solids, malformed = generator._analyze(valid)
    assert not malformed

    no_frames = [[0 if value == 8 else value for value in row] for row in valid]
    assert generator.self_check(no_frames)

    no_solids = [[0 if value not in (0, 8) else value for value in row] for row in valid]
    assert generator.self_check(no_solids)

    tied_areas = clone(valid)
    # Copy one frame's outline over another frame after clearing the target.
    first, second = sorted(frames, key=lambda frame: frame["area"])[:2]
    for r, c in second["cells"]:
        tied_areas[r][c] = 0
    fr1, fc1, _, _ = first["bbox"]
    sr1, sc1, _, _ = second["bbox"]
    for r, c in first["cells"]:
        nr, nc = sr1 + (r - fr1), sc1 + (c - fc1)
        if nr < len(tied_areas) and nc < len(tied_areas[0]):
            tied_areas[nr][nc] = 8
    assert generator.self_check(tied_areas)

    broken_frame = clone(valid)
    r, c = frames[0]["cells"][0]
    broken_frame[r][c] = 0
    assert generator.self_check(broken_frame)

    mismatched_size = clone(valid)
    r, c = solids[0]["cells"][0]
    mismatched_size[r][c] = 0
    assert generator.self_check(mismatched_size)


def test_replay_freshness_global_rng_and_lesson_clip_schedule():
    generator = load_generator()
    random.seed(8675309)
    before = random.getstate()
    first = generator.generate(77, 4, difficulty="medium")
    after = random.getstate()
    second = generator.generate(77, 4, difficulty="medium")

    assert before == after
    assert first == second
    assert first is not second
    assert all(row_a is not row_b for row_a, row_b in zip(first, second))

    clip_values = []
    for sample_index in range(10, 16):
        grid = generator.generate(901, sample_index, difficulty="medium")
        clip_values.append(generator.observe_overrides(grid)["clip_mode"])
    assert any(clip_values)
    assert not all(clip_values)
