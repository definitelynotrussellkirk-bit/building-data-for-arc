from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import subprocess
import sys
from collections import deque
from pathlib import Path

import pytest

TASK_ID = "85de426e8683"
TEST_FILE = Path(__file__).resolve()
GENERATOR_PATH = TEST_FILE.parents[1] / "generator.py"


def _find_runtime_and_canonical() -> tuple[Path, Path]:
    for parent in TEST_FILE.parents:
        source_canonical = parent / "shared/data/canonical/puzzles.jsonl"
        if source_canonical.is_file():
            return parent / "shared/runtime", source_canonical
        runtime_canonical = parent / "data/canonical/puzzles.jsonl"
        if runtime_canonical.is_file():
            return parent, runtime_canonical
    raise RuntimeError("could not locate ARCpuzzles runtime/canonical ledger")


RUNTIME, CANONICAL_PATH = _find_runtime_and_canonical()
sys.path.insert(0, str(RUNTIME))
_spec = importlib.util.spec_from_file_location(f"review_{TASK_ID}_generator", GENERATOR_PATH)
assert _spec and _spec.loader
GEN = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = GEN
_spec.loader.exec_module(GEN)


def _canonical_row() -> dict:
    with CANONICAL_PATH.open(encoding="utf-8") as handle:
        return next(
            json.loads(line)
            for line in handle
            if json.loads(line).get("task_id") == TASK_ID
        )


def _canonical_pairs() -> list[dict]:
    row = _canonical_row()
    test = row["test"]
    return list(row["train"]) + ([test] if isinstance(test, dict) else list(test))


def _components8_of_five(grid: list[list[int]]) -> list[set[tuple[int, int]]]:
    remaining = {
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 5
    }
    components: list[set[tuple[int, int]]] = []
    while remaining:
        start = min(remaining)
        remaining.remove(start)
        queue = deque([start])
        component = {start}
        while queue:
            r, c = queue.popleft()
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if not (dr or dc):
                        continue
                    neighbor = (r + dr, c + dc)
                    if neighbor in remaining:
                        remaining.remove(neighbor)
                        component.add(neighbor)
                        queue.append(neighbor)
        components.append(component)
    return components


