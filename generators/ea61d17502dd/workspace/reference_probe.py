"""Independent rule mirror and coverage probe for ``ea61d17502dd``.

The reviewed generator is loaded only by :func:`load_generator`.  Geometry,
canonical-data decoding, authority discovery, and rival behavior are kept here
so task-local tests do not validate the generator with its own implementation.
The selected Racket rule remains the label authority; ``racket_outputs`` never
falls back to the Python mirror.
"""
from __future__ import annotations

import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
TASK = "ea61d17502dd"
RULE_HASH = "b956a6f1bc99"
sys.path.insert(0, str(ROOT / "shared" / "runtime"))


def load_generator(path=None):
    path = Path(path or ROOT / f"generators/{TASK}/generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_generator", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _decode_grid(grid):
    if grid and isinstance(grid[0], str):
        return [[int(ch) for ch in row] for row in grid]
    return [list(row) for row in grid]


def canonical_rows():
    rows = []
    path = ROOT / "shared/data/canonical/puzzles.jsonl"
    with path.open(encoding="utf-8") as stream:
        for line in stream:
            row = json.loads(line)
            if row.get("task_id") == TASK:
                rows.append(row)
    if not rows:
        raise ValueError(f"canonical task {TASK} is absent")
    return rows


def canonical_program():
    programs = {row["program_solution"] for row in canonical_rows()}
    if len(programs) != 1:
        raise ValueError(f"expected one canonical program, found {len(programs)}")
    return programs.pop()


def normalized_rule_hash(program):
    return hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12]


def canonical_pairs(*, unique=True):
    pairs = []
    seen = set()
    for row in canonical_rows():
        test = row.get("test") or []
        if isinstance(test, dict):
            test = [test]
        for pair in [*(row.get("train") or []), *test]:
            decoded = {
                "input": _decode_grid(pair["input"]),
                "output": _decode_grid(pair["output"]),
            }
            digest = hashlib.sha256(
                json.dumps(decoded, separators=(",", ":"), sort_keys=True).encode()
            ).hexdigest()
            if unique and digest in seen:
                continue
            seen.add(digest)
            pairs.append(decoded)
    return pairs


def authority_files():
    base = ROOT / "shared/data/base/solutions"
    paths = [
        base / "training/f3e14006__ea61d17502dd.json",
        base / "augmented/f3e14006__f4eca8c1e3b7.json",
    ]
    missing = [str(path) for path in paths if not path.exists()]
    if missing:
        raise FileNotFoundError(f"missing authority carriers: {missing}")
    return paths


def _dominant_index(counts):
    best = max(counts)
    return counts.index(best)


def recover(grid):
    """Recover the four colors, marker positions, and crossing ownership."""
    h, w = len(grid), len(grid[0])
    row = _dominant_index([sum(value > 0 for value in values) for values in grid])
    col = _dominant_index([
        sum(grid[r][c] > 0 for r in range(h)) for c in range(w)
    ])
    hvals = [grid[row][c] for c in range(w) if c != col and grid[row][c] > 0]
    vvals = [grid[r][col] for r in range(h) if r != row and grid[r][col] > 0]
    hbase = max(dict.fromkeys(hvals), key=lambda value: hvals.count(value))
    vbase = max(dict.fromkeys(vvals), key=lambda value: vvals.count(value))
    hspec = next(value for value in hvals if value != hbase)
    vspec = next(value for value in vvals if value != vbase)
    hcols = [c for c in range(w) if c != col and grid[row][c] == hspec]
    vrows = [r for r in range(h) if r != row and grid[r][col] == vspec]
    hsegment = [c for c in range(w) if grid[row][c] > 0]
    vsegment = [r for r in range(h) if grid[r][col] > 0]
    return {
        "h": h,
        "w": w,
        "row": row,
        "col": col,
        "hbase": hbase,
        "hspec": hspec,
        "vbase": vbase,
        "vspec": vspec,
        "hcols": hcols,
        "vrows": vrows,
        "hsegment": hsegment,
        "vsegment": vsegment,
        "primary": "horizontal" if grid[row][col] == hbase else "vertical",
    }


def _weave(grid, *, crossing_to_farthest=False):
    info = recover(grid)
    h, w = info["h"], info["w"]
    row = info["row"]
    vrows = info["vrows"]
    hcols = info["hcols"]
    near = min(vrows, key=lambda r: abs(r - row))
    far = max(vrows, key=lambda r: abs(r - row))
    if crossing_to_farthest:
        min_row, max_row = sorted((row, far))
    else:
        min_row = min([row, *vrows])
        max_row = max([row, *vrows])
    min_col, max_col = min(hcols), max(hcols)
    horizontal_primary = info["primary"] == "horizontal"
    out = [[0] * w for _ in range(h)]
    for r in range(min_row, max_row + 1):
        warp_row = (r - min_row) % 2 == 0
        in_band = min(near, far) <= r <= max(near, far)
        for c in range(min_col, max_col + 1):
            warp_col = (c - min_col) % 2 == 0
            if warp_row:
                if in_band:
                    if warp_col:
                        value = info["vspec"]
                    elif r == near and horizontal_primary:
                        value = info["hbase"]
                    else:
                        value = info["vbase"]
                else:
                    value = info["hspec"] if warp_col else info["vbase"]
            elif horizontal_primary:
                value = info["hbase"]
            else:
                value = info["hbase"] if warp_col else info["vbase"]
            out[r][c] = value
    return out


