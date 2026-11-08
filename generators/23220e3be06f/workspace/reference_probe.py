"""Independent rule mirror and reproducible audit for 23220e3be06f.

The generator is loaded only through its public file path.  Geometry,
canonical-pair loading, axis observation, and the Python rule mirror are kept
here so reviewer tests do not merely re-assert the implementation under test.
Use ``--racket`` to require parity with the selected canonical Racket program.
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
from typing import Any, Iterable

TASK = "23220e3be06f"
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "shared"))
sys.path.insert(0, str(ROOT / "shared/runtime"))
sys.path.insert(0, str(ROOT / "src"))


def load_generator(path: str | os.PathLike[str] | None = None):
    selected = Path(
        path
        or os.environ.get("GENERATOR_UNDER_TEST")
        or ROOT / f"generators/{TASK}/generator.py"
    ).resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator_23220e3be06f", selected)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load generator from {selected}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _norm_grid(value: Any) -> list[list[int]]:
    if not value:
        return []
    if isinstance(value, list) and value and isinstance(value[0], str):
        return [[int(cell) for cell in row] for row in value]
    return [list(map(int, row)) for row in value]


def canonical_row() -> dict[str, Any]:
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") == TASK and row.get("program_solution"):
                return row
    raise ValueError(f"canonical task {TASK} is absent from {path}")


def canonical_pairs() -> list[dict[str, list[list[int]]]]:
    row = canonical_row()
    pairs: list[dict[str, list[list[int]]]] = []
    for split in ("train", "test"):
        raw = row.get(split) or []
        items = raw if isinstance(raw, list) else [raw]
        for pair in items:
            if not isinstance(pair, dict) or "input" not in pair or "output" not in pair:
                continue
            input_grid = _norm_grid(pair["input"])
            output_grid = _norm_grid(pair["output"])
            if input_grid and output_grid:
                pairs.append({"input": input_grid, "output": output_grid})
    return pairs


def normalized_rule_hash() -> str:
    source = str(canonical_row()["program_solution"])
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def crop_motif(grid: list[list[int]]) -> list[list[int]]:
    work = [list(row) for row in grid]
    if not work or not work[0]:
        raise ValueError("grid must be nonempty")
    work[0][0] = 0
    cells = [
        (row, col)
        for row, values in enumerate(work)
        for col, value in enumerate(values)
        if value != 0
    ]
    if not cells:
        raise ValueError("grid contains no motif after removing the command")
    r0 = min(row for row, _ in cells)
    r1 = max(row for row, _ in cells)
    c0 = min(col for _, col in cells)
    c1 = max(col for _, col in cells)
    return [values[c0 : c1 + 1] for values in work[r0 : r1 + 1]]


def transform_grid(grid: list[list[int]], code: int) -> list[list[int]]:
    source = [list(row) for row in grid]
    if not source or not source[0] or any(len(row) != len(source[0]) for row in source):
        raise ValueError("transform expects a nonempty rectangular grid")
    if code == 1:
        return source
    if code == 2:  # clockwise
        return [list(row) for row in zip(*source[::-1])]
    if code == 3:
        return [list(reversed(row)) for row in reversed(source)]
    if code == 4:  # counter-clockwise
        return [list(row) for row in zip(*source)][::-1]
    if code == 5:  # left-right
        return [list(reversed(row)) for row in source]
    if code == 6:  # up-down
        return [list(row) for row in reversed(source)]
    raise ValueError(f"command code {code!r} outside 1..6")


def reference_output(grid: list[list[int]]) -> list[list[int]]:
    code = grid[0][0]
    return transform_grid(crop_motif(grid), code)


def dihedral_images(grid: list[list[int]]) -> tuple[tuple[tuple[int, ...], ...], ...]:
    source = [list(row) for row in grid]
    rotations = [source]
    for _ in range(3):
        rotations.append([list(row) for row in zip(*rotations[-1][::-1])])
    reflected = [[list(reversed(row)) for row in image] for image in rotations]
    return tuple(tuple(tuple(row) for row in image) for image in rotations + reflected)


def colored_component_count(grid: list[list[int]]) -> int:
    h, w = len(grid), len(grid[0])
    unseen = {(r, c) for r in range(h) for c in range(w) if grid[r][c] != 0}
    count = 0
    while unseen:
        start = unseen.pop()
        color = grid[start[0]][start[1]]
        queue = deque([start])
        while queue:
            row, col = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxt = (row + dr, col + dc)
                if nxt in unseen and grid[nxt[0]][nxt[1]] == color:
                    unseen.remove(nxt)
                    queue.append(nxt)
        count += 1
    return count


def observed(grid: list[list[int]]) -> dict[str, Any]:
    motif = crop_motif(grid)
    colors = {value for row in motif for value in row if value != 0}
    if len(colors) != 2:
        raise ValueError(f"expected exactly two motif colors, found {sorted(colors)}")
    code = grid[0][0]
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "code": code,
        "n_cells": sum(value != 0 for row in motif for value in row),
        "palette_mode": "overlap" if code in colors else "distinct",
    }


def canonical_profile(grid: list[list[int]]) -> tuple[int, int, int]:
    return (len(grid), len(grid[0]), len({value for row in grid for value in row}))


def rotations_only_rival(grid: list[list[int]]) -> list[list[int]]:
    code = grid[0][0]
    # Plausible shortcut induced by the visible written description and all
    # five canonical pairs: commands 5/6 are treated as identity.
    return transform_grid(crop_motif(grid), code if code in (1, 2, 3, 4) else 1)


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Run the selected Racket authority in one batch; never fall back."""
    from arc_repl.racket_bridge import RacketUnavailableError, racket_runtime_status

    status = racket_runtime_status()
    if not status["available"]:
        raise RacketUnavailableError(status["reason"])

    import tempfile

    from arcpuzzles import Catalog
    from arcpuzzles.runtime import prepare_runtime, run_process

    with tempfile.TemporaryDirectory(prefix=f"{TASK}-parity-") as directory:
        stage = Path(directory)
        prepare_runtime(Catalog(ROOT), stage, TASK)
        request = {"grids": grids}
        (stage / "parity-request.json").write_text(json.dumps(request), encoding="utf-8")
        script = r'''
import json
from pathlib import Path
from puzzle_generators import runner
bundle = runner._load_bundle("23220e3be06f")
bridge, name = runner._open_bridge_with_rule(bundle.rule_callable_text)
try:
    request = json.loads(Path("parity-request.json").read_text())
    outputs = [runner._apply_rule(bridge, name, grid) for grid in request["grids"]]
    print(json.dumps(outputs))
finally:
    bridge.close()
'''
        result = run_process([sys.executable, "-B", "-c", script], stage, timeout=180)
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(
                "Racket parity worker failed: "
                + result.get("stderr", "")
                + result.get("stdout", "")
            )
        return json.loads(result["stdout"])