def _normalized(component: set[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    r0 = min(r for r, _ in component)
    c0 = min(c for _, c in component)
    return tuple(sorted((r - r0, c - c0) for r, c in component))


def _is_exact_diagonal_triple(component: set[tuple[int, int]]) -> bool:
    return _normalized(component) in {
        ((0, 0), (1, 1), (2, 2)),
        ((0, 2), (1, 1), (2, 0)),
    }


def _contains_diagonal_window(component: set[tuple[int, int]]) -> bool:
    for r, c in component:
        for dc in (-1, 1):
            if {(r, c), (r + 1, c + dc), (r + 2, c + 2 * dc)} <= component:
                return True
    return False


def _scene_facts(grid: list[list[int]]) -> dict:
    components = _components8_of_five(grid)
    targets = [component for component in components if _is_exact_diagonal_triple(component)]
    decoys = [component for component in components if not _is_exact_diagonal_triple(component)]
    slopes = {
        "main" if _normalized(component) == ((0, 0), (1, 1), (2, 2)) else "anti"
        for component in targets
    }
    distractor_colors = {
        value
        for row in grid
        for value in row
        if value not in {0, 5}
    }
    return {
        "targets": targets,
        "decoys": decoys,
        "slopes": slopes,
        "distractor_colors": distractor_colors,
        "embedded_decoys": [
            component
            for component in decoys
            if len(component) > 3 and _contains_diagonal_window(component)
        ],
    }


def test_self_check_accepts_every_canonical_input():
    for index, pair in enumerate(_canonical_pairs()):
        assert GEN.self_check(pair["input"]) == [], index


def test_rule_hash_pins_the_canonical_program():
    source = _canonical_row()["program_solution"]
    expected = hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]
    assert getattr(GEN, "RULE_HASH", None) == expected


def test_four_example_schedule_teaches_component_scope_and_both_slopes():
    count = getattr(GEN, "EXAMPLES_NEEDED", 4)
    assert count == 4
    for start in range(8):
        lesson = [GEN.generate(20261002, start + offset, difficulty="medium") for offset in range(count)]
        facts = [_scene_facts(grid) for grid in lesson]
        assert any(item["embedded_decoys"] for item in facts), start
        assert set().union(*(item["slopes"] for item in facts)) == {"main", "anti"}, start
        assert any(item["distractor_colors"] for item in facts), start


def test_declared_exact_axes_are_observable_and_honored():
    assert callable(getattr(GEN, "observe_overrides", None))
    profiles = tuple(getattr(GEN, "SCENE_PROFILES", ()))
    assert len(profiles) >= 4
    for profile in profiles:
        grid = GEN.generate(
            7,
            3,
            difficulty="hard",
            grid_h=8,
            grid_w=9,
            scene_profile=profile,
        )
        assert GEN.self_check(grid) == []
        assert GEN.observe_overrides(grid) == {
            "grid_h": 8,
            "grid_w": 9,
            "scene_profile": profile,
        }


def test_rule_mirror_matches_every_canonical_output_and_generated_scene():
    assert callable(getattr(GEN, "rule_mirror", None))
    for index, pair in enumerate(_canonical_pairs()):
        assert GEN.rule_mirror(pair["input"]) == pair["output"], index
    for sample_index in range(24):
        grid = GEN.generate(99, sample_index, difficulty=("easy", "medium", "hard")[sample_index % 3])
        before = [row[:] for row in grid]
        output = GEN.rule_mirror(grid)
        assert grid == before
        facts = _scene_facts(grid)
        changed = {
            (r, c)
            for r in range(len(grid))
            for c in range(len(grid[0]))
            if grid[r][c] != output[r][c]
        }
        expected = {
            sorted(component)[1]
            for component in facts["targets"]
        }
        assert changed == expected


def test_unknown_override_and_invalid_difficulty_fail_loudly():
    with pytest.raises(ValueError, match="unknown override"):
        GEN.generate(1, 0, typo_axis=3)
    with pytest.raises(ValueError, match="difficulty"):
        GEN.generate(1, 0, difficulty="extreme")


def test_generation_is_deterministic_fresh_and_global_rng_pure():
    state = random.getstate()
    first = GEN.generate(12345, 7, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(12345, 7, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(left is not right for left, right in zip(first, second))
    first[0][0] = 9
    assert GEN.generate(12345, 7, difficulty="hard") == second


def test_pinned_profile_floor_has_support_in_every_difficulty_band():
    """Reproduce the repository gate's fixed 20-draw cross-band census."""
    canonical_profiles = {
        (
            len(pair["input"]),
            len(pair["input"][0]),
            len({value for row in pair["input"] for value in row}),
        )
        for pair in _canonical_pairs()
    }
    h_min = min(item[0] for item in canonical_profiles)
    h_max = max(item[0] for item in canonical_profiles)
    w_min = min(item[1] for item in canonical_profiles)
    w_max = max(item[1] for item in canonical_profiles)
    p_min = min(item[2] for item in canonical_profiles)
    p_max = max(item[2] for item in canonical_profiles)

    for band in ("easy", "medium", "hard"):
        support = 0
        for index in range(20):
            digest = hashlib.sha256(
                f"profile-floor:v1:{TASK_ID}:{band}:{index}".encode()
            ).hexdigest()
            seed = int(digest[:12], 16)
            grid = GEN.generate(seed, seed % 7919 + index, difficulty=band)
            profile = (
                len(grid),
                len(grid[0]),
                len({value for row in grid for value in row}),
            )
            in_envelope = (
                h_min <= profile[0] <= h_max
                and w_min <= profile[1] <= w_max
                and p_min <= profile[2] <= p_max
            )
            support += int(profile in canonical_profiles or in_envelope)
        assert support >= 1, (band, support)


def test_workspace_curriculum_probe_reports_no_surviving_declared_rivals(tmp_path):
    script = TEST_FILE.parents[1] / "workspace" / "probe_curriculum.py"
    report = tmp_path / "report.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(script),
            "--seed",
            "20261002",
            "--starts",
            "8",
            "--output",
            str(report),
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    payload = json.loads(report.read_text())
    assert payload["lesson_windows"] == 8
    assert payload["unique_sample_indices"] == 11
    assert all(not window["surviving_competitors"] for window in payload["windows"])
