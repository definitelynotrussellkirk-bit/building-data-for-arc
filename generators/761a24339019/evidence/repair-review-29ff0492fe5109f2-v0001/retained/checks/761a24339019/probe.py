"""Bounded default-lesson target-selection audit; no source or approval changes."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path.cwd().resolve()
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "shared/runtime"))
from arcpuzzles import Catalog
from arcpuzzles.parametric_worker import _real_evaluator
from arcpuzzles.runtime import validate_grid
from reviewer_support import load_selected_generator

TASK = "761a24339019"
PINNED = "e6e8c3271f289c286cb40c0a439beb4998edb0ce3645b73a7a1a9e6320a45b2d"
OUT = Path(__file__).resolve().parent / "witness.json"


def digest(value):
    return hashlib.sha256(value).hexdigest()


def predict(module, grid, selection):
    info = module._stamp_contract(grid)
    if info["errors"]:
        raise ValueError(info["errors"])
    targets = info["targets"]
    if selection == "rightward_targets":
        targets = [p for p in targets if p[1] >= info["anchor"][1]]
    elif selection == "first_target":
        targets = targets[:1]
    result = deepcopy(grid)
    for r, c in targets:
        for dr, dc in info["offsets"]:
            result[r + dr][c + dc] = 3
    return result


def main():
    if OUT.exists():
        raise FileExistsError("Use a fresh evidence directory for another audit")
    module, source, source_hash = load_selected_generator(TASK, root=ROOT)
    if source_hash != PINNED:
        raise ValueError("Assigned generator source drifted")
    catalog = Catalog(ROOT)
    record = catalog.get(TASK)
    programs = {v["program_solution"] for v in record["variants"]}
    if len(programs) != 1:
        raise ValueError("Expected one selected canonical program")
    canonical = next(iter(programs))
    rivals = {
        "rightward_targets": canonical.replace(
            "(not (equal? p anchor))", "(and (not (equal? p anchor)) (>= (second p) (second anchor)))"),
        "first_target": canonical.replace("(in-list targets)", "(in-list (list (first targets)))"),
    }
    if any(p == canonical for p in rivals.values()):
        raise ValueError("Canonical text no longer matches the explicit rival construction")
    screened, candidate = [], None
    # This source has no EXAMPLES_NEEDED declaration; native automatic floor is 3.
    for seed in range(16):
        grids = [module.generate(seed, i) for i in range(4)]
        labels = [predict(module, g, "all_targets") for g in grids]
        row = {"seed": seed, "sample_indices": [0, 1, 2, 3], "rivals": {}}
        for name in rivals:
            predictions = [predict(module, g, name) for g in grids]
            fits = predictions[:3] == labels[:3]
            differs = predictions[3] != labels[3]
            row["rivals"][name] = {"fits_all_three_demos": fits, "differs_on_query": differs}
            if fits and differs and candidate is None:
                candidate = (seed, name, grids)
        screened.append(row)
        if candidate:
            break
    seed, name, proposed_inputs = candidate if candidate else (0, "rightward_targets", None)
    # Materialize the actual native default episode; do not promote a manual grouping.
    episode = catalog.generate(TASK, count=1, seed=seed, timeout=90)[0]
    if len(episode["train"]) != 3 or len(episode["test"]) != 1:
        raise ValueError("Native default demonstration/query counts changed")
    pairs = episode["train"] + episode["test"]
    if proposed_inputs is not None and [p["input"] for p in pairs] != proposed_inputs:
        raise ValueError("Native sampling differs from the screened lesson; no defect claimed")
    apply, identity, bridge = _real_evaluator(ROOT / "shared/runtime")
    try:
        canonical_outputs = [validate_grid(apply(canonical, p["input"])) for p in pairs]
        rival_outputs = [validate_grid(apply(rivals[name], p["input"])) for p in pairs]
    finally:
        bridge.close()
    if canonical_outputs != [p["output"] for p in pairs]:
        raise ValueError("Independent protected replay differs from native labels")
    finding = candidate is not None and rival_outputs[:3] == canonical_outputs[:3] and rival_outputs[3] != canonical_outputs[3]
    if candidate and not finding:
        raise ValueError("Python prescreen did not reproduce under protected Racket")
    if digest(source.read_bytes()) != source_hash:
        raise ValueError("Generator changed during audit")
    report = {
        "task_id": TASK, "status": "finding" if finding else "bounded_no_finding",
        "generator_sha256": source_hash, "canonical_rule_hash": record["rule_hash"],
        "canonical_program_sha256": digest(canonical.encode()),
        "canonical_ledger_sha256": digest((ROOT / "shared/data/canonical/puzzles.jsonl").read_bytes()),
        "probe_sha256": digest(Path(__file__).read_bytes()), "seed_budget": 16,
        "screened": screened, "actual_default_counts": {"demonstrations": 3, "queries": 1},
        "rival_name": name, "canonical_program": canonical, "rival_program": rivals[name],
        "rival_program_sha256": digest(rivals[name].encode()), "racket": identity,
        "protected_program_evaluations": 8, "original_ambiguous_lesson": episode,
        "canonical_outputs": canonical_outputs, "rival_outputs": rival_outputs,
        "all_visible_demonstrations_agree": rival_outputs[:3] == canonical_outputs[:3],
        "query_differs": rival_outputs[3] != canonical_outputs[3],
        "proposal": "Select default demonstrations that reject plausible target selectors before a query distinguishes them; retain this original lesson separately for any optional alternative-answer research.",
        "limits": "At most 16 seeds and two finite target-selection rivals; native default canonical lesson only. Parametric family, other seeds, universal uniqueness, existing audit resolution and training admission are not assessed.",
        "source_changed": False, "owner_acceptance": "unchanged", "training_admitted": False,
    }
    OUT.write_text(json.dumps(report, sort_keys=True, separators=(",", ":")) + "\n")
    print(json.dumps({"status": report["status"], "seed": seed, "rival": name,
                      "seeds_screened": len(screened), "racket_evaluations": 8,
                      "evidence": "checks/761a24339019/witness.json"}, sort_keys=True))


if __name__ == "__main__":
    main()
