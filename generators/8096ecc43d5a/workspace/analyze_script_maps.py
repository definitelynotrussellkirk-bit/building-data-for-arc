#!/usr/bin/env python3
"""Enumerate constant command maps against recorded canonical authoring labels.

Run from any directory, in a repository or a copied runtime::

    python path/to/analyze_script_maps.py --include-pools --out analysis.json

This tool executes neither generate() nor Racket. It reads normalized public
canonical pairs through reviewer_support and records the selected source bytes.
The resulting finite map/rival evidence is not a proof of general lesson
identifiability, source approval, or training eligibility.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import itertools
import json
from pathlib import Path


TASK_ID = "8096ecc43d5a"
TRANSFORM_NAMES = (
    "identity", "rotate_cw", "rotate_180", "rotate_ccw", "flip_lr",
    "rotate_cw_after_flip_lr", "flip_ud", "rotate_ccw_after_flip_lr",
)
INTENDED_MAP = (1, 4, 2, 6)
ASYMMETRIC_CROP = [[8, 0, 0], [8, 8, 8]]
SCRIPT_RIVALS = {
    "sorted_codes": lambda codes: tuple(sorted(codes)),
    "deduplicate_codes": lambda codes: tuple(dict.fromkeys(codes)),
    "first_code_only": lambda codes: tuple(codes[:1]),
    "last_code_only": lambda codes: tuple(codes[-1:]),
    "reverse_codes": lambda codes: tuple(reversed(codes)),
    "ignore_codes": lambda codes: (),
    "first_three_only": lambda codes: tuple(codes[:3]),
    "collapse_adjacent_codes": lambda codes: tuple(key for key, _ in itertools.groupby(codes)),
}


def _load_support():
    """Find the public helper in this tool's own tree; never infer from cwd."""
    tool_path = Path(__file__).resolve()
    for ancestor in tool_path.parents:
        for relative in ("reviewer_support.py", "shared/runtime/reviewer_support.py"):
            source = ancestor / relative
            if not source.is_file():
                continue
            spec = importlib.util.spec_from_file_location("_script_map_reviewer_support", source)
            if spec is None or spec.loader is None:
                raise ImportError(f"Cannot load public reviewer support from {source}")
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            return module
    raise FileNotFoundError("No reviewer_support.py in this tool's library/runtime ancestors")


