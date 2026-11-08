"""Independent oracle and distribution probe for b9e736518d82.

This module intentionally does not import generator geometry helpers.  It
reconstructs the canonical channel from the input pixels, applies the selected
Racket rule in Python for regression evidence, and can optionally compare a
batch with the real Racket authority.  The Python oracle is supplementary test
evidence, never a replacement label authority.
"""
from __future__ import annotations

import argparse
from collections import Counter, deque
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from typing import Iterable

ROOT = Path(__file__).resolve().parents[3]
TASK = "b9e736518d82"
CARDINAL = ((-1, 0), (1, 0), (0, -1), (0, 1))


def load_generator(path: str | Path | None = None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_rows() -> list[dict]:
    rows: list[dict] = []
    with (ROOT / "shared/data/canonical/puzzles.jsonl").open() as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                rows.append(row)
    if not rows:
        raise ValueError(f"canonical task {TASK} is absent")
    return rows


def canonical_program() -> str:
    programs = {row["program_solution"] for row in canonical_rows()}
    if len(programs) != 1:
        raise ValueError("canonical rows disagree on program_solution")
    return programs.pop()


def canonical_pairs() -> list[dict]:
    pairs: list[dict] = []
    for row in canonical_rows():
        pairs.extend(row.get("train", []))
        test = row.get("test", [])
        pairs.extend(test if isinstance(test, list) else [test])
    return pairs


def authority_target_paths() -> tuple[Path, ...]:
    return (
        ROOT / "shared/data/base/solutions/training/f1bcbc2c__b9e736518d82.json",
        ROOT / "shared/data/base/solutions/augmented/f1bcbc2c__012289367e46.json",
    )


def authority_target_codes() -> dict[str, str]:
    return {
        str(path.relative_to(ROOT)): json.loads(path.read_text())["racket_target"]["target_code"]
        for path in authority_target_paths()
    }


def _shape(grid) -> tuple[int, int]:
    if not isinstance(grid, (list, tuple)) or not grid:
        raise ValueError("expected a nonempty grid")
    if not isinstance(grid[0], (list, tuple)) or not grid[0]:
        raise ValueError("expected nonempty rows")
    width = len(grid[0])
    if any(not isinstance(row, (list, tuple)) or len(row) != width for row in grid):
        raise ValueError("ragged grid")
    return len(grid), width


def _neighbors(point: tuple[int, int]) -> Iterable[tuple[int, int]]:
    r, c = point
    for dr, dc in CARDINAL:
        yield r + dr, c + dc


def _bfs(start: tuple[int, int], pool: set[tuple[int, int]]) -> set[tuple[int, int]]:
    visited = {start}
    queue = deque([start])
    while queue:
        point = queue.popleft()
        for nxt in _neighbors(point):
            if nxt in pool and nxt not in visited:
                visited.add(nxt)
                queue.append(nxt)
    return visited


def adjacent_orange_band(grid) -> list[tuple[int, int]]:
    """Canonical row-major list of 0/9 cells cardinally adjacent to orange."""
    h, w = _shape(grid)
    result: list[tuple[int, int]] = []
    for r in range(h):
        for c in range(w):
            if grid[r][c] not in (0, 9):
                continue
            if any(
                0 <= nr < h and 0 <= nc < w and grid[nr][nc] == 7
                for nr, nc in _neighbors((r, c))
            ):
                result.append((r, c))
    return result


def authority_channel(grid) -> set[tuple[int, int]]:
    """Reproduce the authority's component choice, including no-marker order."""
    band = adjacent_orange_band(grid)
    if not band:
        raise ValueError("no 0/9 cell is adjacent to orange")
    pool = set(band)
    markers = [point for point in band if grid[point[0]][point[1]] == 9]
    if markers:
        return _bfs(markers[0], pool)
    comp1 = _bfs(band[0], pool)
    remaining = [point for point in band if point not in comp1]
    if not remaining:
        return comp1
    comp2 = _bfs(remaining[0], pool)
    return comp1 if len(comp1) > len(comp2) else comp2


def ordered_path(channel: set[tuple[int, int]]) -> list[tuple[int, int]]:
    """Return either orientation of a simple cardinal path or raise ValueError."""
    if len(channel) < 2:
        raise ValueError("channel is too short")
    adjacency = {
        point: sorted(nxt for nxt in _neighbors(point) if nxt in channel)
        for point in channel
    }
    bad = {point: len(nbrs) for point, nbrs in adjacency.items() if len(nbrs) not in (1, 2)}
    if bad:
        raise ValueError(f"channel is not a simple path: degrees={bad}")
    endpoints = sorted(point for point, nbrs in adjacency.items() if len(nbrs) == 1)
    if len(endpoints) != 2:
        raise ValueError(f"expected two path endpoints, found {len(endpoints)}")
    result = [endpoints[0]]
    previous = None
    current = endpoints[0]
    while current != endpoints[1]:
        candidates = [point for point in adjacency[current] if point != previous]
        if len(candidates) != 1:
            raise ValueError("path traversal became ambiguous")
        previous, current = current, candidates[0]
        result.append(current)
        if len(result) > len(channel):
            raise ValueError("path traversal cycled")
    if set(result) != channel:
        raise ValueError("path is disconnected")
    return result


def path_turns(path: list[tuple[int, int]]) -> list[int]:
    turns: list[int] = []
    for index in range(1, len(path) - 1):
        prev, cur, nxt = path[index - 1], path[index], path[index + 1]
        incoming = (cur[0] - prev[0], cur[1] - prev[1])
        outgoing = (nxt[0] - cur[0], nxt[1] - cur[1])
        if incoming != outgoing:
            turns.append(index)
    return turns


def expected_orange_walls(path: list[tuple[int, int]], h: int, w: int) -> set[tuple[int, int]]:
    """Exact canonical wall construction: sides plus the outer corner at bends."""
    channel = set(path)
    walls = {
        point
        for cell in channel
        for point in _neighbors(cell)
        if 0 <= point[0] < h and 0 <= point[1] < w and point not in channel
    }
    for index in path_turns(path):
        prev, cur, nxt = path[index - 1], path[index], path[index + 1]
        incoming = (cur[0] - prev[0], cur[1] - prev[1])
        outgoing = (nxt[0] - cur[0], nxt[1] - cur[1])
        outer = (cur[0] + incoming[0] - outgoing[0],
                 cur[1] + incoming[1] - outgoing[1])
        if 0 <= outer[0] < h and 0 <= outer[1] < w and outer not in channel:
            walls.add(outer)
    return walls


def marker_mode(grid, path: list[tuple[int, int]]) -> str:
    markers = [(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 9]
    if not markers:
        return "none"
    if len(markers) != 1 or markers[0] not in set(path):
        raise ValueError("expected zero or one marker on the selected channel")
    index = path.index(markers[0])
    if index in (0, len(path) - 1):
        raise ValueError("marker cannot be a channel endpoint")
    return "turn" if index in path_turns(path) else "straight"


def analyze(grid) -> dict:
    h, w = _shape(grid)
    channel = authority_channel(grid)
    path = ordered_path(channel)
    walls = {(r, c) for r, row in enumerate(grid) for c, value in enumerate(row) if value == 7}
    expected = expected_orange_walls(path, h, w)
    endpoints = (path[0], path[-1])
    return {
        "grid_h": h,
        "grid_w": w,
        "path": path,
        "channel": channel,
        "walls": walls,
        "expected_walls": expected,
        "wall_match": walls == expected,
        "turn_count": len(path_turns(path)),
        "marker_mode": marker_mode(grid, path),
        "endpoints": endpoints,
        "endpoints_on_boundary": all(
            r in (0, h - 1) or c in (0, w - 1) for r, c in endpoints
        ),
    }


def oracle_output(grid) -> list[list[int]]:
    """Independent Python mirror of the canonical Racket rule."""
    out = deepcopy(grid)
    channel = authority_channel(grid)
    markers = sorted(point for point in channel if grid[point[0]][point[1]] == 9)
    if not markers:
        fill = channel
    else:
        marker = markers[0]
        neighbors = [point for point in _neighbors(marker) if point in channel]
        same_col = all(point[1] == marker[1] for point in neighbors)
        same_row = all(point[0] == marker[0] for point in neighbors)
        if same_col or same_row:
            fill = channel
        else:
            without = set(channel) - {marker}
            first = min(without)
            half1 = _bfs(first, without)
            half2 = without - half1
            fill = half1 if len(half1) > len(half2) else half2
    for r, c in fill:
        out[r][c] = 8
    return out


def rival_marker_required(grid) -> list[list[int]]:
    if not any(value == 9 for row in grid for value in row):
        return deepcopy(grid)
    return oracle_output(grid)


def rival_fill_entire_channel(grid) -> list[list[int]]:
    out = deepcopy(grid)
    for r, c in authority_channel(grid):
        out[r][c] = 8
    return out


def rival_split_every_marker(grid) -> list[list[int]]:
    channel = authority_channel(grid)
    marker = next(((r, c) for r, c in channel if grid[r][c] == 9), None)
    if marker is None:
        return oracle_output(grid)
    without = set(channel) - {marker}
    half1 = _bfs(min(without), without)
    half2 = without - half1
    fill = half1 if len(half1) > len(half2) else half2
    out = deepcopy(grid)
    for r, c in fill:
        out[r][c] = 8
    return out


def racket_outputs(grids: list[list[list[int]]]) -> list[list[list[int]]]:
    """Apply the real selected Racket authority to a batch; never fall back."""
    from arc_repl.racket_bridge import racket_runtime_status, RacketUnavailableError
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
        request = {"program": canonical_program(), "grids": grids}
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
        if result["exit_code"] or result["timed_out"]:
            raise RuntimeError(f"Racket worker failed: {result['stderr']} {result['stdout']}")
        outputs = json.loads(result["stdout"])
        if len(outputs) != len(grids):
            raise RuntimeError("Racket worker returned an incomplete batch")
        return outputs


def audit(module, count: int) -> tuple[dict, list]:
    by_band: dict[str, dict] = {}
    all_grids: list = []
    canonical = canonical_pairs()
    canonical_errors = [module.self_check(pair["input"]) for pair in canonical]
    canonical_oracle_matches = sum(oracle_output(pair["input"]) == pair["output"] for pair in canonical)
    total = Counter()
    for band in (None, "easy", "medium", "hard"):
        counts = Counter()
        shapes: set[tuple[int, int]] = set()
        turns: set[int] = set()
        modes: set[str] = set()
        hashes: set[str] = set()
        endpoint_bins: set[tuple[tuple[bool, bool, bool, bool], ...]] = set()
        for index in range(count):
            grid = module.generate(9001 + index, index * 7 + 3, difficulty=band)
            info = analyze(grid)
            issues = module.self_check(grid)
            counts["samples"] += 1
            counts["self_check_errors"] += bool(issues)
            counts["wall_mismatches"] += not info["wall_match"]
            counts["nondeterministic"] += grid != module.generate(9001 + index, index * 7 + 3, difficulty=band)
            truth = oracle_output(grid)
            counts["changed"] += truth != grid
            if info["marker_mode"] == "none":
                counts["marker_required_disagreements"] += rival_marker_required(grid) != truth
            elif info["marker_mode"] == "turn":
                counts["fill_entire_disagreements"] += rival_fill_entire_channel(grid) != truth
            else:
                counts["split_every_marker_disagreements"] += rival_split_every_marker(grid) != truth
            shapes.add((info["grid_h"], info["grid_w"]))
            turns.add(info["turn_count"])
            modes.add(info["marker_mode"])
            hashes.add(hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest())
            h, w = info["grid_h"], info["grid_w"]
            endpoint_bins.add(tuple((r == 0, r == h - 1, c == 0, c == w - 1) for r, c in info["endpoints"]))
            if index < 12:
                all_grids.append(grid)
        counts.update({
            "distinct_shapes": len(shapes),
            "distinct_inputs": len(hashes),
            "endpoint_bins": len(endpoint_bins),
        })
        by_band[str(band)] = dict(counts, turn_counts=sorted(turns), marker_modes=sorted(modes))
        total.update(counts)
    report = {
        "schema": f"{TASK}-independent-audit-v1",
        "version": module.VERSION,
        "rule_hash": hashlib.sha256(" ".join(canonical_program().split()).encode()).hexdigest()[:12],
        "canonical_pairs": len(canonical),
        "canonical_oracle_matches": canonical_oracle_matches,
        "canonical_self_check_errors": canonical_errors,
        "counts": dict(total),
        "by_band": by_band,
        "sampling_design": (
            "Each band uses count deterministic seed/index pairs; the same index schedule is crossed "
            "with bands, so pooled counts are not claimed as independent draws."
        ),
        "warning": "Python geometry is supplementary evidence, not Racket runtime validation.",
    }
    return report, [pair["input"] for pair in canonical] + all_grids


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=250, help="samples per difficulty band")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report, grids = audit(module, args.count)
    path = (args.generator or ROOT / f"generators/{TASK}/generator.py").resolve()
    report["generator_sha256"] = hashlib.sha256(path.read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["racket"] = {"status": "not_requested", "checked": 0}
    exit_code = int(
        any(report["canonical_self_check_errors"])
        or report["canonical_oracle_matches"] != report["canonical_pairs"]
        or report["counts"].get("self_check_errors", 0)
        or report["counts"].get("wall_mismatches", 0)
        or report["counts"].get("nondeterministic", 0)
    )
    if args.racket:
        try:
            outputs = racket_outputs(grids)
            mismatches = [index for index, (grid, output) in enumerate(zip(grids, outputs)) if oracle_output(grid) != output]
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
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({key: report[key] for key in ("version", "canonical_oracle_matches", "counts", "racket")}, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
