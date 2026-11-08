"""Independent geometry oracle and repeatable audit for ``bdcb4c9eb6bd``.

This module is review tooling, not the label authority.  It deliberately does
not import implementation helpers from ``generator.py``.  The optional Racket
path executes the selected canonical program and never silently substitutes the
Python mirror.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Iterable

TASK = "bdcb4c9eb6bd"
ROOT = Path(__file__).resolve().parents[3]
_RUNTIME = ROOT / "shared" / "runtime"
if str(_RUNTIME) not in sys.path:
    sys.path.insert(0, str(_RUNTIME))

from reviewer_support import canonical_pairs as _portable_canonical_pairs  # noqa: E402


def load_generator(path: str | os.PathLike[str] | None = None):
    path = Path(path or ROOT / "generators" / TASK / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs(*, labeled_only: bool = True) -> list[dict]:
    return _portable_canonical_pairs(TASK, root=ROOT, labeled_only=labeled_only)


def mode(grid: list[list[int]]) -> int:
    counts = Counter(value for row in grid for value in row)
    if not counts:
        raise ValueError("empty grid")
    return counts.most_common(1)[0][0]


def components(grid: list[list[int]], color: int = 1) -> list[list[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    todo = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
    result: list[list[tuple[int, int]]] = []
    while todo:
        first = min(todo)
        todo.remove(first)
        queue = deque([first])
        cells: list[tuple[int, int]] = []
        while queue:
            r, c = queue.popleft()
            cells.append((r, c))
            for dr, dc in ((-1, 0), (0, -1), (0, 1), (1, 0)):
                point = (r + dr, c + dc)
                if point in todo:
                    todo.remove(point)
                    queue.append(point)
        result.append(sorted(cells))
    return result


def rectangle_facts(cells: Iterable[tuple[int, int]]) -> dict:
    cells = set(cells)
    if not cells:
        raise ValueError("empty component")
    r0 = min(r for r, _ in cells)
    r1 = max(r for r, _ in cells)
    c0 = min(c for _, c in cells)
    c1 = max(c for _, c in cells)
    perimeter = {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }
    missing = sorted(perimeter - cells)
    extras = sorted(cells - perimeter)
    if extras or len(missing) != 1:
        raise ValueError(
            f"component is not a one-gap rectangle: extras={extras}, missing={missing}"
        )
    gap = missing[0]
    if gap in {(r0, c0), (r0, c1), (r1, c0), (r1, c1)}:
        raise ValueError("corner gaps are outside the task grammar")
    if gap[0] == r0:
        side = "up"
    elif gap[0] == r1:
        side = "down"
    elif gap[1] == c0:
        side = "left"
    elif gap[1] == c1:
        side = "right"
    else:
        raise ValueError("gap is not on the bounding-box perimeter")
    return {
        "bbox": (r0, c0, r1, c1),
        "height": r1 - r0 + 1,
        "width": c1 - c0 + 1,
        "gap": gap,
        "side": side,
    }


def observed(grid: list[list[int]]) -> dict:
    facts = [rectangle_facts(cells) for cells in components(grid)]
    return {
        "scene_profile": f"{len(grid)}x{len(grid[0])}",
        "background": mode(grid),
        "rectangle_count": len(facts),
        "sizes": tuple((item["height"], item["width"]) for item in facts),
        "sides": tuple(item["side"] for item in facts),
        "touches_border": tuple(
            item["bbox"][0] == 0
            or item["bbox"][1] == 0
            or item["bbox"][2] == len(grid) - 1
            or item["bbox"][3] == len(grid[0]) - 1
            for item in facts
        ),
    }


def intended_output(
    grid: list[list[int]], *, only_four_by_four: bool = False
) -> list[list[int]]:
    """Independent mirror of the documented hook rule.

    The input is never mutated.  ``only_four_by_four`` is the strongest
    canonical-fitting shortcut found in review: it ignores every otherwise
    lawful rectangle whose bounding box is not 4x4.
    """
    bg = mode(grid)
    out = deepcopy(grid)
    h, w = len(grid), len(grid[0])
    for cells in components(grid):
        facts = rectangle_facts(cells)
        r0, c0, r1, c1 = facts["bbox"]
        if only_four_by_four and (facts["height"], facts["width"]) != (4, 4):
            continue
        for r in range(r0 + 1, r1):
            for c in range(c0 + 1, c1):
                if out[r][c] == bg:
                    out[r][c] = 2
        gr, gc = facts["gap"]
        if facts["side"] == "up":
            beam = ((r, gc) for r in range(0, r0 + 1))
        elif facts["side"] == "down":
            beam = ((r, gc) for r in range(r1, h))
        elif facts["side"] == "left":
            beam = ((gr, c) for c in range(0, c0 + 1))
        else:
            beam = ((gr, c) for c in range(c1, w))
        for r, c in beam:
            if out[r][c] == bg:
                out[r][c] = 2
    return out


def four_by_four_only(grid: list[list[int]]) -> list[list[int]]:
    return intended_output(grid, only_four_by_four=True)


def non_four_by_four_witness(grid: list[list[int]]) -> bool:
    return any(
        (facts["height"], facts["width"]) != (4, 4)
        for facts in (rectangle_facts(cells) for cells in components(grid))
    )


def witness_input() -> list[list[int]]:
    """Exact 7x9 counterexample: a 4x5 right-open rectangle."""
    bg = 5
    g = [[bg] * 9 for _ in range(7)]
    r0, c0, rh, rw = 1, 2, 4, 5
    for c in range(c0, c0 + rw):
        g[r0][c] = g[r0 + rh - 1][c] = 1
    for r in range(r0, r0 + rh):
        g[r][c0] = g[r][c0 + rw - 1] = 1
    g[r0 + 1][c0 + rw - 1] = bg
    return g


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Execute the canonical Racket rule in the repository runtime."""
    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    canonical = None
    with (ROOT / "shared" / "data" / "canonical" / "puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                canonical = row
                break
    if canonical is None:
        raise ValueError(f"canonical task {TASK} is missing")

    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        request = {"program": canonical["program_solution"], "grids": grids}
        (stage / "parity-request.json").write_text(json.dumps(request))
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('parity-request.json').read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in request['grids']]))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["timed_out"] or result["exit_code"]:
            raise RuntimeError(f"Racket parity failed: {result['stderr']} {result['stdout']}")
        return json.loads(result["stdout"])


