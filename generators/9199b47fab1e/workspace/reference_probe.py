"""Independent oracle and audit helpers for task 9199b47fab1e.

The Python oracle is supplementary test tooling. The canonical Racket program
remains the label authority; ``racket_outputs`` executes that source when Racket
is available. This module deliberately does not import production generator
helpers when computing outputs or structural observations.
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

# The copied task-test runtime exposes reviewer_support directly. The source
# repository keeps it under shared/runtime, so add that portable location only
# when needed.
HERE = Path(__file__).resolve()
for candidate in (HERE.parent, *HERE.parents):
    runtime = candidate / "shared" / "runtime"
    if runtime.is_dir():
        sys.path.insert(0, str(runtime))
        break

from reviewer_support import canonical_pairs as _canonical_pairs, find_root

TASK_ID = "9199b47fab1e"
ROOT = find_root(__file__)
TASK_DIR = HERE.parents[1]
SHAPE_OPTIONS = (
    "9x9", "9x13", "10x12", "11x11", "11x13",
    "12x14", "14x16", "16x18", "18x20",
)


def load_generator(path: str | os.PathLike[str] | None = None):
    path = Path(path or TASK_DIR / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs() -> list[dict]:
    return _canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def open_components(grid: list[list[int]]) -> list[list[tuple[int, int]]]:
    """Cardinal components made of rule-traversable cells (0 or 2)."""
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    result: list[list[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] not in (0, 2) or (r, c) in seen:
                continue
            component: list[tuple[int, int]] = []
            queue = deque([(r, c)])
            seen.add((r, c))
            while queue:
                point = queue.popleft()
                component.append(point)
                pr, pc = point
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = pr + dr, pc + dc
                    if (0 <= nr < h and 0 <= nc < w
                            and grid[nr][nc] in (0, 2)
                            and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(component)
    return result


def rule_output(grid: list[list[int]]) -> list[list[int]]:
    """Independent multi-source BFS mirror of the selected rule."""
    if not grid or not grid[0]:
        raise ValueError("expected nonempty grid")
    h, w = len(grid), len(grid[0])
    dist: dict[tuple[int, int], int] = {}
    queue: deque[tuple[int, int]] = deque()
    for r, row in enumerate(grid):
        if len(row) != w:
            raise ValueError("ragged grid")
        for c, value in enumerate(row):
            if value == 2:
                dist[(r, c)] = 0
                queue.append((r, c))
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if (0 <= nr < h and 0 <= nc < w
                    and (nr, nc) not in dist
                    and grid[nr][nc] in (0, 2)):
                dist[(nr, nc)] = dist[(r, c)] + 1
                queue.append((nr, nc))
    out = deepcopy(grid)
    colors = (3, 4, 5)
    for (r, c), distance in dist.items():
        out[r][c] = colors[distance % 3]
    return out


def nearest_seed_manhattan_ignoring_walls(grid: list[list[int]]) -> list[list[int]]:
    """Plausible wrong rule: walls do not block distance propagation.

    Wall pixels are preserved, but every 0/2 cell is recolored by Manhattan
    distance to the nearest seed. This is exactly the shortcut implicated by the
    prior audit when demonstrations contained non-consequential walls.
    """
    seeds = [
        (r, c)
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 2
    ]
    if not seeds:
        return deepcopy(grid)
    out = deepcopy(grid)
    colors = (3, 4, 5)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value in (0, 2):
                distance = min(abs(r - sr) + abs(c - sc) for sr, sc in seeds)
                out[r][c] = colors[distance % 3]
    return out


def color_8_only_barrier(grid: list[list[int]]) -> list[list[int]]:
    """Plausible canonical shortcut: only color 8 is impassable.

    Every other pixel is traversable and receives a distance-band color.  The
    shortcut fits all public pairs because they use 8 as their sole wall color.
    """
    if not grid or not grid[0]:
        raise ValueError("expected nonempty grid")
    h, w = len(grid), len(grid[0])
    dist: dict[tuple[int, int], int] = {}
    queue: deque[tuple[int, int]] = deque()
    for r, row in enumerate(grid):
        if len(row) != w:
            raise ValueError("ragged grid")
        for c, value in enumerate(row):
            if value == 2:
                dist[(r, c)] = 0
                queue.append((r, c))
    while queue:
        r, c = queue.popleft()
        for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nr, nc = r + dr, c + dc
            if (0 <= nr < h and 0 <= nc < w
                    and (nr, nc) not in dist
                    and grid[nr][nc] != 8):
                dist[(nr, nc)] = dist[(r, c)] + 1
                queue.append((nr, nc))
    out = deepcopy(grid)
    colors = (3, 4, 5)
    for (r, c), distance in dist.items():
        out[r][c] = colors[distance % 3]
    return out


def observed(grid: list[list[int]]) -> dict[str, int | str]:
    wall_colors = sorted({value for row in grid for value in row if value not in (0, 2)})
    if len(wall_colors) != 1:
        raise ValueError(f"expected one wall color, found {wall_colors}")
    return {
        "shape": f"{len(grid)}x{len(grid[0])}",
        "n_seeds": sum(value == 2 for row in grid for value in row),
        "wall_color": wall_colors[0],
    }


def component_signature(grid: list[list[int]]) -> tuple[int, tuple[int, ...], tuple[int, ...]]:
    components = open_components(grid)
    sizes = tuple(sorted((len(component) for component in components), reverse=True))
    seeded = tuple(sorted((sum(grid[r][c] == 2 for r, c in component) for component in components), reverse=True))
    wall_cells = sum(value not in (0, 2) for row in grid for value in row)
    return wall_cells, sizes, seeded


def canonical_rule_source() -> str:
    ledger = ROOT / "shared/data/canonical/puzzles.jsonl"
    if not ledger.exists():
        ledger = ROOT / "data/canonical/puzzles.jsonl"
    with ledger.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row["program_solution"]
    raise KeyError(TASK_ID)


def selected_authority_path() -> Path:
    # Portable task-test runtimes may mirror the same authority tree under
    # both shared/data and data.  Prefer the canonical shared/data location
    # and use data only as a fallback instead of double-counting the mirror.
    roots = [ROOT / "shared/data/base/solutions", ROOT / "data/base/solutions"]
    searched: list[Path] = []
    for base in roots:
        if not base.is_dir():
            continue
        matches = list(base.glob(f"**/*__{TASK_ID}.json"))
        searched.extend(matches)
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise FileNotFoundError(
                f"expected one selected authority JSON under {base}, found {matches}"
            )
    raise FileNotFoundError(f"selected authority JSON not found; searched {searched}")


def selected_target_code() -> str:
    data = json.loads(selected_authority_path().read_text(encoding="utf-8"))
    return data["racket_target"]["target_code"]


def racket_outputs(grids: Iterable[list[list[int]]]) -> list[list[list[int]]]:
    """Execute the canonical Racket authority in an isolated prepared runtime."""
    grids = list(grids)
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile
    src = ROOT / "src"
    if src.is_dir():
        sys.path.insert(0, str(src))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK_ID)
        request = {"program": canonical_rule_source(), "grids": grids}
        (stage / "parity-request.json").write_text(json.dumps(request))
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
request=json.loads(Path('parity-request.json').read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(request['program']))
try:
    outputs=[runner._apply_rule(bridge,name,g) for g in request['grids']]
    print(json.dumps(outputs))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(module, count: int = 128) -> dict:
    report: dict = {
        "schema": "9199b47fab1e-independent-audit-v1",
        "task_id": TASK_ID,
        "version": getattr(module, "VERSION", None),
        "generator_sha256": hashlib.sha256(
            Path(module.__file__).read_bytes()
        ).hexdigest(),
        "bands": {},
    }
    for band in (None, "easy", "medium", "hard"):
        shapes: set[str] = set()
        colors: set[int] = set()
        seeds: set[int] = set()
        signatures: set[tuple] = set()
        hashes: set[str] = set()
        errors = nondeterministic = rival_survivors = color8_survivors = 0
        for index in range(count):
            grid = module.generate(1009 + index, index * 7 + 3, difficulty=band)
            errors += bool(module.self_check(grid))
            nondeterministic += grid != module.generate(
                1009 + index, index * 7 + 3, difficulty=band
            )
            stats = observed(grid)
            shapes.add(str(stats["shape"]))
            seeds.add(int(stats["n_seeds"]))
            colors.add(int(stats["wall_color"]))
            signatures.add(component_signature(grid))
            hashes.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            intended = rule_output(grid)
            rival_survivors += nearest_seed_manhattan_ignoring_walls(grid) == intended
            color8_survivors += color_8_only_barrier(grid) == intended
        report["bands"][str(band)] = {
            "draws": count,
            "self_check_errors": errors,
            "nondeterministic": nondeterministic,
            "wall_ignoring_rival_survivors": rival_survivors,
            "color_8_only_rival_survivors": color8_survivors,
            "distinct_inputs": len(hashes),
            "shapes": sorted(shapes),
            "n_seeds": sorted(seeds),
            "wall_colors": sorted(colors),
            "component_signatures": len(signatures),
        }
    canonical = canonical_pairs()
    report["canonical"] = {
        "pairs": len(canonical),
        "oracle_matches": sum(
            rule_output(pair["input"]) == pair["output"]
            for pair in canonical
        ),
        "color_8_only_shortcut_matches": sum(
            color_8_only_barrier(pair["input"]) == pair["output"]
            for pair in canonical
        ),
        "declared_shortcuts": {
            name: sum(solver(pair["input"]) == pair["output"] for pair in canonical)
            for name, solver in getattr(module, "CANONICAL_SHORTCUTS", {}).items()
        },
        "self_check_errors": [module.self_check(pair["input"]) for pair in canonical],
    }

    lesson_count = min(count, 100)
    report["lessons"] = {}
    for band in (None, "easy", "medium", "hard"):
        ordered_ambiguities: Counter[str] = Counter()
        rotation_ambiguities: Counter[str] = Counter()
        for start in range(lesson_count):
            pairs = []
            for offset in range(int(getattr(module, "EXAMPLES_NEEDED", 3)) + 1):
                grid = module.generate(70001 + start, start + offset, difficulty=band)
                pairs.append({"input": grid, "output": rule_output(grid)})
            demos = pairs[:-1]
            query = pairs[-1]
            for name, rival in getattr(module, "LESSON_COMPETITORS", {}).items():
                if all(rival(pair["input"]) == pair["output"] for pair in demos):
                    if rival(query["input"]) != query["output"]:
                        ordered_ambiguities[name] += 1
                for query_index, held_out in enumerate(pairs):
                    rotated = [pair for index, pair in enumerate(pairs) if index != query_index]
                    if all(rival(pair["input"]) == pair["output"] for pair in rotated):
                        if rival(held_out["input"]) != held_out["output"]:
                            rotation_ambiguities[name] += 1
        report["lessons"][str(band)] = {
            "windows": lesson_count,
            "rotations": lesson_count * (int(getattr(module, "EXAMPLES_NEEDED", 3)) + 1),
            "ordered_ambiguities": dict(ordered_ambiguities),
            "rotation_ambiguities": dict(rotation_ambiguities),
        }
    report["authority"] = {
        "canonical_equals_selected_target": canonical_rule_source() == selected_target_code(),
    }
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=128)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    module = load_generator(args.generator)
    report = audit(module, args.count)
    if args.racket:
        grids = [pair["input"] for pair in canonical_pairs()]
        grids += [module.generate(431, index, difficulty=("easy", "medium", "hard")[index % 3]) for index in range(24)]
        report["racket"] = {
            "grids": len(grids),
            "matches_python_oracle": racket_outputs(grids) == [rule_output(grid) for grid in grids],
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
