#!/usr/bin/env python3
"""Reproduce the two random audit findings with staged task sources and Racket."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile

PACKET = Path(__file__).resolve().parents[1]
REPO = PACKET / "repo"
sys.path.insert(0, str(REPO / "src"))

from arcpuzzles.catalog import Catalog  # noqa: E402
from arcpuzzles.runtime import prepare_runtime, run_process  # noqa: E402

TARGETS = ("ac3c9342fc5c", "97b3f59b5cc4")

CHILD = r'''
from __future__ import annotations
from copy import deepcopy
import hashlib
import importlib
import json
from pathlib import Path

from puzzle_generators import runner
from scripts.canonical_profile_gate import canonical_pairs
from scripts.coder_synth_verify import _grids_equal


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def normalized_rule_hash(source):
    return hashlib.sha256(" ".join(source.split()).encode()).hexdigest()[:12]


def top_only_difference(grid):
    width = len(grid[0])
    return [
        [3 if grid[r][c] != 0 and grid[r + 7][c] == 0 else 0
         for c in range(width)]
        for r in range(6)
    ]


def occupancy_counts(grid):
    counts = {"00": 0, "10": 0, "01": 0, "11": 0}
    for r in range(6):
        for c in range(len(grid[0])):
            counts[f"{int(grid[r][c] != 0)}{int(grid[r+7][c] != 0)}"] += 1
    return counts


def color_presence_shortcut(grid):
    h, w = len(grid), len(grid[0])
    border_colors = {
        grid[r][c]
        for r in range(h)
        for c in range(w)
        if (r in (0, h - 1) or c in (0, w - 1)) and grid[r][c] != 0
    }
    return [
        [value if value in border_colors else 0 for value in row]
        for row in grid
    ]


def run_ac3():
    task = "ac3c9342fc5c"
    gen = importlib.import_module(f"puzzle_generators.per_puzzle.{task}.generator")
    bundle = runner._load_bundle(task)
    bridge, fn = runner._open_bridge_with_rule(bundle.rule_callable_text)
    try:
        lesson = runner.run_one(
            task,
            seed=17,
            sample_index=0,
            n_train=3,
            n_test=1,
            bundle=bundle,
            bridge=bridge,
            fn_name=fn,
            difficulty="medium",
            panel_pattern="stripes",
        )
    finally:
        bridge.shutdown()
    pairs = lesson["train"] + lesson["test"]
    pair_rows = []
    for index, pair in enumerate(pairs):
        rival = top_only_difference(deepcopy(pair["input"]))
        pair_rows.append({
            "index": index,
            "split": "train" if index < 3 else "test",
            "input": pair["input"],
            "actual_racket_output": pair["output"],
            "rival_output": rival,
            "rival_matches": _grids_equal(rival, pair["output"]),
            "self_check": gen.self_check(pair["input"]),
            "occupancy_counts": occupancy_counts(pair["input"]),
        })
    return {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": task,
        "finding": "declared stripes mode makes bottom-only occupancy impossible; a top-only-difference rival fits the entire 3-demo lesson and query",
        "generator_sha256": sha(gen.__file__),
        "generator_version": gen.VERSION,
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "selected_rule_hash": normalized_rule_hash(bundle.rule_source),
        "rule_source": bundle.rule_file,
        "replay": {
            "seed": 17,
            "sample_index": 0,
            "difficulty": "medium",
            "n_train": 3,
            "n_test": 1,
            "overrides": {"panel_pattern": "stripes"},
        },
        "documented_domain": True,
        "validator_passes_all": all(not row["self_check"] for row in pair_rows),
        "rival_fits_all_demos": all(row["rival_matches"] for row in pair_rows[:3]),
        "rival_matches_query": pair_rows[3]["rival_matches"],
        "pairs": pair_rows,
        "limitations": "This proves ambiguity for the declared stripes subdomain, not the default mixed-pattern lesson distribution as a whole.",
    }


def run_97():
    task = "97b3f59b5cc4"
    gen = importlib.import_module(f"puzzle_generators.per_puzzle.{task}.generator")
    bundle = runner._load_bundle(task)
    canonical = canonical_pairs(task)
    canonical_rows = []
    for index, pair in enumerate(canonical):
        rival = color_presence_shortcut(deepcopy(pair["input"]))
        canonical_rows.append({
            "index": index,
            "input": pair["input"],
            "actual_canonical_output": pair["output"],
            "rival_output": rival,
            "rival_matches": _grids_equal(rival, pair["output"]),
            "self_check": gen.self_check(pair["input"]),
        })

    custom = [[0 for _ in range(9)] for _ in range(7)]
    # Border component of color 6.
    custom[0][0] = custom[1][0] = 6
    # Disconnected interior component of the SAME color 6.
    custom[3][3] = custom[3][4] = 6
    # Second border component and second interior component preserve the other
    # advertised count constraints, isolating repeated color as the rejection.
    custom[6][8] = custom[5][8] = 2
    custom[2][6] = custom[2][7] = 3

    bridge, fn = runner._open_bridge_with_rule(bundle.rule_callable_text)
    try:
        actual = runner._apply_rule(bridge, fn, custom)
    finally:
        bridge.shutdown()
    rival = color_presence_shortcut(deepcopy(custom))
    return {
        "schema": "arcpuzzles-audit-counterexample-v1",
        "task_id": task,
        "finding": "distinct-component-color invariant rejects a shipped canonical example and makes a global color-presence shortcut indistinguishable on generated data",
        "generator_sha256": sha(gen.__file__),
        "generator_version": gen.VERSION,
        "declared_rule_hash": getattr(gen, "RULE_HASH", None),
        "selected_rule_hash": normalized_rule_hash(bundle.rule_source),
        "rule_source": bundle.rule_file,
        "canonical_pairs": canonical_rows,
        "canonical_pairs_rejected_by_self_check": [
            row["index"] for row in canonical_rows if row["self_check"]
        ],
        "color_presence_shortcut_fits_all_canonical": all(
            row["rival_matches"] for row in canonical_rows
        ),
        "counterexample": {
            "input": custom,
            "actual_racket_output": actual,
            "rival_output": rival,
            "outputs_differ": not _grids_equal(actual, rival),
            "self_check": gen.self_check(custom),
            "passes_target_validator": not gen.self_check(custom),
            "belongs_documented_generator_domain": False,
            "domain_note": "It preserves >=2 border and >=2 interior components but repeats color 6 across disconnected components, the exact restriction under review.",
        },
        "limitations": "The custom discriminator is outside the current distinct-color generator domain; the stronger defect is that the same restriction also rejects canonical pair index 1.",
    }


ac3 = run_ac3()
n97 = run_97()
Path("audit-ac3c9342fc5c.json").write_text(json.dumps(ac3, indent=2) + "\n")
Path("audit-97b3f59b5cc4.json").write_text(json.dumps(n97, indent=2) + "\n")
print(json.dumps({
    "ac3": {
        "rival_fits_all_demos": ac3["rival_fits_all_demos"],
        "rival_matches_query": ac3["rival_matches_query"],
        "validator_passes_all": ac3["validator_passes_all"],
    },
    "97": {
        "canonical_rejections": n97["canonical_pairs_rejected_by_self_check"],
        "shortcut_fits_all_canonical": n97["color_presence_shortcut_fits_all_canonical"],
        "counterexample_differs": n97["counterexample"]["outputs_differ"],
        "counterexample_self_check": n97["counterexample"]["self_check"],
    },
}, indent=2))
'''


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="arc-audit-repro-") as directory:
        stage = Path(directory)
        manifest = prepare_runtime(Catalog(REPO), stage, task_ids=list(TARGETS))
        (stage / "audit_child.py").write_text(CHILD)
        result = run_process([sys.executable, "-B", "audit_child.py"], stage, timeout=600)
        if result["exit_code"] != 0 or result["timed_out"]:
            print(result["stdout"])
            print(result["stderr"], file=sys.stderr)
            return 1
        for name in ("audit-ac3c9342fc5c.json", "audit-97b3f59b5cc4.json"):
            payload = json.loads((stage / name).read_text())
            payload["reproducer_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
            payload["runtime_manifest_sha256"] = hashlib.sha256(
                (stage / "RUNTIME_MANIFEST.json").read_bytes()
            ).hexdigest()
            payload["runtime_file_count"] = len(manifest["files"])
            (PACKET / "checks" / name).write_text(json.dumps(payload, indent=2) + "\n")
        print(result["stdout"], end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