def rule_output(grid):
    """Independent transliteration of the selected canonical Racket rule."""
    return _weave(deepcopy(grid), crossing_to_farthest=False)


def crossing_to_farthest_output(grid):
    """Canonical-fitting shortcut: use only crossing and far vertical marker.

    All public pairs put both vertical markers on one side of the crossing, so
    this shortcut has the same vertical bounds there.  It fails when the two
    vertical markers straddle the crossing.
    """
    return _weave(deepcopy(grid), crossing_to_farthest=True)


def observed(grid):
    info = recover(grid)
    full = (
        info["hsegment"] == list(range(info["w"]))
        and info["vsegment"] == list(range(info["h"]))
    )
    partial = (
        info["hsegment"] != list(range(info["w"]))
        and info["vsegment"] != list(range(info["h"]))
    )
    row = info["row"]
    lo, hi = min(info["vrows"]), max(info["vrows"])
    return {
        "grid_h": info["h"],
        "grid_w": info["w"],
        "primary": info["primary"],
        "vertical_relation": "straddle" if lo < row < hi else "outside",
        "strand_extent": "full" if full else "partial" if partial else "mixed",
    }


def racket_outputs(grids):
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
    bridge.shutdown()
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


def audit(module, count):
    report = {
        "schema": "ea61d17502dd-independent-audit-v1",
        "version": module.VERSION,
        "canonical_pairs": len(canonical_pairs()),
        "canonical_self_check_errors": [],
        "canonical_rule_mismatches": [],
        "canonical_shortcut_mismatches": [],
        "by_band": {},
    }
    for index, pair in enumerate(canonical_pairs()):
        errors = module.self_check(deepcopy(pair["input"]))
        if errors:
            report["canonical_self_check_errors"].append({"index": index, "errors": errors})
        if rule_output(pair["input"]) != pair["output"]:
            report["canonical_rule_mismatches"].append(index)
        if crossing_to_farthest_output(pair["input"]) != pair["output"]:
            report["canonical_shortcut_mismatches"].append(index)

    parity = [pair["input"] for pair in canonical_pairs()]
    all_inputs = set()
    for band in (None, "easy", "medium", "hard"):
        counts = Counter()
        shapes, primaries, relations, extents, unique = set(), set(), set(), set(), set()
        for index in range(count):
            grid = module.generate(4100 + index, index, difficulty=band)
            obs = observed(grid)
            counts["samples"] += 1
            counts["self_check_errors"] += bool(module.self_check(grid))
            counts["nondeterministic"] += grid != module.generate(4100 + index, index, difficulty=band)
            counts["rule_changes_input"] += rule_output(grid) != grid
            counts["shortcut_disagreements"] += rule_output(grid) != crossing_to_farthest_output(grid)
            shapes.add((obs["grid_h"], obs["grid_w"]))
            primaries.add(obs["primary"])
            relations.add(obs["vertical_relation"])
            extents.add(obs["strand_extent"])
            digest = hashlib.sha256(json.dumps(grid, separators=(",", ":")).encode()).hexdigest()
            unique.add(digest)
            if index < 8:
                parity.append(grid)
        all_inputs.update(unique)
        report["by_band"][str(band)] = {
            **dict(counts),
            "shapes": sorted(shapes),
            "primaries": sorted(primaries),
            "relations": sorted(relations),
            "extents": sorted(extents),
            "unique_inputs": len(unique),
        }
    report["unique_inputs"] = len(all_inputs)
    return report, parity


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=100)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--racket", action="store_true")
    args = parser.parse_args()
    module = load_generator(args.generator)
    report, grids = audit(module, args.count)
    source = args.generator or ROOT / f"generators/{TASK}/generator.py"
    report["generator_sha256"] = hashlib.sha256(Path(source).read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    report["rule_hash"] = normalized_rule_hash(canonical_program())
    report["racket"] = {"status": "not_requested", "checked": 0}
    exit_code = int(
        bool(report["canonical_self_check_errors"])
        or bool(report["canonical_rule_mismatches"])
        or any(row["self_check_errors"] or row["nondeterministic"] for row in report["by_band"].values())
    )
    if args.racket:
        try:
            outputs = racket_outputs(grids)
            mismatches = [
                index for index, (grid, output) in enumerate(zip(grids, outputs))
                if rule_output(grid) != output
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
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
