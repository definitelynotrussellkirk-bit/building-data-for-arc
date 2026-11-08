"""Independent probes for ARC task fe0dc9f32b7b (Nested Palette Fill).

This module intentionally does not import implementation helpers from
``generator.py``.  It reconstructs the selected public rule from pixels:
column-0 palette colors are read top-to-bottom; color-8 objects qualify as
frames when their component size equals their bounding-box perimeter; each
zero cell is recolored by the number of qualifying boxes strictly containing
it.  The optional rivals make the task's decisive distinctions executable.
"""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import importlib.util
import json
import os
from pathlib import Path
import sys
from typing import Iterable

TASK_ID = "fe0dc9f32b7b"
GENERATOR_HOME = Path(__file__).resolve().parents[1]
REPO_ROOT = GENERATOR_HOME.parents[1]
for _path in (REPO_ROOT / "shared/runtime", REPO_ROOT / "src", REPO_ROOT):
    _text = str(_path)
    if _text not in sys.path:
        sys.path.insert(0, _text)


def normalize_grid(grid):
    if grid and isinstance(grid[0], str):
        return [[int(value) for value in row] for row in grid]
    return [list(row) for row in grid]


def canonical_row():
    path = REPO_ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                return row
    raise AssertionError(f"canonical task {TASK_ID} not found")


def canonical_pairs():
    row = canonical_row()
    pairs = list(row.get("train") or [])
    test = row.get("test")
    if isinstance(test, list):
        pairs.extend(test)
    elif isinstance(test, dict):
        pairs.append(test)
    return [
        {"input": normalize_grid(pair["input"]),
         "output": normalize_grid(pair["output"])}
        for pair in pairs
    ]


