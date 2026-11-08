from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SOURCE_REPO = Path(__file__).resolve().parents[3]
RUNTIME = SOURCE_REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

GENERATOR_PATH = SOURCE_REPO / "generators" / "e005c30bc59a" / "generator.py"
SPEC = importlib.util.spec_from_file_location("generator_e005c30bc59a", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _trace(grid: list[list[int]]) -> dict:
    h, w = len(grid), len(grid[0])
    sources = [
        (r, c, value)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value in {3, 4, 6, 7, 8, 9}
        and (r in {0, h - 1} or c in {0, w - 1})
    ]
    assert len(sources) == 1
    sr, sc, _ = sources[0]
    if sr == 0:
        direction = (1, 0)
    elif sr == h - 1:
        direction = (-1, 0)
    elif sc == 0:
        direction = (0, 1)
    else:
        direction = (0, -1)

    r, c = sr + direction[0], sc + direction[1]
    hits: list[int] = []
    states: set[tuple[int, int, int, int]] = set()
    termination = None
    for _ in range(5 * h * w):
        if not (0 <= r < h and 0 <= c < w):
            termination = "boundary"
            break
        state = (r, c, direction[0], direction[1])
        assert state not in states, "beam looped"
        states.add(state)
        value = grid[r][c]
        if value == 5:
            termination = "wall"
            break
        if value == 1:
            hits.append(value)
            direction = (-direction[1], -direction[0])
        elif value == 2:
            hits.append(value)
            direction = (direction[1], direction[0])
        r += direction[0]
        c += direction[1]
    return {
        "source": (sr, sc),
        "corner": sr in {0, h - 1} and sc in {0, w - 1},
        "hits": tuple(hits),
        "termination": termination,
    }


def test_every_regular_draw_has_unambiguous_source_and_reachable_mirror() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for index in range(128):
            grid = GEN.generate(10_000 + index, 20_000 + index, difficulty=difficulty)
            trace = _trace(grid)
            assert not trace["corner"]
            assert trace["hits"], (difficulty, index, grid)
            assert trace["termination"] in {"wall", "boundary"}


def test_exact_override_profiles_are_realized_at_boundary_sizes() -> None:
    mirror_profiles = tuple(GEN.MIRROR_PROFILES)
    wall_profiles = tuple(GEN.WALL_PROFILES)
    index = 0
    for grid_h, grid_w in ((8, 8), (14, 15)):
        for source_edge in GEN.SOURCE_EDGES:
            for mirror_profile in mirror_profiles:
                for wall_profile in wall_profiles:
                    overrides = {
                        "grid_h": grid_h,
                        "grid_w": grid_w,
                        "source_edge": source_edge,
                        "source_color": GEN.SOURCE_COLORS[index % len(GEN.SOURCE_COLORS)],
                        "mirror_profile": mirror_profile,
                        "wall_profile": wall_profile,
                    }
                    grid = GEN.generate(30_000 + index, 40_000 + index, difficulty="hard", **overrides)
                    assert GEN.self_check(grid) == []
                    assert GEN.observe_overrides(grid) == overrides
                    index += 1


def _canonical_row() -> dict:
    import json

    path = SOURCE_REPO / "shared" / "data" / "canonical" / "puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == GEN.TASK_ID or row.get("id") == GEN.TASK_ID:
                return row
    raise AssertionError("canonical row missing")


def test_canonical_inputs_are_owned_and_python_mirror_matches_outputs() -> None:
    row = _canonical_row()
    for pair in list(row["train"]) + list(row["test"]):
        assert GEN.self_check(pair["input"]) == []
        assert GEN.rule_mirror(pair["input"]) == pair["output"]


def test_constant_seven_is_a_true_canonical_shortcut_but_generated_non7_refutes_it() -> None:
    row = _canonical_row()
    shortcut = GEN.CANONICAL_SHORTCUTS["constant_trail_color_7"]
    for pair in list(row["train"]) + list(row["test"]):
        assert shortcut(pair["input"]) == pair["output"]

    grid = GEN.generate(51_001, 0, difficulty="medium")
    analysis = GEN._analysis(grid)
    assert analysis["source_color"] != 7
    assert shortcut(grid) != GEN.rule_mirror(grid)


def test_every_four_consecutive_demos_refute_all_declared_competitors() -> None:
    for difficulty in ("easy", "medium", "hard"):
        for start in range(16):
            pairs = []
            for offset in range(GEN.EXAMPLES_NEEDED + 1):
                grid = GEN.generate(60_000 + start, start + offset, difficulty=difficulty)
                pairs.append({"input": grid, "output": GEN.rule_mirror(grid)})
            demos, query = pairs[:-1], pairs[-1]
            assert GEN.lesson_identifiable(demos, query) == []
            for name, competitor in GEN.LESSON_COMPETITORS.items():
                assert any(
                    competitor(pair["input"]) != pair["output"] for pair in demos
                ), (difficulty, start, name)


def test_determinism_fresh_returns_and_unknown_override_rejection() -> None:
    import copy
    import random

    state = random.getstate()
    first = GEN.generate(777, 888, difficulty="hard")
    assert random.getstate() == state
    second = GEN.generate(777, 888, difficulty="hard")
    assert first == second
    assert first is not second
    assert all(a is not b for a, b in zip(first, second))
    first[0][0] = 9 if first[0][0] != 9 else 8
    assert GEN.generate(777, 888, difficulty="hard") == second

    try:
        GEN.generate(1, 2, unknown_axis=3)
    except ValueError as exc:
        assert "unknown override" in str(exc)
    else:
        raise AssertionError("unknown override was silently ignored")


def test_each_semantic_witness_fires_in_each_band() -> None:
    for difficulty in ("easy", "medium", "hard"):
        grids = [
            GEN.generate(70_000 + index, index, difficulty=difficulty)
            for index in range(48)
        ]
        for name, witness in GEN.SEMANTIC_WITNESSES.items():
            assert any(witness(grid) for grid in grids), (difficulty, name)


def test_hard_boundary_override_does_not_inherit_wall_stop_role_constraints() -> None:
    """A wall-profile override must not keep an incompatible default route template."""
    import signal

    class DeadlineExceeded(Exception):
        pass

    def expire(_signum, _frame):
        raise DeadlineExceeded("generation exceeded 0.5 seconds")

    previous = signal.signal(signal.SIGALRM, expire)
    try:
        for wall_profile in (
            "boundary_none",
            "boundary_one_decoy",
            "boundary_two_decoys",
        ):
            signal.setitimer(signal.ITIMER_REAL, 0.5)
            try:
                grid = GEN.generate(
                    0,
                    3,  # hard role 3 normally uses a three-mirror wall-stop template
                    difficulty="hard",
                    wall_profile=wall_profile,
                )
            finally:
                signal.setitimer(signal.ITIMER_REAL, 0)
            observed = GEN.observe_overrides(grid)
            assert observed["wall_profile"] == wall_profile
            assert observed["mirror_profile"] == "three_hit_one_decoy"
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)


