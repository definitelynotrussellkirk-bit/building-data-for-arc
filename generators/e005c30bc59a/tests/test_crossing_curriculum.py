from __future__ import annotations

from copy import deepcopy
import importlib.util
import sys
from pathlib import Path


SOURCE_REPO = Path(__file__).resolve().parents[3]
RUNTIME = SOURCE_REPO / "shared" / "runtime"
if str(RUNTIME) not in sys.path:
    sys.path.insert(0, str(RUNTIME))

GENERATOR_PATH = SOURCE_REPO / "generators" / "e005c30bc59a" / "generator.py"
SPEC = importlib.util.spec_from_file_location("generator_e005c30bc59a_crossing", GENERATOR_PATH)
assert SPEC and SPEC.loader
GEN = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(GEN)


def _stop_on_revisited_cell(grid: list[list[int]]) -> list[list[int]]:
    """Plausible rival: beam stops when it reaches any previously visited cell."""
    analysis = GEN._analysis(grid)
    assert analysis["errors"] == []
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    r, c = analysis["source"]
    direction = GEN._inward(analysis["source_edge"])
    r += direction[0]
    c += direction[1]
    visited: set[tuple[int, int]] = set()

    for _ in range(5 * h * w + 8):
        if not (0 <= r < h and 0 <= c < w):
            break
        if (r, c) in visited:
            break
        visited.add((r, c))
        value = grid[r][c]
        if value == 0:
            out[r][c] = analysis["source_color"]
        elif value == 5:
            break
        elif value in (1, 2):
            direction = GEN._bounce(direction, value)
        else:
            break
        r += direction[0]
        c += direction[1]
    return out


def test_every_four_demo_lesson_refutes_stop_on_revisited_cell() -> None:
    """Each cyclic lesson needs a crossing that visibly continues afterward."""
    for difficulty in ("easy", "medium", "hard"):
        for start in range(8):
            grids = [
                GEN.generate(81_000 + start, start + offset, difficulty=difficulty)
                for offset in range(GEN.EXAMPLES_NEEDED)
            ]
            assert any(
                _stop_on_revisited_cell(grid) != GEN.rule_mirror(grid)
                for grid in grids
            ), (difficulty, start)


def test_crossing_revisit_probe_cli_reports_canonical_fit_and_lesson_coverage(tmp_path) -> None:
    import json
    import subprocess

    probe_path = (
        SOURCE_REPO
        / "generators"
        / "e005c30bc59a"
        / "workspace"
        / "crossing_revisit_probe.py"
    )
    assert probe_path.is_file(), "reusable crossing probe is missing"
    output_path = tmp_path / "crossing-report.json"
    completed = subprocess.run(
        [
            sys.executable,
            str(probe_path),
            "--repo",
            str(SOURCE_REPO),
            "--lessons-per-band",
            "2",
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
    assert report["canonical"]["rival_fits_all_train_demonstrations"] is True
    assert report["canonical"]["intended_matches_all_public_pairs"] is True
    for band in ("easy", "medium", "hard"):
        assert report["bands"][band]["lesson_count"] == 2
        assert report["bands"][band]["all_lessons_refute_rival"] is True
        assert report["bands"][band]["generator_rule_matches_independent_trace"] is True
