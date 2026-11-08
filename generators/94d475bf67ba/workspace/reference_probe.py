"""Independent geometry oracle and reproducible audit for 94d475bf67ba.

This module is reviewer tooling, not a label authority.  Its Python oracle is
checked against the canonical Racket program by ``--racket`` and by the focused
test suite; it never silently replaces Racket when parity is requested.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Iterable

TASK_ID = "94d475bf67ba"

# Make the helper work both in the source library and the staged task-test tree.
_SOURCE_ROOT = Path(__file__).resolve().parents[3]
for candidate in (_SOURCE_ROOT / "shared/runtime", _SOURCE_ROOT / "runtime"):
    if candidate.is_dir() and str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))
from reviewer_support import canonical_pairs as _canonical_pairs, find_root  # noqa: E402

ROOT = find_root(__file__)


def load_generator(path: str | os.PathLike[str] | None = None):
    candidates = []
    if path:
        candidates.append(Path(path))
    candidates.extend(
        [
            ROOT / "generators" / TASK_ID / "generator.py",
            ROOT / "puzzle_generators" / "per_puzzle" / TASK_ID / "generator.py",
        ]
    )
    source = next((candidate.resolve() for candidate in candidates if candidate.is_file()), None)
    if source is None:
        raise FileNotFoundError(f"cannot locate generator.py for {TASK_ID}: {candidates}")
    spec = importlib.util.spec_from_file_location("reviewed_94d475bf67ba", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import generator at {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    return _canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def _canonical_row() -> dict:
    paths = (ROOT / "shared/data/canonical/puzzles.jsonl", ROOT / "data/canonical/puzzles.jsonl")
    path = next((candidate for candidate in paths if candidate.is_file()), None)
    if path is None:
        raise FileNotFoundError(f"canonical ledger absent under {ROOT}")
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                row = json.loads(line)
                if row.get("task_id") == TASK_ID:
                    return row
    raise KeyError(TASK_ID)


def _bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    if not cells:
        raise ValueError("empty component has no bounding box")
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def _outline(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    top, left, bottom, right = box
    return (
        {(top, c) for c in range(left, right + 1)}
        | {(bottom, c) for c in range(left, right + 1)}
        | {(r, left) for r in range(top, bottom + 1)}
        | {(r, right) for r in range(top, bottom + 1)}
    )


def _components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    height, width = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(height) for c in range(width) if grid[r][c] == color}
    result: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        component = {start}
        stack = [start]
        while stack:
            r, c = stack.pop()
            for point in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if point in unseen:
                    unseen.remove(point)
                    component.add(point)
                    stack.append(point)
        result.append(component)
    return result


def frame_specs(grid: list[list[int]], *, operative_only: bool = False) -> list[dict]:
    """Return exact monochrome rectangle outlines, sorted largest to smallest.

    A 2-by-N terminal outline is retained for structural inspection but is not
    operative under the canonical Racket rule, whose frame predicate requires
    both dimensions to be at least three.
    """
    specs = []
    colors = sorted({value for row in grid for value in row if value != 0})
    for color in colors:
        components = _components(grid, color)
        if len(components) != 1:
            continue
        cells = components[0]
        box = _bbox(cells)
        height = box[2] - box[0] + 1
        width = box[3] - box[1] + 1
        if height < 2 or width < 2 or cells != _outline(box):
            continue
        operative = height >= 3 and width >= 3
        if operative_only and not operative:
            continue
        specs.append(
            {
                "color": color,
                "box": box,
                "height": height,
                "width": width,
                "area": height * width,
                "operative": operative,
            }
        )
    return sorted(specs, key=lambda item: item["area"], reverse=True)


def _inside(box: tuple[int, int, int, int], r: int, c: int) -> bool:
    top, left, bottom, right = box
    return top < r < bottom and left < c < right


def _fill_with_selector(grid: list[list[int]], selector) -> list[list[int]]:
    frames = frame_specs(grid, operative_only=True)
    output = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            enclosing = [frame for frame in frames if _inside(frame["box"], r, c)]
            if enclosing:
                output[r][c] = selector(enclosing)["color"]
    return output


def expected_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent mirror of the selected rule: smallest enclosing exact frame."""
    return _fill_with_selector(grid, lambda frames: min(frames, key=lambda item: item["area"]))


def outermost_output(grid: list[list[int]]) -> list[list[int]]:
    return _fill_with_selector(grid, lambda frames: max(frames, key=lambda item: item["area"]))