def audit(module, count: int) -> tuple[dict, list[list[list[int]]]]:
    report: dict = {
        "schema": f"{TASK}-independent-audit-v1",
        "version": module.VERSION,
        "canonical": {},
        "bands": {},
    }
    canonical = canonical_pairs()
    report["canonical"] = {
        "pairs": len(canonical),
        "oracle_matches": sum(intended_output(pair["input"]) == pair["output"] for pair in canonical),
        "shortcut_matches": sum(four_by_four_only(pair["input"]) == pair["output"] for pair in canonical),
        "self_check_errors": [module.self_check(pair["input"]) for pair in canonical],
    }
    retained = [pair["input"] for pair in canonical]
    for band in (None, "easy", "medium", "hard"):
        counts = Counter()
        unique = set()
        for index in range(count):
            grid = module.generate(5100 + index, index, difficulty=band)
            counts["draws"] += 1
            counts["valid"] += not module.self_check(grid)
            counts["deterministic"] += grid == module.generate(5100 + index, index, difficulty=band)
            counts["non_4x4"] += non_four_by_four_witness(grid)
            counts["multi_object"] += len(components(grid)) > 1
            counts["border_touching"] += any(observed(grid)["touches_border"])
            counts["shortcut_disagreement"] += intended_output(grid) != four_by_four_only(grid)
            unique.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            if index < 8:
                retained.append(grid)
        counts["unique_inputs"] = len(unique)
        report["bands"][str(band)] = dict(counts)
    witness = witness_input()
    report["witness"] = {
        "input": witness,
        "intended_python": intended_output(witness),
        "four_by_four_only": four_by_four_only(witness),
    }
    retained.append(witness)
    return report, retained


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report, grids = audit(module, args.count)
    generator_path = args.generator or ROOT / "generators" / TASK / "generator.py"
    report["generator_sha256"] = hashlib.sha256(Path(generator_path).read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["racket"] = {"status": "not_requested", "checked": 0}
    exit_code = int(
        report["canonical"]["oracle_matches"] != report["canonical"]["pairs"]
        or any(report["canonical"]["self_check_errors"])
        or any(values["valid"] != values["draws"] for values in report["bands"].values())
    )
    if args.racket:
        try:
            outputs = racket_outputs(grids)
            mismatches = [
                index for index, (grid, output) in enumerate(zip(grids, outputs))
                if intended_output(grid) != output
            ]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
                "mismatches": mismatches,
            }
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:  # retained as explicit unavailable evidence
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"canonical": report["canonical"], "bands": report["bands"], "racket": report["racket"]}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
