"""Independent oracle and source-bound curriculum probe for 72a261e69372.

The Python oracle deliberately does not import geometry helpers from the
production generator.  It is supplementary evidence: ``--racket`` also runs
all checked grids through the selected canonical Racket rule and fails loudly
when that runtime is unavailable or disagrees.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
TASK = "72a261e69372"
sys.path.insert(0, str(ROOT / "shared/runtime"))

PALETTE_SETS = {
    "low": frozenset({2, 3, 4}),
    "high": frozenset({7, 8, 9}),
    "mixed": frozenset({2, 6, 9}),
}


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_row() -> dict:
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise FileNotFoundError(f"canonical task {TASK} not found")


def _grid(value) -> list[list[int]]:
    if isinstance(value, list) and value and all(isinstance(row, str) for row in value):
        return [[int(cell) for cell in row] for row in value]
    return [list(row) for row in value]


def canonical_pairs() -> list[dict[str, list[list[int]]]]:
    row = canonical_row()
    raw = list(row.get("train") or [])
    test = row.get("test")
    raw.extend(test if isinstance(test, list) else [test])
    return [{"input": _grid(pair["input"]), "output": _grid(pair["output"])} for pair in raw]


def components(grid: list[list[int]], color: int) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] == color}
    found: list[set[tuple[int, int]]] = []
    while unseen:
        start = min(unseen)
        stack = [start]
        unseen.remove(start)
        comp = {start}
        while stack:
            r, c = stack.pop()
            for p in ((r - 1, c), (r + 1, c), (r, c - 1), (r, c + 1)):
                if p in unseen:
                    unseen.remove(p)
                    comp.add(p)
                    stack.append(p)
        found.append(comp)
    return found


def bbox(cells: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = tuple(cells)
    return (
        min(r for r, _ in cells),
        min(c for _, c in cells),
        max(r for r, _ in cells),
        max(c for _, c in cells),
    )


def outline(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r1, c1, r2, c2 = box
    return (
        {(r1, c) for c in range(c1, c2 + 1)}
        | {(r2, c) for c in range(c1, c2 + 1)}
        | {(r, c1) for r in range(r1, r2 + 1)}
        | {(r, c2) for r in range(r1, r2 + 1)}
    )


def exact_frames(grid: list[list[int]]) -> list[tuple[int, tuple[int, int, int, int]]]:
    colors = sorted({v for row in grid for v in row if v not in (0, 1)})
    frames = []
    for color in colors:
        for comp in components(grid, color):
            box = bbox(comp)
            if box[2] - box[0] >= 2 and box[3] - box[1] >= 2 and comp == outline(box):
                frames.append((color, box))
    return frames


def color_boxes(grid: list[list[int]]) -> list[tuple[int, tuple[int, int, int, int]]]:
    colors = sorted({v for row in grid for v in row if v not in (0, 1)})
    result = []
    for color in colors:
        cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == color}
        result.append((color, bbox(cells)))
    return result


def _inside(box: tuple[int, int, int, int], point: tuple[int, int]) -> bool:
    r1, c1, r2, c2 = box
    r, c = point
    return r1 < r < r2 and c1 < c < c2


def reference_output(
    grid: list[list[int]], *, use_bboxes: bool = False, outermost: bool = False
) -> list[list[int]]:
    """Independent implementation of the selected rule and two named rivals."""
    out = deepcopy(grid)
    candidates = color_boxes(grid) if use_bboxes else exact_frames(grid)
    for r, row in enumerate(grid):
        for c, value in enumerate(row):
            if value != 1:
                continue
            enclosing = [(color, box) for color, box in candidates if _inside(box, (r, c))]
            if not enclosing:
                continue
            enclosing.sort(
                key=lambda item: (item[1][2] - item[1][0] + 1) * (item[1][3] - item[1][1] + 1),
                reverse=outermost,
            )
            out[r][c] = enclosing[0][0]
    return out


def marker_enclosures(grid: list[list[int]]) -> dict[tuple[int, int], list[int]]:
    frames = exact_frames(grid)
    return {
        (r, c): [color for color, box in frames if _inside(box, (r, c))]
        for r, row in enumerate(grid)
        for c, value in enumerate(row)
        if value == 1
    }


def has_occluded_orphan(grid: list[list[int]]) -> bool:
    exact = exact_frames(grid)
    exact_colors = {color for color, _ in exact}
    boxes = dict(color_boxes(grid))
    for point, enclosing in marker_enclosures(grid).items():
        if enclosing:
            continue
        if any(color not in exact_colors and _inside(box, point) for color, box in boxes.items()):
            return True
    return False


def has_nested_choice(grid: list[list[int]]) -> bool:
    return any(len(colors) >= 2 for colors in marker_enclosures(grid).values())


def palette_kind(grid: list[list[int]]) -> str:
    colors = frozenset(v for row in grid for v in row if v not in (0, 1))
    if colors <= PALETTE_SETS["low"]:
        return "low"
    if colors <= PALETTE_SETS["high"]:
        return "high"
    if colors <= PALETTE_SETS["mixed"] and colors & {2, 6} and colors & {6, 9}:
        return "mixed"
    # n_frames=2 mixed palettes can be any two members of {2,6,9}; every pair
    # crosses the low/high partition and is therefore still unambiguous.
    if colors <= PALETTE_SETS["mixed"] and len(colors) == 2:
        return "mixed"
    raise ValueError(f"unrecognized palette family: {sorted(colors)}")


def observed(grid: list[list[int]]) -> dict[str, object]:
    colors = {v for row in grid for v in row if v not in (0, 1)}
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "n_frames": len(colors),
        "layout_kind": "overlap" if has_occluded_orphan(grid) else "nested",
        "palette_kind": palette_kind(grid),
    }


def profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({v for row in grid for v in row})


def pinned_seed(band: str, index: int) -> int:
    digest = hashlib.sha256(f"profile-floor:v1:{TASK}:{band}:{index}".encode()).hexdigest()
    return int(digest[:12], 16)


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": canonical_row()["program_solution"], "grids": grids})
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
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(module, per_band: int) -> tuple[dict, list[list[list[int]]]]:
    canonical = canonical_pairs()
    canonical_errors = [module.self_check(pair["input"]) for pair in canonical]
    if any(reference_output(pair["input"]) != pair["output"] for pair in canonical):
        raise AssertionError("independent oracle does not reproduce canonical outputs")

    racket_grids = [pair["input"] for pair in canonical]
    by_band = {}
    pooled = Counter()
    distinct_inputs = set()
    n_demos = int(getattr(module, "EXAMPLES_NEEDED", 4))

    for band in ("easy", "medium", "hard"):
        counts = Counter()
        profiles = Counter()
        axis_values = defaultdict(set)
        grids = []
        for index in range(per_band):
            seed = pinned_seed(band, index)
            sample_index = seed % 7919 + index
            grid = module.generate(seed, sample_index, difficulty=band)
            grids.append(grid)
            if index < 32:
                racket_grids.append(grid)
            issues = module.self_check(grid)
            counts["draws"] += 1
            counts["self_check_errors"] += bool(issues)
            counts["nondeterministic"] += grid != module.generate(seed, sample_index, difficulty=band)
            counts["changed"] += reference_output(grid) != grid
            counts["occluded_orphan"] += has_occluded_orphan(grid)
            counts["nested_choice"] += has_nested_choice(grid)
            counts["bbox_rival_disagreements"] += reference_output(grid) != reference_output(grid, use_bboxes=True)
            counts["outermost_rival_disagreements"] += reference_output(grid) != reference_output(grid, outermost=True)
            profiles[profile(grid)] += 1
            obs = observed(grid)
            for key, value in obs.items():
                axis_values[key].add(value)
            distinct_inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())

        # Mirror the semantic gate's actual lesson schedule: pinned lesson seed,
        # start sample_index k*11, then consecutive demos and one query.
        lessons = Counter(
            total=0,
            identifiable=0,
            hook_errors=0,
            bbox_survives=0,
            outermost_survives=0,
            missing_layout_coverage=0,
        )
        lesson_input_hashes = set()
        for lesson_index in range(per_band):
            seed = pinned_seed(f"lesson:{band}", lesson_index)
            start = lesson_index * 11
            demos = []
            for offset in range(n_demos):
                demo_grid = module.generate(seed, start + offset, difficulty=band)
                demos.append({"input": demo_grid, "output": reference_output(demo_grid)})
                lesson_input_hashes.add(
                    hashlib.sha256(json.dumps(demo_grid, separators=(",", ":")).encode()).hexdigest()
                )
            query_grid = module.generate(seed, start + n_demos, difficulty=band)
            query = {"input": query_grid, "output": reference_output(query_grid)}
            lessons["total"] += 1
            try:
                reasons = module.lesson_identifiable(demos, query)
            except Exception:
                lessons["hook_errors"] += 1
                reasons = ["hook raised"]
            if not reasons:
                lessons["identifiable"] += 1
            layouts = {observed(pair["input"])["layout_kind"] for pair in demos}
            lessons["missing_layout_coverage"] += layouts != {"nested", "overlap"}
            lessons["bbox_survives"] += all(
                reference_output(pair["input"], use_bboxes=True) == pair["output"]
                for pair in demos
            )
            lessons["outermost_survives"] += all(
                reference_output(pair["input"], outermost=True) == pair["output"]
                for pair in demos
            )
        lessons["unique_demo_inputs"] = len(lesson_input_hashes)

        exact_profiles = {profile(pair["input"]) for pair in canonical}
        counts["canonical_profile_hits"] = sum(count for p, count in profiles.items() if p in exact_profiles)
        pooled.update(counts)
        by_band[band] = {
            "counts": dict(counts),
            "profiles": {str(key): value for key, value in sorted(profiles.items())},
            "axis_values": {key: sorted(values, key=repr) for key, values in sorted(axis_values.items())},
            "actual_lessons": dict(lessons),
        }

    report = {
        "schema": f"{TASK}-independent-audit-v1",
        "version": module.VERSION,
        "rule_hash": getattr(module, "RULE_HASH", None),
        "canonical_pairs": len(canonical),
        "canonical_self_check_errors": canonical_errors,
        "counts": dict(pooled),
        "distinct_inputs": len(distinct_inputs),
        "by_band": by_band,
        "sampling_design": (
            "Census uses pinned profile-floor seeds with sample_index=seed%7919+index. "
            f"Lessons mirror the gate/trainer schedule: {per_band} pinned lesson seeds per band, "
            f"start sample_index=k*11, {n_demos} consecutive demos and one query."
        ),
        "limitations": (
            "The Python oracle is independently implemented but supplementary. --racket is required for "
            "selected-rule execution evidence; this census does not claim universal induction."
        ),
    }
    return report, racket_grids


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--per-band", type=int, default=200)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.per_band < 1:
        parser.error("--per-band must be positive")

    module = load_generator(args.generator)
    report, grids = audit(module, args.per_band)
    source = (args.generator or ROOT / f"generators/{TASK}/generator.py").resolve()
    report["generator_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["racket"] = {"status": "not_requested", "checked": 0}
    exit_code = int(bool(any(report["canonical_self_check_errors"]) or report["counts"]["self_check_errors"] or report["counts"]["nondeterministic"]))
    if args.racket:
        try:
            # Canonical pairs plus 32 generated grids from each difficulty band.
            selected = grids
            actual = racket_outputs(selected)
            expected = [reference_output(grid) for grid in selected]
            mismatches = [i for i, (a, e) in enumerate(zip(actual, expected)) if a != e]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(selected),
                "mismatches": mismatches,
            }
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:
            report["racket"] = {
                "status": "unavailable_or_failed",
                "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2

    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"version": report["version"], "counts": report["counts"], "racket": report["racket"]}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
