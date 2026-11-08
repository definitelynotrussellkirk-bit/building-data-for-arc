"""Independent geometry oracle and reproducible audit for 85e65da9fb15.

This file is review/test tooling.  The selected Racket program remains label
authority; the Python implementation exists to make geometry hypotheses,
shortcut counterexamples, and source-bound parity checks cheap to replay.
"""
from __future__ import annotations

import argparse
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
TASK = "85e65da9fb15"
sys.path.insert(0, str(ROOT / "shared/runtime"))
sys.path.insert(0, str(ROOT / "src"))


def load_generator(path: str | Path | None = None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical() -> dict:
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                return row
    raise ValueError(f"canonical task {TASK} is absent")


def canonical_pairs() -> list[dict]:
    row = canonical()
    test = row.get("test", [])
    if isinstance(test, dict):
        test = [test]
    return list(row.get("train", [])) + list(test)


def canonical_rule_hash() -> str:
    source = canonical()["program_solution"]
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def _components(grid: list[list[int]]) -> list[dict]:
    h, w = len(grid), len(grid[0])
    seen: set[tuple[int, int]] = set()
    objects: list[dict] = []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if color == 0 or (r, c) in seen:
                continue
            stack = [(r, c)]
            seen.add((r, c))
            cells: list[tuple[int, int]] = []
            while stack:
                rr, cc = stack.pop()
                cells.append((rr, cc))
                for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    nr, nc = rr + dr, cc + dc
                    if (0 <= nr < h and 0 <= nc < w and
                            (nr, nc) not in seen and grid[nr][nc] == color):
                        seen.add((nr, nc))
                        stack.append((nr, nc))
            r1 = min(x for x, _ in cells)
            c1 = min(y for _, y in cells)
            r2 = max(x for x, _ in cells)
            c2 = max(y for _, y in cells)
            objects.append({
                "color": color,
                "cells": tuple(sorted(cells)),
                "r1": r1, "c1": c1, "r2": r2, "c2": c2,
                "h": r2 - r1 + 1, "w": c2 - c1 + 1,
                "size": len(cells),
            })
    return objects


def _is_frame(obj: dict) -> bool:
    if obj["h"] < 3 or obj["w"] < 3:
        return False
    border = {
        (r, c)
        for r in range(obj["r1"], obj["r2"] + 1)
        for c in range(obj["c1"], obj["c2"] + 1)
        if r in (obj["r1"], obj["r2"]) or c in (obj["c1"], obj["c2"])
    }
    return set(obj["cells"]) == border


def _object_grid(obj: dict) -> list[list[int]]:
    out = [[0] * obj["w"] for _ in range(obj["h"])]
    for r, c in obj["cells"]:
        out[r - obj["r1"]][c - obj["c1"]] = obj["color"]
    return out


def _rotate_cw(grid: list[list[int]]) -> list[list[int]]:
    return [list(row) for row in zip(*grid[::-1])]


def _stamp(out: list[list[int]], sub: list[list[int]], r0: int, c0: int) -> None:
    for r, row in enumerate(sub):
        for c, value in enumerate(row):
            if value and 0 <= r0 + r < len(out) and 0 <= c0 + c < len(out[0]):
                out[r0 + r][c0 + c] = value


def _ordered_solids(objects: list[dict], order: str) -> list[dict]:
    solids = [obj for obj in objects if not _is_frame(obj)]
    if order == "top_left":
        return sorted(solids, key=lambda obj: (obj["r1"], obj["c1"]))
    if order == "area":
        return sorted(solids, key=lambda obj: (obj["size"], obj["r1"], obj["c1"]))
    raise ValueError(f"unknown solid order {order!r}")


def reference_output(
    grid: list[list[int]], *, placement: str = "center",
    solid_order: str = "top_left", allow_rotation: bool = True,
    exact_only: bool = False,
) -> list[list[int]]:
    """Independent implementation of the selected rule plus narrow rivals."""
    objects = _components(grid)
    frames = sorted(
        [obj for obj in objects if _is_frame(obj)],
        key=lambda obj: (obj["r1"], obj["c1"]),
    )
    solids = _ordered_solids(objects, solid_order)
    out = [[0] * len(grid[0]) for _ in grid]
    for frame in frames:
        for r, c in frame["cells"]:
            out[r][c] = frame["color"]

    used: set[int] = set()
    for solid in solids:
        original = _object_grid(solid)
        rotated = _rotate_cw(original)
        candidates: list[tuple] = []
        for index, frame in enumerate(frames):
            if index in used:
                continue
            ih, iw = frame["h"] - 2, frame["w"] - 2
            oriented = None
            if len(original) <= ih and len(original[0]) <= iw:
                oriented = original
            elif allow_rotation and len(rotated) <= ih and len(rotated[0]) <= iw:
                oriented = rotated
            if oriented is None:
                continue
            if exact_only and (len(oriented), len(oriented[0])) != (ih, iw):
                continue
            leftover = ih * iw - len(oriented) * len(oriented[0])
            candidates.append((leftover, frame["r1"], frame["c1"], index, frame, oriented))
        if not candidates:
            continue
        _, _, _, index, frame, oriented = min(candidates, key=lambda item: item[:3])
        used.add(index)
        if placement == "center":
            r0 = frame["r1"] + 1 + (frame["h"] - 2 - len(oriented)) // 2
            c0 = frame["c1"] + 1 + (frame["w"] - 2 - len(oriented[0])) // 2
        elif placement == "top_left":
            r0, c0 = frame["r1"] + 1, frame["c1"] + 1
        else:
            raise ValueError(f"unknown placement {placement!r}")
        _stamp(out, oriented, r0, c0)
    return out


def frame_first_output(grid: list[list[int]]) -> list[list[int]]:
    """Plausible rival: process frames top-left and take first fitting solid."""
    objects = _components(grid)
    frames = sorted([obj for obj in objects if _is_frame(obj)], key=lambda x: (x["r1"], x["c1"]))
    solids = sorted([obj for obj in objects if not _is_frame(obj)], key=lambda x: (x["r1"], x["c1"]))
    out = [[0] * len(grid[0]) for _ in grid]
    for frame in frames:
        for r, c in frame["cells"]:
            out[r][c] = frame["color"]
    used: set[int] = set()
    for frame in frames:
        ih, iw = frame["h"] - 2, frame["w"] - 2
        for index, solid in enumerate(solids):
            if index in used:
                continue
            original = _object_grid(solid)
            rotated = _rotate_cw(original)
            if len(original) <= ih and len(original[0]) <= iw:
                oriented = original
            elif len(rotated) <= ih and len(rotated[0]) <= iw:
                oriented = rotated
            else:
                continue
            used.add(index)
            r0 = frame["r1"] + 1 + (ih - len(oriented)) // 2
            c0 = frame["c1"] + 1 + (iw - len(oriented[0])) // 2
            _stamp(out, oriented, r0, c0)
            break
    return out


def object_count(grid: list[list[int]]) -> int:
    return len(_components(grid))


def palette_profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return len(grid), len(grid[0]), len({value for row in grid for value in row})


def racket_outputs(grids: Iterable[list[list[int]]]) -> list[list[list[int]]]:
    """Require the real canonical Racket worker; never silently fall back."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError
    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])
    import tempfile
    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    grids = list(grids)
    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        (stage / "request.json").write_text(json.dumps({
            "program": canonical()["program_solution"], "grids": grids,
        }))
        script = """
import json
from pathlib import Path
from puzzle_generators import runner
req=json.loads(Path('request.json').read_text())
bridge,name=runner._open_bridge_with_rule(runner.wrap_rule(req['program']))
try:
    print(json.dumps([runner._apply_rule(bridge,name,g) for g in req['grids']]))
finally:
    bridge.close()
"""
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=240)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(module, count: int) -> tuple[dict, list[list[list[int]]]]:
    canonical_rows = canonical_pairs()
    canonical_mismatches = [
        i for i, pair in enumerate(canonical_rows)
        if reference_output(pair["input"]) != pair["output"]
    ]
    canonical_shortcuts = {
        "top_left_in_frame": lambda g: reference_output(g, placement="top_left"),
        "exact_bbox_only": lambda g: reference_output(g, exact_only=True),
        "solid_area_order": lambda g: reference_output(g, solid_order="area"),
    }
    shortcut_fit = {
        name: all(fn(pair["input"]) == pair["output"] for pair in canonical_rows)
        for name, fn in canonical_shortcuts.items()
    }
    bands: dict[str, dict] = {}
    retained: list[list[list[int]]] = [pair["input"] for pair in canonical_rows]
    profiles: set[tuple[int, int, int]] = set()
    for band in (None, "easy", "medium", "hard"):
        unique: set[str] = set()
        profile_counts: dict[str, int] = {}
        witness_counts = {name: 0 for name in getattr(module, "SEMANTIC_WITNESSES", {})}
        errors = nondeterministic = 0
        for index in range(count):
            grid = module.generate(1009 + index, index * 7 + 3, difficulty=band)
            errors += bool(module.self_check(grid))
            nondeterministic += grid != module.generate(1009 + index, index * 7 + 3, difficulty=band)
            digest = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
            unique.add(digest)
            profile = palette_profile(grid)
            profiles.add(profile)
            key = "x".join(map(str, profile))
            profile_counts[key] = profile_counts.get(key, 0) + 1
            for name, predicate in getattr(module, "SEMANTIC_WITNESSES", {}).items():
                witness_counts[name] += bool(predicate(deepcopy(grid)))
            if index < 8:
                retained.append(grid)
        bands[str(band)] = {
            "draws": count,
            "self_check_errors": errors,
            "nondeterministic": nondeterministic,
            "distinct_inputs": len(unique),
            "profiles": profile_counts,
            "witness_hits": witness_counts,
        }
    report = {
        "schema": f"{TASK}-independent-audit-v1",
        "task_id": TASK,
        "version": module.VERSION,
        "rule_hash": canonical_rule_hash(),
        "canonical_reference_mismatches": canonical_mismatches,
        "canonical_shortcut_fit": shortcut_fit,
        "bands": bands,
        "distinct_profiles": sorted(profiles),
        "generator_sha256": hashlib.sha256(Path(module.__file__).read_bytes()).hexdigest(),
        "probe_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "sampling_design": (
            "Deterministic crossed seed/index schedules per band; counts are a replayable "
            "census, not an independent random sample or a universal proof."
        ),
        "racket": {"status": "not_requested", "checked": 0},
    }
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
    exit_code = int(
        bool(report["canonical_reference_mismatches"])
        or any(row["self_check_errors"] or row["nondeterministic"] for row in report["bands"].values())
        or not all(report["canonical_shortcut_fit"].values())
    )
    if args.racket:
        try:
            expected = [reference_output(grid) for grid in grids]
            actual = racket_outputs(grids)
            mismatches = [i for i, (a, b) in enumerate(zip(expected, actual)) if a != b]
            report["racket"] = {
                "status": "passed" if not mismatches else "failed",
                "checked": len(actual), "mismatches": mismatches,
            }
            exit_code = max(exit_code, int(bool(mismatches)))
        except Exception as exc:
            report["racket"] = {
                "status": "unavailable_or_failed", "checked": 0,
                "error": f"{type(exc).__name__}: {exc}",
            }
            exit_code = 2
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    print(json.dumps({
        "canonical_reference_mismatches": report["canonical_reference_mismatches"],
        "canonical_shortcut_fit": report["canonical_shortcut_fit"],
        "bands": report["bands"], "racket": report["racket"],
    }, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