def load_generator(path: str | os.PathLike[str] | None = None):
    selected = path or os.environ.get("GENERATOR_UNDER_TEST")
    selected_path = Path(selected) if selected else GENERATOR_HOME / "generator.py"
    spec = importlib.util.spec_from_file_location(
        f"generator_under_test_{TASK_ID}", selected_path
    )
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {selected_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def palette(grid) -> list[int]:
    return [row[0] for row in grid if row[0] not in (0, 8)]


def color8_components(grid) -> list[set[tuple[int, int]]]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    components: list[set[tuple[int, int]]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] != 8 or (r, c) in seen:
                continue
            todo = [(r, c)]
            seen.add((r, c))
            component: set[tuple[int, int]] = set()
            while todo:
                rr, cc = todo.pop()
                component.add((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            grid[nr][nc] == 8 and (nr, nc) not in seen):
                        seen.add((nr, nc))
                        todo.append((nr, nc))
            components.append(component)
    return components


def bbox(component: Iterable[tuple[int, int]]) -> tuple[int, int, int, int]:
    cells = list(component)
    rows = [r for r, _ in cells]
    cols = [c for _, c in cells]
    return min(rows), min(cols), max(rows), max(cols)


def perimeter_cells(box: tuple[int, int, int, int]) -> set[tuple[int, int]]:
    r0, c0, r1, c1 = box
    return {
        (r, c)
        for r in range(r0, r1 + 1)
        for c in range(c0, c1 + 1)
        if r in (r0, r1) or c in (c0, c1)
    }


def authority_frame(component: set[tuple[int, int]]) -> bool:
    r0, c0, r1, c1 = bbox(component)
    height, width = r1 - r0 + 1, c1 - c0 + 1
    return (
        height >= 3
        and width >= 3
        and len(component) == 2 * (height + width) - 4
    )


def clean_frame(component: set[tuple[int, int]]) -> bool:
    return authority_frame(component) and component == perimeter_cells(bbox(component))


def qualifying_boxes(grid) -> list[tuple[int, int, int, int]]:
    return sorted(bbox(component) for component in color8_components(grid)
                  if authority_frame(component))


def nested_palette_output(
    grid,
    *,
    outermost_only: bool = False,
    include_malformed_bboxes: bool = False,
    clamp_palette: bool = False,
    exact_perimeter_only: bool = False,
):
    """Independent selected rule, with explicit wrong-rule switches."""
    source = normalize_grid(grid)
    colors = palette(source)
    components = color8_components(source)
    if include_malformed_bboxes:
        boxes = [
            bbox(component)
            for component in components
            if (bbox(component)[2] - bbox(component)[0] + 1 >= 3 and
                bbox(component)[3] - bbox(component)[1] + 1 >= 3)
        ]
    elif exact_perimeter_only:
        boxes = [bbox(component) for component in components
                 if clean_frame(component)]
    else:
        boxes = [bbox(component) for component in components
                 if authority_frame(component)]
    boxes.sort()
    if outermost_only and boxes:
        boxes = [max(boxes, key=lambda box: (box[2] - box[0] + 1) *
                                            (box[3] - box[1] + 1))]

    output = copy.deepcopy(source)
    for r, row in enumerate(source):
        for c, value in enumerate(row):
            if value != 0:
                continue
            depth = sum(r0 < r < r1 and c0 < c < c1
                        for r0, c0, r1, c1 in boxes)
            if depth <= 0 or not colors:
                continue
            if depth <= len(colors):
                output[r][c] = colors[depth - 1]
            elif clamp_palette:
                output[r][c] = colors[-1]
    return output


def scene_kind(grid) -> str:
    components = color8_components(grid)
    qualified = [component for component in components if authority_frame(component)]
    malformed = [component for component in components if not authority_frame(component)]
    if len(qualified) == 2 and not malformed:
        nonclean = [component for component in qualified if not clean_frame(component)]
        if not nonclean:
            return "two_clean"
        if len(nonclean) == 1:
            return "warped_inner"
    if len(qualified) == 3 and not malformed and all(
        clean_frame(component) for component in qualified
    ):
        return "three_clean"
    if len(qualified) == 1 and len(malformed) == 1:
        return "malformed_inner"
    return "other"


def observed(grid) -> dict[str, int | str]:
    source = normalize_grid(grid)
    return {
        "grid_h": len(source),
        "grid_w": len(source[0]),
        "palette_size": len(palette(source)),
        "scene_kind": scene_kind(source),
    }


def output_profile(grid) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def racket_outputs(grids):
    """Execute the selected canonical Racket rule; never fall back to Python."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile

    sys.path.insert(0, str(REPO_ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical_row()["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK_ID}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(REPO_ROOT), stage, TASK_ID)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": program, "grids": grids}), encoding="utf-8"
        )
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
            raise RuntimeError(
                f"Racket worker failed: {result['stderr']} {result['stdout']}"
            )
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(module, count: int = 100) -> tuple[dict, list]:
    counts: dict[str, int] = {
        "samples": 0,
        "self_check_errors": 0,
        "oracle_mismatches": 0,
        "nondeterministic": 0,
        "outermost_counterexamples": 0,
        "malformed_counterexamples": 0,
        "clamp_counterexamples": 0,
        "exact_perimeter_counterexamples": 0,
    }
    by_band: dict[str, dict] = {}
    samples: list = []
    all_inputs: set[str] = set()
    for band in (None, "easy", "medium", "hard"):
        local = {key: 0 for key in counts}
        scenes: dict[str, int] = {}
        profiles: set[tuple[int, int, int]] = set()
        for index in range(count):
            seed = 1709 + index * 37
            grid = module.generate(seed, index * 11 + 3, difficulty=band)
            local["samples"] += 1
            local["self_check_errors"] += bool(module.self_check(grid))
            local["nondeterministic"] += (
                grid != module.generate(seed, index * 11 + 3, difficulty=band)
            )
            local["oracle_mismatches"] += (
                module.rule_mirror(grid) != nested_palette_output(grid)
            )
            intended = nested_palette_output(grid)
            local["outermost_counterexamples"] += (
                intended != nested_palette_output(grid, outermost_only=True)
            )
            local["malformed_counterexamples"] += (
                intended != nested_palette_output(grid, include_malformed_bboxes=True)
            )
            local["clamp_counterexamples"] += (
                intended != nested_palette_output(grid, clamp_palette=True)
            )
            local["exact_perimeter_counterexamples"] += (
                intended != nested_palette_output(grid, exact_perimeter_only=True)
            )
            kind = scene_kind(grid)
            scenes[kind] = scenes.get(kind, 0) + 1
            profiles.add(output_profile(grid))
            digest = hashlib.sha256(
                json.dumps(grid, separators=(",", ":")).encode()
            ).hexdigest()
            all_inputs.add(digest)
            if len(samples) < 32:
                samples.append(grid)
        by_band[str(band)] = {
            **local,
            "scene_counts": scenes,
            "profiles": sorted(profiles),
        }
        for key, value in local.items():
            counts[key] += value

    canonical_errors = [module.self_check(pair["input"]) for pair in canonical_pairs()]
    report = {
        "schema": f"{TASK_ID}-independent-audit-v1",
        "version": module.VERSION,
        "canonical_self_check_errors": canonical_errors,
        "canonical_oracle_matches": sum(
            nested_palette_output(pair["input"]) == pair["output"]
            for pair in canonical_pairs()
        ),
        "counts": counts,
        "by_band": by_band,
        "distinct_inputs": len(all_inputs),
        "warning": "Python oracle is independent supplemental evidence, not Racket authority.",
    }
    grids = [pair["input"] for pair in canonical_pairs()] + samples
    return report, grids


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
    generator_path = args.generator or GENERATOR_HOME / "generator.py"
    report["generator_sha256"] = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["racket"] = {"status": "not_requested", "checked": 0}
    exit_code = int(
        any(report["canonical_self_check_errors"])
        or report["canonical_oracle_matches"] != len(canonical_pairs())
        or report["counts"]["self_check_errors"]
        or report["counts"]["oracle_mismatches"]
        or report["counts"]["nondeterministic"]
    )
    if args.racket:
        try:
            outputs = racket_outputs(grids)
            mismatches = [
                index for index, (grid, output) in enumerate(zip(grids, outputs))
                if nested_palette_output(grid) != output
            ]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(outputs),
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
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "version": report["version"],
        "canonical_oracle_matches": report["canonical_oracle_matches"],
        "counts": report["counts"],
        "racket": report["racket"],
    }, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
