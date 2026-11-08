"""Bounded peer learnability check; labels for retained findings use protected Racket."""
from pathlib import Path
from copy import deepcopy
import hashlib
import json
import sys
import time

WORK = Path(__file__).resolve().parents[2]
ROOT = WORK / "repo"
OUT = Path(__file__).resolve().parent
RUNTIME = ROOT / "shared/runtime"
sys.path.insert(0, str(RUNTIME))
from reviewer_support import load_selected_generator
from arcpuzzles.parametric_worker import _local_imports, _real_evaluator, _grid


def pin(tree, target):
    if isinstance(tree, dict):
        if target in tree:
            return tree[target]
        for value in tree.values():
            found = pin(value, target)
            if found is not None:
                return found
    elif isinstance(tree, list):
        for value in tree:
            found = pin(value, target)
            if found is not None:
                return found
    return None


def tolerant(grid, threshold):
    p9 = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 9)
    p6 = next((r, c) for r, row in enumerate(grid) for c, v in enumerate(row) if v == 6)
    delta = [b-a for a, b in zip(p9, p6)]
    step = [0 if abs(d) <= threshold else (1 if d > 0 else -1) for d in delta]
    out = deepcopy(grid)
    out[p9[0]][p9[1]] = 5
    out[p9[0]+step[0]][p9[1]+step[1]] = 9
    out[p6[0]][p6[1]] = 9
    return out


def main():
    started = time.monotonic()
    module, source, source_hash = load_selected_generator("a85f5274d2ae", root=ROOT)
    manifest = json.loads((WORK / "PACKET-MANIFEST.json").read_text())
    pinned = pin(manifest, "repo/generators/a85f5274d2ae/generator.py")
    assert pinned == source_hash, (pinned, source_hash)
    canonical = next(json.loads(row) for row in (ROOT / "shared/data/canonical/puzzles.jsonl").read_text().splitlines()
                     if json.loads(row).get("task_id") == "a85f5274d2ae")
    program = canonical["program_solution"]
    rule_hash = hashlib.sha256(program.encode()).hexdigest()
    assert hashlib.sha256(" ".join(program.split()).encode()).hexdigest()[:12] == module.RULE_HASH
    counts = {"lessons": 0, "declared_panel_ambiguities": 0, "axis_tolerance_0": 0, "axis_tolerance_2": 0}
    first = {}
    for seed in range(12):
        for band in ("easy", "medium", "hard"):
            pairs = []
            for index in range(7):
                grid = module.generate(seed, index, difficulty=band)
                pairs.append({"input": grid, "output": module.rule_mirror(grid)})
            for start in range(4):
                demos, query = pairs[start:start+3], pairs[start+3]
                counts["lessons"] += 1
                rival = module.SEMANTIC_RIVALS["panel_direction_only"]
                if all(rival(p["input"]) == p["output"] for p in demos) and rival(query["input"]) != query["output"]:
                    counts["declared_panel_ambiguities"] += 1
                for threshold in (0, 2):
                    name = f"axis_tolerance_{threshold}"
                    if (all(tolerant(p["input"], threshold) == p["output"] for p in demos)
                            and tolerant(query["input"], threshold) != query["output"]):
                        counts[name] += 1
                        first.setdefault(name, {"seed": seed, "difficulty": band, "start": start,
                            "threshold": threshold, "train": demos, "test": [query],
                            "existing_lesson_check": module.lesson_identifiable(demos, query)})
    receipts = []
    with _local_imports(RUNTIME, RUNTIME):
        apply, identity, bridge = _real_evaluator(RUNTIME)
        try:
            for name, lesson in first.items():
                threshold = lesson["threshold"]
                alternate = program.replace("(abs dr) 1", f"(abs dr) {threshold}").replace("(abs dc) 1", f"(abs dc) {threshold}")
                assert alternate != program
                pairs = lesson["train"] + lesson["test"]
                actual = [_grid(apply(program, p["input"])) for p in pairs]
                wrong = [_grid(apply(alternate, p["input"])) for p in pairs]
                assert actual == [p["output"] for p in pairs]
                assert actual[:3] == wrong[:3] and actual[3] != wrong[3]
                assert all(not module.self_check(p["input"]) for p in pairs)
                witness = {"schema": "bounded-peer-lesson-counterexample-v1", "task_id": module.TASK_ID,
                    "source_sha256": source_hash, "canonical_program_sha256": rule_hash,
                    "rival": name, "program": program, "counterfactual_program": alternate,
                    "racket": identity, **lesson,
                    "counterfactual_train_outputs": wrong[:3], "counterfactual_query_output": wrong[3],
                    "query_delta_cells": [[r,c,actual[3][r][c],wrong[3][r][c]]
                        for r in range(len(actual[3])) for c in range(len(actual[3][0]))
                        if actual[3][r][c] != wrong[3][r][c]],
                    "all_labels_protected_racket": True}
                path = OUT / (name + "-witness.json")
                path.write_text(json.dumps(witness, indent=2) + "\n")
                receipts.append({"rival": name, "seed": lesson["seed"], "difficulty": lesson["difficulty"],
                    "start": lesson["start"], "racket_evaluations": 8, "witness": str(path.relative_to(WORK)),
                    "existing_lesson_check": lesson["existing_lesson_check"]})
            if not first:
                checked = []
                for p in canonical["train"] + canonical["test"]:
                    assert _grid(apply(program, p["input"])) == p["output"]
                    checked.append(True)
                receipts.append({"canonical_pairs_replayed": len(checked)})
        finally:
            bridge.close()
    assert hashlib.sha256(source.read_bytes()).hexdigest() == source_hash
    report = {"schema": "bounded-peer-review-v1", "task_id": module.TASK_ID,
        "outcome": "unchanged", "finding": "demonstration_ambiguity" if receipts and first else "bounded_no_finding",
        "source_sha256": source_hash, "packet_manifest_sha256": pinned,
        "canonical_program_sha256": rule_hash, "rule_hash": module.RULE_HASH,
        "search": {"seeds": list(range(12)), "bands": ["easy","medium","hard"],
                   "starts": list(range(4)), "demos": 3, "queries": 1, **counts},
        "racket": identity, "retained": receipts,
        "elapsed_seconds": round(time.monotonic()-started,3),
        "command": "WORK/.venv/bin/python review.py run python3 ../checks/a85f5274d2ae/probe.py",
        "prior_probe_attempt": "Exit1 before search: probe initially compared raw text hash to catalog normalized-rule hash; corrected only the probe after reading catalog.py hash convention.",
        "limits": ["Only three plausible rivals and144 consecutive lessons were searched.",
                   "Search counts use Python candidate screening; only retained findings are protected-Racket verified.",
                   "No generator, canonical rule, parametric prototype, fixture, or shared runtime was edited.",
                   "Existing frozen-fixture blocker was not rerun or cleared; no approval or admission claim."]}
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report))


if __name__ == "__main__":
    main()
