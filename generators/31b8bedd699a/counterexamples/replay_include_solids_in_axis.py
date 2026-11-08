"""Replay the exact six-pair historical v3 lesson against canonical Racket.

From WORK/ (the wrapper runs its payload from WORK/repo)::

    python run_with_racket.py python \
        generators/31b8bedd699a/counterexamples/replay_include_solids_in_axis.py \
        --out ../checks/main-counterexample/replay-01

The sibling JSON is the unchanged screening fixture. Its original Python label
basis is retained; only this public Catalog.apply replay establishes agreement
with authoritative labels. The historical generator is not imported or rerun.
No selected generator, tests, or rule are changed. --out must be a new directory.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import tempfile


def _bootstrap():
    for parent in Path(__file__).resolve().parents:
        for relative in ("shared/runtime", ""):
            support = parent / relative
            if (support / "reviewer_support.py").is_file():
                sys.path.insert(0, str(support))
                if (parent / "src/arcpuzzles").is_dir():
                    sys.path.insert(0, str(parent / "src"))
                return
    raise FileNotFoundError("No public reviewer_support in this file's own tree")


_bootstrap()
from reviewer_support import find_root, normalize_grid

TASK_ID = "31b8bedd699a"
FIXTURE_SHA256 = "6c87b3e06c0f120f5904393d4294f7fe63b76e4456d9dc915fd1328dac4c8ad3"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def components(grid):
    """Independent 4-connected monochrome component extraction."""
    h, w = len(grid), len(grid[0])
    seen, objects = set(), []
    for r in range(h):
        for c in range(w):
            color = grid[r][c]
            if not color or (r, c) in seen:
                continue
            pending, cells = [(r, c)], {(r, c)}
            seen.add((r, c))
            while pending:
                rr, cc = pending.pop()
                for y, x in ((rr - 1, cc), (rr + 1, cc), (rr, cc - 1), (rr, cc + 1)):
                    if (0 <= y < h and 0 <= x < w and grid[y][x] == color
                            and (y, x) not in seen):
                        seen.add((y, x)); cells.add((y, x)); pending.append((y, x))
            rows, cols = zip(*cells)
            top, left = min(rows), min(cols)
            area = (max(rows) - top + 1) * (max(cols) - left + 1)
            objects.append({"color": color, "top": top, "left": left,
                            "frame": len(cells) < area})
    return objects


def include_solids_in_axis(grid):
    """Wrong rule: retain frame tokens, but choose their axis using all objects."""
    objects = components(normalize_grid(grid))
    frames = [obj for obj in objects if obj["frame"]]
    rr = max(obj["top"] for obj in objects) - min(obj["top"] for obj in objects)
    cr = max(obj["left"] for obj in objects) - min(obj["left"] for obj in objects)
    vertical = rr > cr
    frames.sort(key=lambda obj: obj["top"] if vertical else obj["left"])
    colors = [obj["color"] for obj in frames]
    if vertical:
        return [[colors[r // 4] if r % 4 in (0, 3) or c in (0, 3) else 0
                 for c in range(4)] for r in range(4 * len(colors))]
    return [[colors[c // 4] if r in (0, 3) or c % 4 in (0, 3) else 0
             for c in range(4 * len(colors))] for r in range(4)]


def load_fixture():
    path = Path(__file__).with_name("include_solids_in_axis_lesson.json")
    if digest(path) != FIXTURE_SHA256:
        raise ValueError("The exact historical fixture hash changed")
    fixture = json.loads(path.read_text())
    if fixture["task_id"] != TASK_ID or len(fixture["pairs"]) != 6:
        raise ValueError("Expected the retained six-pair task fixture")
    return fixture, path


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="A new directory for the Racket receipt and verification.")
    parser.add_argument("--describe", action="store_true", help="Portable read-only fixture/rival preflight; does not execute or establish reference labels.")
    args = parser.parse_args(argv)
    fixture, fixture_path = load_fixture()
    pairs = fixture["pairs"]
    predictions = [include_solids_in_axis(pair["input"]) for pair in pairs]
    saved_rival_matches = [prediction == pair["rival_output"] for prediction, pair in zip(predictions, pairs)]
    if args.describe:
        print(json.dumps({"task_id": TASK_ID, "root": str(find_root(__file__)),
                          "fixture_sha256": digest(fixture_path), "pairs": len(pairs),
                          "saved_rival_outputs_reproduced": saved_rival_matches,
                          "reference_execution": False}, sort_keys=True))
        return 0 if all(saved_rival_matches) else 1
    if args.out is None:
        parser.error("--out is required for authoritative replay")
    out = args.out.resolve()
    if out.exists():
        parser.error(f"Refusing to reuse an existing output directory: {out}")
    out.mkdir(parents=True, exist_ok=False)
    from arcpuzzles import Catalog
    root = find_root(__file__)
    applied = Catalog(root).apply(TASK_ID, [pair["input"] for pair in pairs],
                                  reference="canonical", timeout=120)
    results = applied["results"]
    checks = []
    for position, (pair, result, rival) in enumerate(zip(pairs, results, predictions, strict=True)):
        valid = bool(result.get("valid_output") and result.get("output"))
        checks.append({
            "position": position, "sample_index": pair["sample_index"], "profile": pair["profile"],
            "role": "query" if position == fixture["query_position"] else "demonstration",
            "valid_reference_output": valid, "reference_error": result.get("error"),
            "saved_input_hash_matches": result["input_sha256"] == pair["input_sha256"],
            "saved_output_matches_racket": valid and pair["output"] == result["output"],
            "saved_rival_output_reproduced": rival == pair["rival_output"],
            "rival_matches_racket": valid and rival == result["output"],
            "input_sha256": result["input_sha256"], "output_sha256": result["output_sha256"],
            "racket_shape": [len(result["output"]), len(result["output"][0])] if valid else None,
            "rival_shape": [len(rival), len(rival[0])],
        })
    demos = fixture["demonstration_positions"]
    query = fixture["query_position"]
    verified = (len(checks) == 6 and applied["rule_hash_matches_catalog"]
                and all(check["valid_reference_output"] and check["saved_input_hash_matches"]
                        and check["saved_output_matches_racket"] and check["saved_rival_output_reproduced"]
                        for check in checks)
                and all(checks[position]["rival_matches_racket"] for position in demos)
                and not checks[query]["rival_matches_racket"])
    receipt = {
        "schema": "frame-historical-counterexample-replay-v1", "task_id": TASK_ID,
        "status": "PASS" if verified else "FAIL", "counterexample_verified": verified,
        "historical_generator_sha256": fixture["source_sha256"],
        "original_screening_fixture_sha256": FIXTURE_SHA256,
        "fixture_sha256": digest(fixture_path), "replay_sha256": digest(__file__),
        "original_label_basis": fixture["label_basis"],
        "verified_label_basis": "Public Catalog.apply, canonical Racket reference.",
        "rival": fixture["rival"], "rival_replay": "Independent implementation checked against every saved rival output.",
        "seed": fixture["seed"], "difficulty": fixture["difficulty"], "start": fixture["start"],
        "demonstration_positions": demos, "query_position": query,
        "valid_reference_outputs": sum(check["valid_reference_output"] for check in checks),
        "saved_output_matches": sum(check["saved_output_matches_racket"] for check in checks),
        "rival_demo_matches": [checks[position]["rival_matches_racket"] for position in demos],
        "rival_query_matches": checks[query]["rival_matches_racket"],
        "checks": checks,
        "authority_identity": {key: value for key, value in applied.items() if key != "results"},
        "scope": "Historical six-pair lesson replay only. The current generator is used by Catalog solely for authority resolution; it is not regenerated or assessed by this counterexample.",
    }
    # Keep a complete temporary copy until both destination files verify. This
    # also preserves authoritative output if a space-limited destination fails.
    backup = Path(tempfile.mkdtemp(prefix="frame-counterexample-evidence-"))
    values = (("racket.json", applied), ("receipt.json", receipt))
    for name, value in values:
        (backup / name).write_text(json.dumps(value, sort_keys=True, separators=(",", ":")) + "\n")
    try:
        for name, _ in values:
            path = out / name
            path.write_bytes((backup / name).read_bytes())
            path.chmod(0o644)
            if digest(path) != digest(backup / name):
                raise OSError(f"Output verification failed: {path}")
    except OSError:
        print(json.dumps({"preserved_complete_outputs": str(backup), "destination": str(out)}), file=sys.stderr)
        raise
    else:
        for name, _ in values:
            (backup / name).unlink()
        backup.rmdir()
    print(json.dumps({"status": receipt["status"], "out": str(out),
                      "valid_reference_outputs": receipt["valid_reference_outputs"],
                      "saved_output_matches": receipt["saved_output_matches"],
                      "rival_demo_matches": receipt["rival_demo_matches"],
                      "rival_query_matches": receipt["rival_query_matches"],
                      "executed_rule_hash": applied["executed_rule_hash"],
                      "fixture_sha256": receipt["fixture_sha256"],
                      "replay_sha256": receipt["replay_sha256"]}, sort_keys=True))
    return 0 if verified else 1


if __name__ == "__main__":
    raise SystemExit(main())
