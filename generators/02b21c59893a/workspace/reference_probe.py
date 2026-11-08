"""Independent oracle and curriculum probe for ARC task 02b21c59893a.

This module deliberately does not import production rule helpers.  It gives tests
and later reviewers a portable way to inspect canonical pairs, compute the
selected transformation, execute the selected Racket source, and enumerate
lesson/rival outcomes.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any, Callable

TASK = "02b21c59893a"
CANONICAL_PROFILES = {(8, 9, 6), (9, 10, 7), (7, 11, 5), (9, 11, 7)}


def _load_reviewer_support():
    try:
        import reviewer_support  # type: ignore
        return reviewer_support
    except ImportError:
        here = Path(__file__).resolve()
        for parent in here.parents:
            for candidate in (parent / "shared/runtime", parent / "runtime", parent):
                if (candidate / "reviewer_support.py").is_file():
                    sys.path.insert(0, str(candidate))
                    import reviewer_support  # type: ignore
                    return reviewer_support
        raise


_support = _load_reviewer_support()
ROOT = _support.find_root(__file__)


def _generator_candidates(root: Path) -> list[Path]:
    return [
        root / "generators" / TASK / "generator.py",
        root / "puzzle_generators" / "per_puzzle" / TASK / "generator.py",
    ]


def load_generator(path: str | Path | None = None):
    if path is None:
        path = next((candidate for candidate in _generator_candidates(ROOT) if candidate.is_file()), None)
    if path is None:
        raise FileNotFoundError(f"cannot locate generator {TASK} under {ROOT}")
    path = Path(path).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict[str, Any]]:
    return _support.canonical_pairs(TASK, root=ROOT, labeled_only=True)


def canonical_program() -> str:
    path = _support.canonical_path(ROOT)
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK and row.get("program_solution"):
                return str(row["program_solution"])
    raise KeyError(TASK)


def rectangular_grid(grid: Any) -> tuple[int, int]:
    if not isinstance(grid, list) or not grid or not isinstance(grid[0], list) or not grid[0]:
        raise ValueError("grid must be a nonempty list of nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, list) or len(row) != width for row in grid):
        raise ValueError("grid must be rectangular")
    if any(type(value) is not int or not 0 <= value <= 9 for row in grid for value in row):
        raise ValueError("grid cells must be integer colours 0..9")
    return len(grid), width


def anchors_payload(grid: Any) -> tuple[tuple[int, int], list[tuple[int, int]], list[tuple[int, int, int]]]:
    height, width = rectangular_grid(grid)
    blues: list[tuple[int, int]] = []
    reds: list[tuple[int, int]] = []
    payload: list[tuple[int, int, int]] = []
    for row in range(height):
        for col in range(width):
            value = grid[row][col]
            if value == 1:
                blues.append((row, col))
            elif value == 2:
                reds.append((row, col))
            elif value != 0:
                payload.append((row, col, value))
    if len(blues) != 1:
        raise ValueError(f"expected exactly one blue anchor, found {len(blues)}")
    if not reds:
        raise ValueError("expected at least one red anchor")
    if not payload:
        raise ValueError("expected nonempty payload")
    return blues[0], reds, payload


def _translate(
    grid: Any,
    *,
    source: tuple[int, int],
    destination: tuple[int, int],
    all_or_nothing: bool = False,
) -> list[list[int]]:
    height, width = rectangular_grid(grid)
    _, _, payload = anchors_payload(grid)
    moved = [
        (destination[0] + row - source[0], destination[1] + col - source[1], value)
        for row, col, value in payload
    ]
    out = [[0] * width for _ in range(height)]
    out[destination[0]][destination[1]] = 2
    if all_or_nothing and any(not (0 <= row < height and 0 <= col < width) for row, col, _ in moved):
        return out
    for row, col, value in moved:
        if 0 <= row < height and 0 <= col < width:
            out[row][col] = value
    return out


def oracle_output(grid: Any) -> list[list[int]]:
    source, reds, _ = anchors_payload(grid)
    return _translate(grid, source=source, destination=reds[-1])


def always_origin_rival(grid: Any) -> list[list[int]]:
    _, reds, _ = anchors_payload(grid)
    return _translate(grid, source=(0, 0), destination=reds[-1])


def payload_bbox_rival(grid: Any) -> list[list[int]]:
    _, reds, payload = anchors_payload(grid)
    source = (min(row for row, _, _ in payload), min(col for _, col, _ in payload))
    return _translate(grid, source=source, destination=reds[-1])


def first_red_rival(grid: Any) -> list[list[int]]:
    source, reds, _ = anchors_payload(grid)
    return _translate(grid, source=source, destination=reds[0])


def all_or_nothing_clip_rival(grid: Any) -> list[list[int]]:
    source, reds, _ = anchors_payload(grid)
    return _translate(grid, source=source, destination=reds[-1], all_or_nothing=True)


RIVALS: dict[str, Callable[[Any], list[list[int]]]] = {
    "always_origin": always_origin_rival,
    "payload_bbox_origin": payload_bbox_rival,
    "first_red": first_red_rival,
    "all_or_nothing_clip": all_or_nothing_clip_rival,
}


def profile_tuple(grid: Any) -> tuple[int, int, int]:
    height, width = rectangular_grid(grid)
    return height, width, len({value for row in grid for value in row})


def clipping_count(grid: Any) -> int:
    height, width = rectangular_grid(grid)
    source, reds, payload = anchors_payload(grid)
    destination = reds[-1]
    return sum(
        not (0 <= destination[0] + row - source[0] < height and 0 <= destination[1] + col - source[1] < width)
        for row, col, _ in payload
    )


def observed_profile(grid: Any) -> str:
    shape = profile_tuple(grid)
    _, reds, _ = anchors_payload(grid)
    clipped = clipping_count(grid)
    if shape == (8, 9, 6) and len(reds) == 1 and clipped == 0:
        return "canonical_anchor"
    if shape == (9, 10, 7) and len(reds) == 1 and clipped == 0:
        return "offset_anchor"
    if shape == (7, 11, 5) and len(reds) == 2 and clipped == 0:
        return "last_red"
    if shape == (9, 11, 7) and len(reds) == 2 and clipped > 0:
        return "last_red_clip"
    if len(reds) == 1 and clipped > 0 and shape not in CANONICAL_PROFILES:
        return "clip_multicolor"
    raise ValueError(f"grid does not match a declared profile: shape={shape} reds={len(reds)} clipped={clipped}")


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    src_dir = ROOT / "src"
    if src_dir.is_dir():
        sys.path.insert(0, str(src_dir))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": canonical_program(), "grids": grids}), encoding="utf-8"
        )
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('parity-request.json').read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request['grids']]))
finally:
    bridge.shutdown()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        return json.loads(result["stdout"])


def lesson_matrix(gen, *, starts: int = 20) -> dict[str, Any]:
    failures: list[dict[str, Any]] = []
    checked = 0
    for band in ("easy", "medium", "hard"):
        for start in range(starts):
            pairs = []
            for step in range(5):
                grid = gen.generate(70_000 + start, start + step, difficulty=band)
                pairs.append({"input": grid, "output": oracle_output(grid)})
            for query_index, query in enumerate(pairs):
                demos = [pair for index, pair in enumerate(pairs) if index != query_index]
                checked += 1
                reasons = gen.lesson_identifiable(demos, query)
                if reasons:
                    failures.append({
                        "band": band,
                        "start": start,
                        "query_index": query_index,
                        "reasons": reasons,
                    })
    return {"task_id": TASK, "checked_rotations": checked, "failures": failures}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--starts", type=int, default=20)
    parser.add_argument("--out", default="")
    args = parser.parse_args()
    gen = load_generator(os.environ.get("GENERATOR_UNDER_TEST"))
    report = lesson_matrix(gen, starts=args.starts)
    text = json.dumps(report, indent=2, sort_keys=True)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8")
    print(text)
    return 1 if report["failures"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