def maximum_color_output(grid: list[list[int]]) -> list[list[int]]:
    return _fill_with_selector(grid, lambda frames: max(frames, key=lambda item: item["color"]))


def two_levels_output(grid: list[list[int]]) -> list[list[int]]:
    """Plausible canonical shortcut: ignore every frame below the two largest.

    It reproduces all public canonical pairs because their third colored object
    has height two and is therefore not an operative frame.  A generated deep
    third frame is the required counterexample.
    """
    frames = frame_specs(grid, operative_only=True)[:2]
    output = deepcopy(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 0:
                continue
            enclosing = [frame for frame in frames if _inside(frame["box"], r, c)]
            if enclosing:
                output[r][c] = min(enclosing, key=lambda item: item["area"])["color"]
    return output


def observed_axes(grid: list[list[int]]) -> dict[str, int]:
    colors = {value for row in grid for value in row if value != 0}
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_frames": len(colors)}


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Require and execute the real canonical Racket program for parity checks."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile

    src = ROOT / "src"
    if src.is_dir() and str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    row = _canonical_row()
    program = row.get("program_solution") or row.get("racket_target", {}).get("target_code")
    if not program:
        raise KeyError("canonical row has no executable program_solution")
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK_ID)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": program, "grids": grids}), encoding="utf-8"
        )
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path("parity-request.json").read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    outputs=[runner._apply_rule(bridge,name,grid) for grid in request["grids"]]
    print(json.dumps(outputs))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket parity worker failed: {result['stderr']} {result['stdout']}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket parity worker returned an incomplete batch")
        return outputs


def audit(module, per_band: int) -> tuple[dict, list[list[list[int]]]]:
    report = {
        "schema": f"{TASK_ID}-independent-audit-v1",
        "task_id": TASK_ID,
        "generator_version": getattr(module, "VERSION", None),
        "rule_hash": getattr(module, "RULE_HASH", None),
        "per_band": per_band,
        "canonical": {},
        "bands": {},
    }
    canonical = canonical_pairs()
    report["canonical"] = {
        "pairs": len(canonical),
        "python_matches": sum(expected_output(pair["input"]) == pair["output"] for pair in canonical),
        "self_check_failures": [module.self_check(pair["input"]) for pair in canonical],
        "two_level_shortcut_matches": sum(
            two_levels_output(pair["input"]) == pair["output"] for pair in canonical
        ),
    }
    retained = [pair["input"] for pair in canonical]
    for band in (None, "easy", "medium", "hard"):
        counts = Counter()
        profiles: Counter[tuple[int, int, int]] = Counter()
        layouts = set()
        for i in range(per_band):
            seed = 940_000 + i
            index = i * 11
            grid = module.generate(seed, index, difficulty=band)
            counts["samples"] += 1
            counts["self_check_failures"] += bool(module.self_check(grid))
            counts["nondeterministic"] += grid != module.generate(seed, index, difficulty=band)
            counts["changed"] += expected_output(grid) != grid
            counts["outermost_disagreements"] += outermost_output(grid) != expected_output(grid)
            counts["max_color_disagreements"] += maximum_color_output(grid) != expected_output(grid)
            counts["two_level_disagreements"] += two_levels_output(grid) != expected_output(grid)
            observed = observed_axes(grid)
            profiles[(observed["grid_h"], observed["grid_w"], observed["n_frames"])] += 1
            layouts.add(tuple((item["color"], item["box"]) for item in frame_specs(grid)))
            if i < 4:
                retained.append(grid)
        report["bands"][str(band)] = {
            **dict(counts),
            "profiles": {"x".join(map(str, key)): value for key, value in sorted(profiles.items())},
            "distinct_frame_layouts": len(layouts),
        }
    return report, retained


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--per-band", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.per_band < 1:
        parser.error("--per-band must be positive")
    module = load_generator(args.generator)
    report, grids = audit(module, args.per_band)
    source = Path(args.generator).resolve() if args.generator else Path(module.__file__).resolve()
    report["generator_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["racket"] = {"status": "not_requested", "checked": 0}
    exit_code = int(
        report["canonical"]["python_matches"] != report["canonical"]["pairs"]
        or any(row["self_check_failures"] or row["nondeterministic"] for row in report["bands"].values())
    )
    if args.racket:
        try:
            outputs = racket_outputs(grids)
            mismatches = [index for index, (grid, output) in enumerate(zip(grids, outputs)) if expected_output(grid) != output]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatches": mismatches,
            }
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:  # requested parity must fail loudly
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
