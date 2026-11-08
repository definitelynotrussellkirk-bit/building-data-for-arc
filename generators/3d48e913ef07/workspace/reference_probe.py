"""Independent oracle and audit tooling for task 3d48e913ef07.

This module intentionally reconstructs the written/Racket rule from returned
pixels.  It never imports generator-private helpers.  The Python oracle is
supplementary evidence; ``racket_outputs`` executes the canonical authority.
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
import tempfile

TASK = "3d48e913ef07"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared/runtime"))
sys.path.insert(0, str(ROOT / "src"))


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator_3d48e913ef07", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical():
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs():
    row = canonical()
    tests = row.get("test", [])
    if isinstance(tests, dict):
        tests = [tests]
    return list(row.get("train", [])) + list(tests)


def palette(grid):
    """Return (row, color) markers in the first column, top to bottom."""
    return [(r, row[0]) for r, row in enumerate(grid) if row[0] not in (0, 3)]


def components(grid, color=3):
    """Return 4-connected monochrome components as sorted coordinate tuples."""
    h, w = len(grid), len(grid[0])
    seen = set()
    result = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != color or (r, c) in seen:
                continue
            queue = deque([(r, c)])
            seen.add((r, c))
            cells = []
            while queue:
                rr, cc = queue.popleft()
                cells.append((rr, cc))
                for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                    nr, nc = rr + dr, cc + dc
                    if 0 <= nr < h and 0 <= nc < w and grid[nr][nc] == color and (nr, nc) not in seen:
                        seen.add((nr, nc))
                        queue.append((nr, nc))
            result.append(tuple(sorted(cells)))
    return result


def bbox(cells):
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def _crop(cells, color):
    r0, c0, r1, c1 = bbox(cells)
    out = [[0] * (c1 - c0 + 1) for _ in range(r1 - r0 + 1)]
    for r, c in cells:
        out[r - r0][c - c0] = color
    return out


def ordered_components(grid, mode="area"):
    comps = components(grid, 3)
    if mode == "area":
        return sorted(comps, key=lambda cells: (-len(cells), bbox(cells)[0], bbox(cells)[1]))
    if mode == "ascending_area":
        return sorted(comps, key=lambda cells: (len(cells), bbox(cells)[0], bbox(cells)[1]))
    if mode == "source":
        return sorted(comps, key=lambda cells: (bbox(cells)[0], bbox(cells)[1]))
    if mode == "bbox_area":
        return sorted(
            comps,
            key=lambda cells: (
                -((bbox(cells)[2] - bbox(cells)[0] + 1) * (bbox(cells)[3] - bbox(cells)[1] + 1)),
                bbox(cells)[0],
                bbox(cells)[1],
            ),
        )
    if mode == "bbox_width":
        return sorted(
            comps,
            key=lambda cells: (
                -(bbox(cells)[3] - bbox(cells)[1] + 1),
                bbox(cells)[0],
                bbox(cells)[1],
            ),
        )
    raise ValueError(f"unknown object order {mode!r}")


def packed_output(grid, *, object_order="area", palette_order="row"):
    markers = palette(grid)
    colors = [color for _, color in markers]
    if palette_order == "numeric":
        colors = sorted(colors)
    elif palette_order != "row":
        raise ValueError(f"unknown palette order {palette_order!r}")
    comps = ordered_components(grid, object_order)
    pieces = [_crop(cells, color) for cells, color in zip(comps, colors)]
    if not pieces:
        return [[0]]
    width = max(len(piece[0]) for piece in pieces)
    height = sum(len(piece) for piece in pieces) + len(pieces) - 1
    out = [[0] * width for _ in range(height)]
    top = 0
    for piece in pieces:
        for r, row in enumerate(piece):
            out[top + r][: len(row)] = row
        top += len(piece) + 1
    return out


def observed(grid):
    return {"grid_h": len(grid), "grid_w": len(grid[0]), "n_objs": len(components(grid, 3))}


def object_signature(grid):
    comps = components(grid, 3)
    return tuple(
        sorted(
            (
                len(cells),
                bbox(cells)[2] - bbox(cells)[0] + 1,
                bbox(cells)[3] - bbox(cells)[1] + 1,
            )
            for cells in comps
        )
    )


def shortcut_witness():
    """A lawful case separating area, reading-order, bbox-area, and palette-order rules."""
    grid = [[0] * 14 for _ in range(10)]
    for r, color in ((0, 7), (4, 2), (8, 9)):
        grid[r][0] = color
    # Earliest object: area 3, 2x2 bbox.
    for r, c in ((1, 3), (2, 3), (2, 4)):
        grid[r][c] = 3
    # Second object: area 5, sparse 3x3 bbox.  It precedes the equally-wide
    # area-6 object, refuting both bbox-area and bbox-width shortcuts.
    for r, c in ((3, 9), (4, 8), (4, 9), (4, 10), (5, 9)):
        grid[r][c] = 3
    # Last object: area 6, compact 2x3 bbox.
    for r in (7, 8):
        for c in (3, 4, 5):
            grid[r][c] = 3
    return grid


def racket_outputs(grids):
    """Execute the real canonical Racket rule against a batch of grids."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    program = canonical()["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(json.dumps({"program": program, "grids": grids}))
        script = r'''\
import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path("parity-request.json").read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    outputs = [runner._apply_rule(bridge, name, grid) for grid in request["grids"]]
    print(json.dumps(outputs))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=240)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs



def _declared_lesson_competitors(module):
    """Return the generator's actual lesson rivals, with shortcuts auto-included."""
    competitors = {}
    for attribute in ("LESSON_COMPETITORS", "CANONICAL_SHORTCUTS"):
        declared = getattr(module, attribute, {})
        if declared is None:
            continue
        if not isinstance(declared, dict):
            raise TypeError(f"{attribute} must be a dict, got {type(declared).__name__}")
        for name, rival in declared.items():
            if not isinstance(name, str) or not callable(rival):
                raise TypeError(f"{attribute}[{name!r}] must be a named callable")
            competitors[name] = rival
    return competitors


def cyclic_lesson_audit(module, cycles_per_band=20):
    """Audit every cyclic query start in the declared schedule.

    The shared lesson census samples production lessons but does not rotate every
    member of a small deterministic schedule into the query position.  This
    task-local companion uses the generator's *actual* declarations rather than
    a copied rival-name list, checks every schedule residue as a query, and
    verifies any declared canonical shortcut against every public pair.
    """
    if isinstance(cycles_per_band, bool) or not isinstance(cycles_per_band, int) or cycles_per_band < 1:
        raise ValueError("cycles_per_band must be a positive integer")
    profiles = tuple(getattr(module, "SCHEDULE_PROFILES", ()))
    if len(profiles) < 4:
        raise ValueError("SCHEDULE_PROFILES must enumerate at least four residues")
    n_demos = getattr(module, "EXAMPLES_NEEDED", 3)
    if isinstance(n_demos, bool) or not isinstance(n_demos, int) or not 2 <= n_demos < len(profiles):
        raise ValueError("EXAMPLES_NEEDED must leave at least one cyclic query residue")

    competitors = _declared_lesson_competitors(module)
    shortcut_names = sorted(getattr(module, "CANONICAL_SHORTCUTS", {}) or {})
    canonical_fit = {}
    for name in shortcut_names:
        rival = competitors[name]
        canonical_fit[name] = all(
            rival(deepcopy(pair["input"])) == pair["output"]
            for pair in canonical_pairs()
        )

    hook = getattr(module, "lesson_identifiable", None)
    if not callable(hook):
        raise TypeError("generator must expose callable lesson_identifiable")

    report = {
        "schema": f"{TASK}-cyclic-lesson-audit-v1",
        "profiles": list(profiles),
        "examples_needed": n_demos,
        "cycles_per_band": cycles_per_band,
        "competitors": sorted(competitors),
        "canonical_shortcuts": shortcut_names,
        "canonical_shortcut_fits_all_pairs": canonical_fit,
        "lessons": 0,
        "unique_inputs": 0,
        "hook_failures": [],
        "surviving_rival_failures": [],
        "per_band": {},
    }
    unique_inputs = set()
    bands = (None, "easy", "medium", "hard")
    for band_index, band in enumerate(bands):
        band_key = str(band)
        band_stats = Counter()
        for cycle in range(cycles_per_band):
            seed = 8100 + band_index * 100_000 + cycle
            base_index = cycle * len(profiles)
            grids = [
                module.generate(seed, base_index + residue, difficulty=band)
                for residue in range(len(profiles))
            ]
            pairs = [{"input": grid, "output": packed_output(grid)} for grid in grids]
            for grid in grids:
                unique_inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            for start in range(len(profiles)):
                demos = [pairs[(start + offset) % len(profiles)] for offset in range(n_demos)]
                query = pairs[(start + n_demos) % len(profiles)]
                lesson_label = {
                    "band": band,
                    "cycle": cycle,
                    "seed": seed,
                    "start_residue": start,
                    "demo_residues": [(start + offset) % len(profiles) for offset in range(n_demos)],
                    "query_residue": (start + n_demos) % len(profiles),
                }
                report["lessons"] += 1
                band_stats["lessons"] += 1
                reasons = hook(deepcopy(demos), deepcopy(query))
                if reasons:
                    report["hook_failures"].append({**lesson_label, "reasons": reasons})
                    band_stats["hook_failures"] += 1
                for name, rival in competitors.items():
                    survives = all(
                        rival(deepcopy(pair["input"])) == pair["output"]
                        for pair in demos
                    )
                    disagrees_on_query = rival(deepcopy(query["input"])) != query["output"]
                    if survives:
                        band_stats[f"{name}:survives_demos"] += 1
                    if survives and disagrees_on_query:
                        report["surviving_rival_failures"].append({**lesson_label, "rival": name})
                        band_stats[f"{name}:lesson_failures"] += 1
        report["per_band"][band_key] = dict(band_stats)
    report["unique_inputs"] = len(unique_inputs)
    return report

def audit(module, count=250, *, run_racket=False):
    report = {
        "schema": f"{TASK}-independent-audit-v1",
        "task_id": TASK,
        "version": getattr(module, "VERSION", None),
        "generator_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        "canonical": {},
        "bands": {},
    }
    pairs = canonical_pairs()
    report["canonical"] = {
        "pairs": len(pairs),
        "oracle_mismatches": [i for i, pair in enumerate(pairs) if packed_output(pair["input"]) != pair["output"]],
        "self_check_errors": [module.self_check(pair["input"]) for pair in pairs],
    }
    retained = [pair["input"] for pair in pairs] + [shortcut_witness()]
    for band in (None, "easy", "medium", "hard"):
        counts = Counter()
        inputs = set()
        dimensions = set()
        object_signatures = set()
        for i in range(count):
            grid = module.generate(3100 + i, i * 17 + 5, difficulty=band)
            again = module.generate(3100 + i, i * 17 + 5, difficulty=band)
            counts["samples"] += 1
            counts["nondeterministic"] += grid != again
            counts["self_check_errors"] += bool(module.self_check(grid))
            for rival_name, rival in sorted(getattr(module, "SEMANTIC_RIVALS", {}).items()):
                counts[f"{rival_name}_counterexamples"] += packed_output(grid) != rival(deepcopy(grid))
            inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            dimensions.add((len(grid), len(grid[0])))
            object_signatures.add(object_signature(grid))
            if i < 12:
                retained.append(grid)
        counts["distinct_inputs"] = len(inputs)
        counts["distinct_dimensions"] = len(dimensions)
        counts["distinct_object_signatures"] = len(object_signatures)
        report["bands"][str(band)] = dict(counts)
    report["lessons"] = cyclic_lesson_audit(module, cycles_per_band=20)
    report["racket"] = {"status": "not_requested", "checked": 0}
    if run_racket:
        outputs = racket_outputs(retained)
        mismatches = [i for i, (grid, output) in enumerate(zip(retained, outputs)) if packed_output(grid) != output]
        report["racket"] = {
            "status": "passed" if not mismatches else "failed",
            "checked": len(outputs),
            "mismatches": mismatches,
        }
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=250)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    parser.add_argument("--cycles-per-band", type=int, default=20)
    args = parser.parse_args()
    module = load_generator(args.generator or os.environ.get("GENERATOR_UNDER_TEST"))
    report = audit(module, args.count, run_racket=args.racket)
    if args.cycles_per_band != 20:
        report["lessons"] = cyclic_lesson_audit(module, cycles_per_band=args.cycles_per_band)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"version": report["version"], "canonical": report["canonical"], "bands": report["bands"], "lessons": report["lessons"], "racket": report["racket"]}, indent=2))
    failed = bool(report["canonical"]["oracle_mismatches"] or any(report["canonical"]["self_check_errors"]))
    failed |= any(values["nondeterministic"] or values["self_check_errors"] for values in report["bands"].values())
    failed |= bool(report["lessons"]["hook_failures"] or report["lessons"]["surviving_rival_failures"])
    failed |= any(not fits for fits in report["lessons"]["canonical_shortcut_fits_all_pairs"].values())
    failed |= report["racket"]["status"] == "failed"
    return int(failed)


if __name__ == "__main__":
    raise SystemExit(main())
