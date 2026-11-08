"""Independent oracle and repeatable review probes for generator 9bd5d9c04dd8.

The helpers deliberately reimplement the public rule from grid geometry instead
of importing private functions from ``generator.py``.  They are test/review
instrumentation, not a replacement label authority.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

try:
    from reviewer_support import canonical_pairs as _canonical_pairs, canonical_path, find_root
except ModuleNotFoundError:  # owner checkout outside the portable test runtime
    _guess = Path(__file__).resolve().parents[3] / "shared" / "runtime"
    sys.path.insert(0, str(_guess))
    from reviewer_support import canonical_pairs as _canonical_pairs, canonical_path, find_root

TASK_ID = "9bd5d9c04dd8"
ROOT = find_root(__file__)


def load_generator(path: str | Path | None = None):
    source = Path(path or ROOT / "generators" / TASK_ID / "generator.py").resolve()
    spec = importlib.util.spec_from_file_location("reviewed_9bd5d9c04dd8", source)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load generator from {source}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def canonical_pairs():
    return _canonical_pairs(TASK_ID, root=ROOT, labeled_only=True)


def canonical_program() -> str:
    programs = []
    with canonical_path(ROOT).open(encoding="utf-8") as handle:
        for line in handle:
            row = json.loads(line)
            if row.get("task_id") == TASK_ID:
                programs.append(row["program_solution"])
    if not programs:
        raise KeyError(TASK_ID)
    if len(set(programs)) != 1:
        raise ValueError("canonical variants disagree on program_solution")
    return programs[0]


def authority_paths() -> list[Path]:
    relatives = (
        "solutions/training/ae4f1146__9bd5d9c04dd8.json",
        "solutions/augmented/ae4f1146__ce5b727da6ba.json",
    )
    for base in (ROOT / "shared" / "data" / "base", ROOT / "data" / "base"):
        paths = [base / relative for relative in relatives]
        if all(path.is_file() for path in paths):
            return paths
    raise FileNotFoundError("task authority JSON files are absent from this snapshot")


def _valid_rectangular_grid(grid) -> bool:
    return (
        isinstance(grid, list)
        and bool(grid)
        and all(isinstance(row, list) and bool(row) for row in grid)
        and len({len(row) for row in grid}) == 1
        and all(type(value) is int and 0 <= value <= 9 for row in grid for value in row)
    )


def isolated_tiles(grid) -> list[tuple[int, int, list[list[int]]]]:
    """Enumerate candidates exactly as the selected Racket rule does.

    Isolation checks the four orthogonal border strips.  Diagonal corner
    contact is therefore lawful and intentionally not rejected here.
    """
    if not _valid_rectangular_grid(grid):
        raise ValueError("expected a nonempty rectangular ARC grid")
    h, w = len(grid), len(grid[0])
    found = []
    for r0 in range(h - 2):
        for c0 in range(w - 2):
            if not all(grid[r0 + dr][c0 + dc] != 0 for dr in range(3) for dc in range(3)):
                continue
            if r0 and any(grid[r0 - 1][c0 + dc] != 0 for dc in range(3)):
                continue
            if r0 + 3 < h and any(grid[r0 + 3][c0 + dc] != 0 for dc in range(3)):
                continue
            if c0 and any(grid[r0 + dr][c0 - 1] != 0 for dr in range(3)):
                continue
            if c0 + 3 < w and any(grid[r0 + dr][c0 + 3] != 0 for dr in range(3)):
                continue
            found.append((r0, c0, [row[c0:c0 + 3] for row in grid[r0:r0 + 3]]))
    return found


def oracle_output(grid) -> list[list[int]]:
    tiles = isolated_tiles(grid)
    if not tiles:
        raise ValueError("no isolated 3x3 candidate")
    # Strict '>' in the authority means the row-major first tile wins a tie.
    return max(tiles, key=lambda item: sum(value == 1 for row in item[2] for value in row))[2]


def most_non_eight_rival(grid) -> list[list[int]]:
    """Plausible canonical-fit shortcut: maximize cells whose color is not 8."""
    tiles = isolated_tiles(grid)
    if not tiles:
        raise ValueError("no isolated 3x3 candidate")
    return max(tiles, key=lambda item: sum(value != 8 for row in item[2] for value in row))[2]


def observed(grid) -> dict[str, int]:
    tiles = isolated_tiles(grid)
    fills = {value for row in grid for value in row if value not in (0, 1)}
    if len(fills) != 1:
        raise ValueError(f"expected one shared fill color, got {sorted(fills)}")
    return {
        "grid_h": len(grid),
        "grid_w": len(grid[0]),
        "tile_count": len(tiles),
        "fill_color": next(iter(fills)),
    }


def make_grid(
    specs: list[tuple[int, int, int]],
    *,
    h: int = 9,
    w: int = 9,
    fill: int = 2,
) -> list[list[int]]:
    """Build explicit row-major blue patterns for focused tests.

    Each spec is ``(top, left, blue_count)``.  The first ``blue_count`` cells
    in row-major order become color 1; the rest use ``fill``.
    """
    grid = [[0 for _ in range(w)] for _ in range(h)]
    for r0, c0, count in specs:
        if not 0 <= count <= 9:
            raise ValueError("blue_count must be in 0..9")
        cells = [(r0 + dr, c0 + dc) for dr in range(3) for dc in range(3)]
        if any(not (0 <= r < h and 0 <= c < w) or grid[r][c] != 0 for r, c in cells):
            raise ValueError("tile does not fit or overlaps")
        for index, (r, c) in enumerate(cells):
            grid[r][c] = 1 if index < count else fill
    return grid


def shortcut_witness_input() -> list[list[int]]:
    """Exact lawful disagreement: intended selects the second tile, rival first."""
    return make_grid([(0, 0, 1), (0, 4, 5)], fill=2)


def audit(module, count: int = 250) -> dict:
    """Run a deterministic independent sampler audit for future reviewers."""
    totals = Counter()
    per_band = {}
    all_hashes = set()
    for band in (None, "easy", "medium", "hard"):
        stats = Counter()
        shapes, colors, tile_counts, outputs = set(), set(), set(), set()
        for i in range(count):
            seed, sample_index = 1009 + i, i * 13 + 7
            grid = module.generate(seed, sample_index, difficulty=band)
            stats["draws"] += 1
            stats["self_check_failures"] += bool(module.self_check(grid))
            stats["nondeterministic"] += grid != module.generate(seed, sample_index, difficulty=band)
            stats["oracle_mismatches"] += module._intended_output(grid) != oracle_output(grid)
            stats["shortcut_witnesses"] += oracle_output(grid) != most_non_eight_rival(grid)
            obs = observed(grid)
            shapes.add((obs["grid_h"], obs["grid_w"]))
            colors.add(obs["fill_color"])
            tile_counts.add(obs["tile_count"])
            encoded = json.dumps(grid, separators=(",", ":"))
            digest = hashlib.sha256(encoded.encode()).hexdigest()
            all_hashes.add(digest)
            outputs.add(json.dumps(oracle_output(grid), separators=(",", ":")))
        stats["distinct_shapes"] = len(shapes)
        stats["distinct_fill_colors"] = len(colors)
        stats["distinct_tile_counts"] = len(tile_counts)
        stats["distinct_outputs"] = len(outputs)
        per_band[str(band)] = dict(stats)
        totals.update(stats)
    return {
        "schema": "9bd5d9c04dd8-independent-audit-v1",
        "version": module.VERSION,
        "canonical_pairs": len(canonical_pairs()),
        "canonical_matches": sum(oracle_output(pair["input"]) == pair["output"] for pair in canonical_pairs()),
        "canonical_self_check_failures": sum(bool(module.self_check(pair["input"])) for pair in canonical_pairs()),
        "per_band": per_band,
        "totals": dict(totals),
        "distinct_inputs": len(all_hashes),
        "witness": {
            "input": shortcut_witness_input(),
            "intended": oracle_output(shortcut_witness_input()),
            "most_non_eight_rival": most_non_eight_rival(shortcut_witness_input()),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--generator", type=Path)
    parser.add_argument("--count", type=int, default=250)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    module = load_generator(args.generator)
    report = audit(module, args.count)
    source = args.generator or ROOT / "generators" / TASK_ID / "generator.py"
    report["generator_sha256"] = hashlib.sha256(Path(source).read_bytes()).hexdigest()
    report["probe_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"totals": report["totals"], "distinct_inputs": report["distinct_inputs"]}, indent=2))
    failures = (
        report["canonical_matches"] != report["canonical_pairs"]
        or report["canonical_self_check_failures"]
        or report["totals"].get("self_check_failures")
        or report["totals"].get("nondeterministic")
        or report["totals"].get("oracle_mismatches")
    )
    return int(bool(failures))


if __name__ == "__main__":
    raise SystemExit(main())