def audit(module: Any, count: int) -> tuple[dict[str, Any], list[list[list[int]]]]:
    canonical = canonical_pairs()
    canonical_profiles = {canonical_profile(pair["input"]) for pair in canonical}
    retained = [deepcopy(pair["input"]) for pair in canonical]
    report: dict[str, Any] = {
        "schema": f"{TASK}-independent-audit-v1",
        "version": getattr(module, "VERSION", None),
        "rule_hash": normalized_rule_hash(),
        "canonical_pairs": len(canonical),
        "canonical_python_matches": sum(
            reference_output(pair["input"]) == pair["output"] for pair in canonical
        ),
        "canonical_self_check_errors": [module.self_check(pair["input"]) for pair in canonical],
        "by_band": {},
    }
    all_digests: set[str] = set()
    for band_index, band in enumerate(("easy", "medium", "hard")):
        counts = Counter()
        codes: set[int] = set()
        modes: set[str] = set()
        profiles: set[tuple[int, int, int]] = set()
        band_digests: set[str] = set()
        for index in range(count):
            seed = int(
                hashlib.sha256(
                    f"{TASK}:independent-probe:{band}:{index}".encode()
                ).hexdigest()[:12],
                16,
            )
            sample_index = index * 11 + 3
            grid = module.generate(seed, sample_index, difficulty=band)
            digest = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
            all_digests.add(digest)
            band_digests.add(digest)
            facts = observed(grid)
            codes.add(facts["code"])
            modes.add(facts["palette_mode"])
            profile = canonical_profile(grid)
            profiles.add(profile)
            counts["samples"] += 1
            counts["self_check_errors"] += bool(module.self_check(grid))
            counts["nondeterministic"] += grid != module.generate(seed, sample_index, difficulty=band)
            counts["canonical_profile_hits"] += profile in canonical_profiles
            counts["fully_asymmetric"] += len(set(dihedral_images(crop_motif(grid)))) == 8
            counts["flip_counterexamples"] += rotations_only_rival(grid) != reference_output(grid)
            if len(retained) < 64:
                retained.append(grid)
        report["by_band"][band] = {
            **dict(counts),
            "distinct_inputs": len(band_digests),
            "codes": sorted(codes),
            "palette_modes": sorted(modes),
            "profiles": sorted(profiles),
        }
    report["distinct_inputs"] = len(all_digests)
    report["sampling_design"] = (
        "Band/index SHA-256-derived seeds with sample_index=11*i+3; exact "
        "set-cardinality counts, not independence estimates."
    )
    return report, retained


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=120, help="samples per band")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report, grids = audit(module, args.count)
    selected = args.generator or ROOT / f"generators/{TASK}/generator.py"
    report["generator_sha256"] = hashlib.sha256(Path(selected).read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["racket"] = {"status": "not_requested", "checked": 0}
    exit_code = int(
        any(report["canonical_self_check_errors"])
        or any(
            row["self_check_errors"] or row["nondeterministic"]
            for row in report["by_band"].values()
        )
    )
    if args.racket:
        outputs = racket_outputs(grids)
        expected = [reference_output(grid) for grid in grids]
        mismatches = [index for index, (got, want) in enumerate(zip(outputs, expected)) if got != want]
        report["racket"] = {
            "status": "pass" if not mismatches and len(outputs) == len(expected) else "fail",
            "checked": len(outputs),
            "mismatch_indexes": mismatches[:20],
        }
        exit_code |= int(bool(mismatches) or len(outputs) != len(expected))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