def _json_hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def read_context(root=None):
    """Return normalized labeled pairs and current, explicit source identities."""
    support = _load_support()
    root = support.find_root(__file__) if root is None else Path(root).resolve()
    pairs = support.canonical_pairs(TASK_ID, root=root, labeled_only=True)
    ledger = support.canonical_path(root)
    canonical_rows = []
    rule_sources = set()
    with ledger.open(encoding="utf-8") as handle:
        for row_index, line in enumerate(handle):
            if not line.strip():
                continue
            row = json.loads(line)
            if row.get("task_id") != TASK_ID:
                continue
            canonical_rows.append({
                "canonical_row": row_index,
                "source": row.get("source"),
                "row_sha256": hashlib.sha256(line.encode()).hexdigest(),
            })
            if row.get("program_solution"):
                rule_sources.add(str(row["program_solution"]))
    if len(rule_sources) != 1:
        raise ValueError("Expected one unambiguous canonical Racket source")
    rule_source = next(iter(rule_sources))
    selected, generator_path, generator_hash = support.load_selected_generator(TASK_ID, root=root)
    identity = {
        "canonical_path": ledger.relative_to(root).as_posix(),
        "canonical_sha256": hashlib.sha256(ledger.read_bytes()).hexdigest(),
        "canonical_rows": canonical_rows,
        "canonical_pairs_sha256": _json_hash(pairs),
        "canonical_rule_source_sha256": hashlib.sha256(rule_source.encode()).hexdigest(),
        "canonical_rule_hash": hashlib.sha256(" ".join(rule_source.split()).encode()).hexdigest()[:12],
        "generator_path": generator_path.relative_to(root).as_posix(),
        "generator_sha256": generator_hash,
        "generator_version": getattr(selected, "VERSION", None),
        "generator_declared_rule_hash": getattr(selected, "RULE_HASH", None),
        "analysis_tool_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    return {"pairs": pairs, "identity": identity}


def transform(grid, index):
    """D4 index: rotate clockwise index%4 times, after LR if index >= 4."""
    result = [row[:] for row in grid]
    if index >= 4:
        result = [row[::-1] for row in result]
    for _ in range(index % 4):
        result = [list(row) for row in zip(*result[::-1])]
    return result


def crop_below_top(grid):
    cells = [(r, c) for r in range(1, len(grid)) for c, value in enumerate(grid[r]) if value]
    if not cells:
        raise ValueError("The canonical crop requires a nonzero cell below row zero")
    top, bottom = min(r for r, _ in cells), max(r for r, _ in cells)
    left, right = min(c for _, c in cells), max(c for _, c in cells)
    return [row[left:right + 1] for row in grid[top:bottom + 1]]


def execute_script(codes, mapping=INTENDED_MAP, crop=ASYMMETRIC_CROP):
    result = [row[:] for row in crop]
    for code in codes:
        if 1 <= code <= 4:
            result = transform(result, mapping[code - 1])
    return result


def solve_mapping(grid, mapping=INTENDED_MAP):
    """Pure Python map candidate; output is not a reference-runtime label."""
    codes = tuple(value for value in grid[0] if value != 0)
    return execute_script(codes, mapping, crop_below_top(grid))


def enumerate_fitting_maps(pairs):
    """Enumerate all 8**4 maps against every supplied normalized labeled pair."""
    if not pairs:
        raise ValueError("At least one labeled pair is required")
    prepared = []
    for pair in pairs:
        if not pair.get("output"):
            raise ValueError("Every labeled pair must have a nonempty output")
        grid = pair["input"]
        prepared.append((tuple(value for value in grid[0] if value), crop_below_top(grid), pair["output"]))
    fitting = []
    for mapping in itertools.product(range(8), repeat=4):
        if all(execute_script(codes, mapping, crop) == output for codes, crop, output in prepared):
            fitting.append(mapping)
    return fitting


def derive_rich_pools(fitting_maps, *, min_length=4, max_length=6):
    """Enumerate scripts refuting eight shortcuts, grouped by map-killing mask.

    The reference L crop has eight distinct D4 variants. Therefore unequal
    variants here remain unequal on any crop with eight distinct variants.
    A leading blank code cell additionally refutes stop_at_first_zero: every
    retained script already refutes ignore_codes and hence is nonidentity.
    """
    if not (type(min_length) is int and type(max_length) is int and 1 <= min_length <= max_length <= 6):
        raise ValueError("Script length bounds must be integers in 1..6")
    maps = [tuple(mapping) for mapping in fitting_maps]
    if INTENDED_MAP not in maps:
        raise ValueError("The intended map must fit the supplied labeled population")
    alternatives = [mapping for mapping in maps if mapping != INTENDED_MAP]
    if not alternatives:
        raise ValueError("At least one fitting alternative map is needed for killing masks")
    variants = [transform(ASYMMETRIC_CROP, index) for index in range(8)]
    pools = {}
    for length in range(min_length, max_length + 1):
        for codes in itertools.product(range(1, 5), repeat=length):
            output = execute_script(codes)
            if any(execute_script(rewrite(codes)) == output for rewrite in SCRIPT_RIVALS.values()):
                continue
            mask = "".join("1" if execute_script(codes, mapping) != output else "0" for mapping in alternatives)
            if "1" not in mask:
                continue
            pools.setdefault(mask, []).append({
                "codes": list(codes),
                "net_transform": TRANSFORM_NAMES[variants.index(output)],
            })
    return {
        "length_range": [min_length, max_length],
        "reference_crop": ASYMMETRIC_CROP,
        "mask_map_order": [list(mapping) for mapping in alternatives],
        "required_rival_refutations": list(SCRIPT_RIVALS),
        "leading_zero_additionally_refutes": "stop_at_first_zero",
        "pools": dict(sorted(pools.items())),
    }


def analyze(*, root=None, include_pools=False):
    context = read_context(root)
    fitting = enumerate_fitting_maps(context["pairs"])
    report = {
        "schema": "arcpuzzles-script-map-analysis-v1",
        "task_id": TASK_ID,
        "evidence_basis": "Recorded normalized canonical train and test labels; finite Python candidate enumeration",
        "reference_execution_performed": False,
        "source_identity": context["identity"],
        "canonical_labeled_pairs": len(context["pairs"]),
        "pair_identities": [
            {key: pair[key] for key in ("variant", "split", "pair_index")}
            for pair in context["pairs"]
        ],
        "candidate_maps_examined": 8 ** 4,
        "transform_index_names": list(TRANSFORM_NAMES),
        "intended_map": list(INTENDED_MAP),
        "intended_map_fits": INTENDED_MAP in fitting,
        "fitting_map_count": len(fitting),
        "fitting_maps": [
            {"indices": list(mapping), "commands": [TRANSFORM_NAMES[index] for index in mapping]}
            for mapping in fitting
        ],
        "limits": [
            "These are constant D4 command maps, not all possible solvers.",
            "Canonical fit does not prove that fresh generated demonstrations determine a query.",
            "No generator draws, Racket labels, audits, approvals, or training admission are performed.",
        ],
    }
    if include_pools:
        report["rich_scripts"] = derive_rich_pools(fitting)
    return report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, help="Explicit library/runtime root; otherwise bind to this tool's tree")
    parser.add_argument("--include-pools", action="store_true", help="Also enumerate rich scripts of length 4..6")
    parser.add_argument("--out", type=Path, help="Save JSON here; omit to print the full report")
    args = parser.parse_args(argv)
    report = analyze(root=args.root, include_pools=args.include_pools)
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out is None:
        print(encoded, end="")
    else:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(encoded, encoding="utf-8")
        print(json.dumps({"out": str(args.out), "canonical_pairs": report["canonical_labeled_pairs"],
                          "fitting_maps": report["fitting_map_count"]}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
