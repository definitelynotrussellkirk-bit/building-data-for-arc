"""Independent oracle and repeatable audit for ARC task 4296e507c770.

Reviewer-owned tooling: geometry is re-derived from input pixels and never calls
production transform helpers.  The canonical Racket program remains the label
authority; ``racket_outputs`` executes it when parity evidence is requested.
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
from typing import Any, Iterable

TASK = "4296e507c770"
ROOT = Path(__file__).resolve().parents[3]
GENERATOR = ROOT / "generators" / TASK / "generator.py"
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def load_generator(path: str | os.PathLike[str] | None = None):
    source = Path(path or os.environ.get("GENERATOR_UNDER_TEST", GENERATOR)).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_4296e507c770", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def canonical() -> dict[str, Any]:
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise LookupError(f"canonical row {TASK} is absent")


def canonical_pairs() -> list[dict[str, Any]]:
    row = canonical()
    test = row["test"] if isinstance(row["test"], list) else [row["test"]]
    return row["train"] + test


def normalize(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = tuple(cells)
    if not points:
        return ()
    top = min(r for r, _ in points)
    left = min(c for _, c in points)
    return tuple(sorted((r - top, c - left) for r, c in points))


def transform(cells: Iterable[tuple[int, int]], marker_color: int) -> tuple[tuple[int, int], ...]:
    points = normalize(cells)
    if not points:
        return ()
    height = max(r for r, _ in points) + 1
    width = max(c for _, c in points) + 1
    out = []
    for r, c in points:
        if marker_color == 4:       # horizontal mirror
            point = (r, width - 1 - c)
        elif marker_color == 5:     # vertical mirror
            point = (height - 1 - r, c)
        elif marker_color == 6:     # clockwise quarter-turn
            point = (c, height - 1 - r)
        else:                       # color 3: identity
            point = (r, c)
        out.append(point)
    return normalize(out)


def transform_ccw(cells: Iterable[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    points = normalize(cells)
    if not points:
        return ()
    width = max(c for _, c in points) + 1
    return normalize((width - 1 - c, r) for r, c in points)


def _components(cells: set[tuple[int, int]]) -> list[set[tuple[int, int]]]:
    remaining = set(cells)
    result: list[set[tuple[int, int]]] = []
    while remaining:
        seed = remaining.pop()
        component = {seed}
        stack = [seed]
        while stack:
            r, c = stack.pop()
            for dr, dc in CARDINAL:
                nxt = (r + dr, c + dc)
                if nxt in remaining:
                    remaining.remove(nxt)
                    component.add(nxt)
                    stack.append(nxt)
        result.append(component)
    return result


def facts(grid: list[list[int]]) -> dict[str, Any]:
    height = len(grid)
    width = len(grid[0])
    template_cells = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 2}
    components = _components(template_cells)
    if len(components) != 1:
        raise ValueError(f"expected one color-2 component, found {len(components)}")
    shape = normalize(components[0])
    markers = [(r, c, value) for r, row in enumerate(grid) for c, value in enumerate(row) if value in (3, 4, 5, 6)]
    return {
        "grid_h": height,
        "grid_w": width,
        "template_size": len(shape),
        "shape": shape,
        "markers": markers,
        "n_markers": len(markers),
        "marker_colors": {value for _, _, value in markers},
    }


def observed(grid: list[list[int]]) -> dict[str, int]:
    info = facts(grid)
    return {name: int(info[name]) for name in ("grid_h", "grid_w", "template_size", "n_markers")}


def transform_signatures(shape: Iterable[tuple[int, int]]) -> dict[str, tuple[tuple[int, int], ...]]:
    return {
        "identity": transform(shape, 3),
        "flip_lr": transform(shape, 4),
        "flip_ud": transform(shape, 5),
        "rotate_cw": transform(shape, 6),
        "rotate_ccw": transform_ccw(shape),
    }


def is_transform_separating(shape: Iterable[tuple[int, int]]) -> bool:
    signatures = transform_signatures(shape)
    return len(set(signatures.values())) == len(signatures)


def geometry_output(
    grid: list[list[int]],
    *,
    mapping: dict[int, str] | None = None,
) -> list[list[int]]:
    info = facts(grid)
    output = [[0 for _ in range(info["grid_w"])] for _ in range(info["grid_h"])]
    shape = info["shape"]
    mapping = mapping or {3: "identity", 4: "flip_lr", 5: "flip_ud", 6: "rotate_cw"}
    signatures = transform_signatures(shape)
    for row, col, color in info["markers"]:
        for dr, dc in signatures[mapping[color]]:
            rr, cc = row + dr, col + dc
            if not (0 <= rr < info["grid_h"] and 0 <= cc < info["grid_w"]):
                raise ValueError("stamp falls outside grid")
            output[rr][cc] = 8
    return output


def identity_everywhere(grid: list[list[int]]) -> list[list[int]]:
    return geometry_output(grid, mapping={3: "identity", 4: "identity", 5: "identity", 6: "identity"})


def swap_mirrors(grid: list[list[int]]) -> list[list[int]]:
    return geometry_output(grid, mapping={3: "identity", 4: "flip_ud", 5: "flip_lr", 6: "rotate_cw"})


def rotate_counterclockwise(grid: list[list[int]]) -> list[list[int]]:
    return geometry_output(grid, mapping={3: "identity", 4: "flip_lr", 5: "flip_ud", 6: "rotate_ccw"})


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Execute the selected Racket authority; never silently fall back."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    import tempfile

    sys.path.insert(0, str(ROOT / "src"))
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    program = canonical()["program_solution"]
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "parity-request.json").write_text(
            json.dumps({"program": program, "grids": grids}), encoding="utf-8"
        )
        script = r'''import json
from pathlib import Path
from puzzle_generators import runner
request = json.loads(Path("parity-request.json").read_text())
bridge, name = runner._open_bridge_with_rule(runner.wrap_rule(request["program"]))
try:
    print(json.dumps([runner._apply_rule(bridge, name, grid) for grid in request["grids"]]))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(module: Any, per_band: int = 120) -> tuple[dict[str, Any], list[list[list[int]]]]:
    report: dict[str, Any] = {
        "schema": "4296e507c770-independent-audit-v1",
        "generator_version": module.VERSION,
        "sampler": {
            "bands": ["easy", "medium", "hard"],
            "per_band": per_band,
            "seed": "7100 + 1000*band_index + i",
            "sample_index": "13*i + 7",
        },
        "canonical": {},
        "by_band": {},
    }
    pairs = canonical_pairs()
    report["canonical"] = {
        "pairs": len(pairs),
        "python_oracle_matches": sum(geometry_output(pair["input"]) == pair["output"] for pair in pairs),
        "self_check_errors": [module.self_check(deepcopy(pair["input"])) for pair in pairs],
    }
    racket_batch = [deepcopy(pair["input"]) for pair in pairs]
    for band_index, band in enumerate(("easy", "medium", "hard")):
        counts = Counter()
        inputs: set[str] = set()
        outputs: set[str] = set()
        shapes: set[tuple[tuple[int, int], ...]] = set()
        profiles: set[tuple[int, int, int]] = set()
        for index in range(per_band):
            seed = 7100 + 1000 * band_index + index
            sample_index = 13 * index + 7
            grid = module.generate(seed, sample_index, difficulty=band)
            replay = module.generate(seed, sample_index, difficulty=band)
            info = facts(grid)
            intended = geometry_output(grid)
            counts["samples"] += 1
            counts["self_check_errors"] += bool(module.self_check(grid))
            counts["nondeterministic"] += grid != replay
            counts["all_marker_colors"] += info["marker_colors"] == {3, 4, 5, 6}
            counts["transform_separating"] += is_transform_separating(info["shape"])
            counts["identity_rival_disagreements"] += intended != identity_everywhere(grid)
            counts["mirror_swap_disagreements"] += intended != swap_mirrors(grid)
            counts["ccw_rival_disagreements"] += intended != rotate_counterclockwise(grid)
            inputs.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            outputs.add(hashlib.sha256(json.dumps(intended, separators=(",", ":")).encode()).hexdigest())
            shapes.add(info["shape"])
            profiles.add((info["grid_h"], info["grid_w"], len({v for row in grid for v in row})))
            if index < 12:
                racket_batch.append(grid)
        counts["unique_inputs"] = len(inputs)
        counts["unique_outputs"] = len(outputs)
        counts["unique_shapes"] = len(shapes)
        report["by_band"][band] = dict(counts, profiles=sorted(profiles))
    return report, racket_batch


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--per-band", type=int, default=120)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.per_band < 100:
        parser.error("--per-band must be at least 100")
    module = load_generator(args.generator)
    report, grids = audit(module, args.per_band)
    source = (args.generator or GENERATOR).resolve()
    report["generator_sha256"] = hashlib.sha256(source.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["racket"] = {"status": "not_requested", "checked": 0}
    if args.racket:
        actual = racket_outputs(grids)
        expected = [geometry_output(grid) for grid in grids]
        mismatches = [index for index, pair in enumerate(zip(actual, expected)) if pair[0] != pair[1]]
        report["racket"] = {
            "status": "pass" if not mismatches else "fail",
            "checked": len(grids),
            "mismatches": mismatches[:20],
        }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