def test_override_profiler_records_success_and_error_rows() -> None:
    profiler_path = (
        SOURCE_REPO
        / "generators"
        / "e005c30bc59a"
        / "workspace"
        / "override_contract_profiler.py"
    )
    spec = importlib.util.spec_from_file_location("override_contract_profiler", profiler_path)
    assert spec and spec.loader
    profiler = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(profiler)

    def fake_generate(seed, sample_index, *, difficulty, axis):
        if axis == "bad":
            raise ValueError("deliberate test failure")
        return [[seed, sample_index, len(difficulty), 1]]

    report = profiler.profile_cases(
        fake_generate,
        lambda grid: {"observed": grid[0][-1]},
        cases=({"axis": "ok"}, {"axis": "bad"}),
        bands=("easy",),
        seed=7,
        sample_index=3,
        deadline_seconds=0.5,
        slow_threshold_seconds=-1.0,
    )
    assert report["case_count"] == 2
    assert report["attempt_count"] == 2
    assert [row["status"] for row in report["rows"]] == ["ok", "error"]
    assert report["rows"][0]["observed"] == {"observed": 1}
    assert "deliberate test failure" in report["rows"][1]["error"]


def test_override_profiler_cli_loads_generator_from_repo(tmp_path) -> None:
    import json
    import subprocess

    profiler_path = (
        SOURCE_REPO
        / "generators"
        / "e005c30bc59a"
        / "workspace"
        / "override_contract_profiler.py"
    )
    output_path = tmp_path / "profile.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(profiler_path),
            "--repo",
            str(SOURCE_REPO),
            "--bands",
            "easy",
            "--deadline-seconds",
            "0.25",
            "--slow-threshold-seconds",
            "999",
            "--out",
            str(output_path),
        ],
        cwd=SOURCE_REPO,
        text=True,
        capture_output=True,
        timeout=20,
    )
    assert completed.returncode == 0, completed.stderr
    report = json.loads(output_path.read_text())
    assert report["case_count"] > 0
    assert report["attempt_count"] == report["case_count"]
    assert report["slow_or_failed_count"] == 0
